"""
Session timer router — hourly plan session status.

GET /session/status  → timer status for the current user's plan
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import Subscription, get_db
from db.models import User
from dependencies import get_current_user
from schemas import SessionStatusResponse
from services.session_timer import get_session_files_used, get_session_remaining

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


# ---------------------------------------------------------------------------
# GET /session/status
# ---------------------------------------------------------------------------
@router.get("/status", response_model=SessionStatusResponse)
async def session_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the current user's session/plan status.

    - No active subscription → inactive
    - Monthly plan → always active, unlimited timer
    - Hourly plan → check Redis timer
    """
    now = datetime.now(timezone.utc)

    # Query active subscription with plan eager-loaded
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.is_active == True,
                Subscription.expires_at > now,
            )
        )
    )
    subscription = result.scalars().first()

    # No active subscription
    if not subscription:
        return SessionStatusResponse(
            is_active=False,
            remaining_seconds=0,
            files_used=0,
            files_allowed=0,
            plan_name="none",
        )

    plan = subscription.plan

    # Monthly plan — no timer, unlimited
    if plan.name == "monthly":
        return SessionStatusResponse(
            is_active=True,
            remaining_seconds=-1,
            files_used=0,
            files_allowed=-1,
            plan_name="monthly",
        )

    # Hourly plan — check Redis timer
    if plan.name == "hourly":
        user_id_str = str(current_user.id)
        remaining = get_session_remaining(user_id_str)

        if remaining <= 0:
            return SessionStatusResponse(
                is_active=False,
                remaining_seconds=0,
                files_used=0,
                files_allowed=plan.max_files_per_month,
                plan_name="hourly",
            )

        return SessionStatusResponse(
            is_active=True,
            remaining_seconds=remaining,
            files_used=get_session_files_used(user_id_str),
            files_allowed=plan.max_files_per_month,
            plan_name="hourly",
        )

    # Fallback for any other plan type (e.g. "free")
    return SessionStatusResponse(
        is_active=True,
        remaining_seconds=-1,
        files_used=0,
        files_allowed=plan.max_files_per_month,
        plan_name=plan.name,
    )
