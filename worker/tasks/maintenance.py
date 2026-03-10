"""
Maintenance tasks — periodic housekeeping jobs.

expire_subscriptions: Marks expired hourly subscriptions as inactive in
PostgreSQL.  Runs every 5 minutes via Celery Beat.
"""

import os
import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as DBSession

from celery_config import app

logger = logging.getLogger(__name__)

# Sync DSN — worker uses psycopg2, not asyncpg
_raw_dsn = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/pdf_platform",
)
_sync_dsn = _raw_dsn.replace("+asyncpg", "+psycopg2").replace("postgresql://", "postgresql+psycopg2://") \
    if "+asyncpg" not in _raw_dsn and "psycopg2" not in _raw_dsn \
    else _raw_dsn.replace("+asyncpg", "+psycopg2")

_engine = create_engine(_sync_dsn, pool_pre_ping=True)


@app.task(name="tasks.maintenance.expire_subscriptions")
def expire_subscriptions():
    """
    Sync expired subscriptions from Redis TTL reality to PostgreSQL.

    Finds all subscriptions where is_active=True AND expires_at < now(),
    then sets is_active=False.  This catches hourly sessions that ended
    while the API wasn't looking.
    """
    from db_models import Subscription

    now = datetime.now(timezone.utc)

    with DBSession(_engine) as db:
        result = db.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.expires_at < now,
            )
        )
        expired = result.scalars().all()

        for sub in expired:
            sub.is_active = False

        db.commit()

        count = len(expired)
        if count > 0:
            logger.info(f"Expired {count} subscription(s)")
        return {"expired_count": count}
