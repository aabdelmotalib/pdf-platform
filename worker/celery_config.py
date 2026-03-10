"""Celery Configuration"""

import os
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

app = Celery("pdf_platform", broker=BROKER_URL, backend=BACKEND_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=120,
    task_time_limit=150,
    task_max_retries=3,
    task_default_retry_delay=60,
    result_expires=3600,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_default_queue="default",
    # Disable autodiscovery to prevent import errors
    autodiscover_ignore_patterns=["*/migrations/*"],
)

# Explicitly disable autodiscovery
app.autodiscovered = True

# Import tasks to register them with celery
# Must be after app.conf.update() to avoid circular imports
try:
    from tasks import convert  # noqa: F401
    import logging
    logging.info("✅ Successfully imported tasks.convert")
except ImportError as e:
    import logging
    logging.error(f"❌ Could not import tasks.convert: {e}", exc_info=True)

