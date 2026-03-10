"""
Payments router — Paymob integration.

POST /payments/initiate  → initiate a payment with Paymob
POST /payments/webhook   → handle Paymob webhooks (idempotent, verified)
GET  /payments/history   → user payment history
GET  /payments/{id}/status → single payment status
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import User, Payment, Subscription, Plan
from dependencies import get_current_user
from schemas import (
    PaymentInitiateRequest, 
    PaymentResponse, 
    PaymentHistoryResponse, 
    PaymentStatusResponse,
    PaymentHistoryItem
)
from services.paymob import paymob_service
from services.session_timer import start_session_timer
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    req: PaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiate a payment with Paymob."""
    try:
        # Pass phone from user if available, else default
        user_phone = current_user.phone_number or "01000000000"
        
        result = await paymob_service.initiate_payment(
            db=db,
            user_id=current_user.id,
            plan_id=req.plan_id,
            method=req.method,
            user_email=current_user.email,
            user_phone=user_phone
        )
        return PaymentResponse(**result)
    except Exception as e:
        logger.error(f"Failed to initiate payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initiation failed: {str(e)}"
        )


@router.post("/webhook")
async def paymob_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Paymob transaction webhook.
    NO AUTH — verified via HMAC.
    """
    received_hmac = request.query_params.get("hmac")
    if not received_hmac:
        logger.warning("Webhook received without HMAC param")
        return {"status": "error", "message": "Missing HMAC"}

    payload = await request.json()
    
    # 1. Verify HMAC
    if not paymob_service.verify_hmac(payload, received_hmac):
        logger.error("Paymob Webhook HMAC verification failed")
        # Return 200 to avoid retries/attacks insight
        return {"status": "unauthorized"}

    # 2. Check success
    # payload["obj"]["success"] is typically true/false
    obj = payload.get("obj", {})
    success = obj.get("success")
    
    if not success:
        logger.info(f"Received unsuccessful payment webhook for order {obj.get('order', {}).get('id')}")
        return {"status": "ok"}

    # 3. Handle successful payment
    gateway_ref = str(obj.get("order", {}).get("id"))
    
    # Idempotency check
    result = await db.execute(select(Payment).where(Payment.gateway_ref == gateway_ref))
    payment = result.scalars().first()
    
    if not payment:
        logger.error(f"Payment record not found for gateway_ref: {gateway_ref}")
        return {"status": "not_found"}

    if payment.status == "completed":
        return {"status": "already_processed"}

    # Update payment status
    payment.status = "completed"
    payment.updated_at = datetime.now(timezone.utc)
    
    # 4. Activate Subscription
    # Get the plan to know frequency (hourly vs monthly)
    plan_result = await db.execute(select(Plan).where(Plan.id == payment.plan_id))
    plan = plan_result.scalars().first()
    
    now = datetime.now(timezone.utc)
    expires_at = now
    if plan.name == "hourly":
        expires_at = now + timedelta(hours=1)
    elif plan.name == "monthly":
        expires_at = now + timedelta(days=30)
    else:
        # Default fallback
        expires_at = now + timedelta(days=30)

    # Check for existing active subscription
    sub_result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == payment.user_id,
                Subscription.is_active == True
            )
        )
    )
    subscription = sub_result.scalars().first()
    
    if subscription:
        subscription.plan_id = plan.id
        subscription.expires_at = expires_at
        subscription.updated_at = now
    else:
        new_sub = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            is_active=True,
            expires_at=expires_at,
            created_at=now,
            updated_at=now
        )
        db.add(new_sub)

    # 5. Start session timer for hourly plans
    if plan.name == "hourly":
        start_session_timer(str(payment.user_id), 3600)
        logger.info(f"Started hourly session timer for user {payment.user_id}")

    await db.commit()
    logger.info(f"Payment successful: gateway_ref={gateway_ref}, user_id={payment.user_id}, plan={plan.name}")
    
    return {"status": "ok"}


@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Return user's payment history."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    
    return PaymentHistoryResponse(
        payments=[
            PaymentHistoryItem(
                id=p.id,
                amount_egp=float(p.amount_egp),
                status=p.status,
                payment_method=p.payment_method,
                created_at=p.created_at
            ) for p in payments
        ]
    )


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Return status of a single payment."""
    try:
        p_uuid = UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

    result = await db.execute(
        select(Payment).where(
            and_(
                Payment.id == p_uuid,
                Payment.user_id == current_user.id
            )
        )
    )
    payment = result.scalars().first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    return PaymentStatusResponse(
        id=payment.id,
        status=payment.status,
        amount_egp=float(payment.amount_egp)
    )
