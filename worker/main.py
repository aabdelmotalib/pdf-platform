"""
Celery Worker Entry Point
Start with: celery -A worker.main worker --loglevel=info --concurrency=2
"""

import os
import logging
from worker.celery_config import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    logger.info(f"Redis Broker: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
    logger.info(f"Max Retries: {app.conf.task_max_retries}")
    logger.info(f"Task Timeout: {app.conf.task_soft_time_limit}s")
    
    app.start([
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # Limit concurrency to prevent resource saturation
        "-c", "2",             # 2 concurrent tasks
        "-n", "celery_worker@%h",  # Worker name
        "-Q", "default,pdf_processing",  # Listen to both queues
        "--time-limit=150",  # Hard task time limit
        "--soft-time-limit=120",  # Soft task time limit
    ])
