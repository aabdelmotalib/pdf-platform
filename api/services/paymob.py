"""
Paymob payment service for PDF Platform.

Handles authentication, order creation, payment key generation, and HMAC verification.
"""

import hmac
import hashlib
import logging
import httpx
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from db.models import Payment, Plan

logger = logging.getLogger(__name__)

class PaymobService:
    BASE_URL = "https://accept.paymob.com/api"

    async def get_auth_token(self) -> str:
        """Step 1: Get Paymob auth token"""
        url = f"{self.BASE_URL}/auth/tokens"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"api_key": settings.PAYMOB_API_KEY})
            if response.status_code != 201:
                logger.error(f"Paymob Auth Token Error: {response.status_code} - {response.text}")
            response.raise_for_status()
            data = response.json()
            return data["token"]

    async def create_order(self, auth_token: str, amount_cents: int, currency: str = "EGP") -> dict:
        """Step 2: Create Paymob order"""
        url = f"{self.BASE_URL}/ecommerce/orders"
        payload = {
            "auth_token": auth_token,
            "delivery_needed": False,
            "amount_cents": amount_cents,
            "currency": currency,
            "items": []
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_payment_key(
        self, 
        auth_token: str, 
        order_id: int, 
        amount_cents: int,
        integration_id: int, 
        billing_data: dict,
        currency: str = "EGP"
    ) -> str:
        """Step 3: Get payment token (payment key)"""
        url = f"{self.BASE_URL}/acceptance/payment_keys"
        payload = {
            "auth_token": auth_token,
            "amount_cents": amount_cents,
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": billing_data,
            "currency": currency,
            "integration_id": integration_id
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["token"]

    def get_integration_id(self, method: str) -> int:
        """Map payment method to integration ID"""
        mapping = {
            "card": settings.PAYMOB_INTEGRATION_ID_CARD,
            "wallet": settings.PAYMOB_INTEGRATION_ID_WALLET,
            "instapay": settings.PAYMOB_INTEGRATION_ID_INSTAPAY,
            "fawry": settings.PAYMOB_INTEGRATION_ID_FAWRY,
        }
        return int(mapping.get(method, settings.PAYMOB_INTEGRATION_ID_CARD))

    def verify_hmac(self, payload: dict, received_hmac: str) -> bool:
        """Verify Paymob webhook HMAC signature"""
        # Paymob concatenates these fields in this exact order:
        fields = [
            "amount_cents", "created_at", "currency", "error_occured",
            "has_parent_transaction", "id", "integration_id", "is_3d_secure",
            "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
            "is_voided", "order", "owner", "pending",
            "source_data.pan", "source_data.sub_type", "source_data.type",
            "success"
        ]
        
        obj = payload.get("obj", {})
        concat = ""
        for field in fields:
            if "." in field:
                parts = field.split(".")
                val = obj.get(parts[0], {}).get(parts[1], "")
                # Convert bool to lowercase string 'true'/'false' as Paymob does
                if isinstance(val, bool):
                    concat += str(val).lower()
                else:
                    concat += str(val if val is not None else "")
            else:
                val = obj.get(field, "")
                if isinstance(val, bool):
                    concat += str(val).lower()
                else:
                    concat += str(val if val is not None else "")
        
        expected = hmac.new(
            settings.PAYMOB_HMAC_SECRET.encode(),
            concat.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected, received_hmac)

    async def initiate_payment(
        self, 
        db: AsyncSession,
        user_id: UUID, 
        plan_id: int, 
        method: str,
        user_email: str, 
        user_phone: str
    ) -> dict:
        """Full flow: Steps 1+2+3, returns payment_url and payment_key"""
        # 1. Get auth token
        auth_token = await self.get_auth_token()
        
        # 2. Get plan from DB to get price
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalars().first()
        if not plan:
            raise ValueError(f"Plan with id {plan_id} not found")
            
        amount_cents = int(plan.price_egp * 100)
        
        # 3. Create order
        order = await self.create_order(auth_token, amount_cents)
        order_id = order["id"]
        
        # 4. Get payment key
        integration_id = self.get_integration_id(method)
        billing_data = {
            "first_name": "User", # Generic as we don't have split name
            "last_name": str(user_id),
            "email": user_email,
            "phone_number": user_phone or "01000000000",
            "apartment": "NA",
            "floor": "NA",
            "street": "NA",
            "building": "NA",
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "NA",
            "country": "EG",
            "state": "NA"
        }
        
        payment_key = await self.get_payment_key(
            auth_token, 
            order_id, 
            amount_cents, 
            integration_id, 
            billing_data
        )
        
        # 5. Build payment URL
        # Iframe URL: https://accept.paymob.com/api/acceptance/iframes/{IFRAME_ID}?payment_token={key}
        payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_key}"
        
        # 6. Create payment row in DB
        db_payment = Payment(
            user_id=user_id,
            amount_egp=plan.price_egp,
            status="pending",
            gateway_ref=str(order_id),
            payment_method=method,
            description=f"Subscription to {plan.name} plan"
        )
        db.add(db_payment)
        await db.commit()
        await db.refresh(db_payment)
        
        # 7. Return details
        return {
            "payment_url": payment_url,
            "payment_key": payment_key,
            "payment_id": db_payment.id,
            "order_id": order_id
        }

# Singleton instance
paymob_service = PaymobService()
