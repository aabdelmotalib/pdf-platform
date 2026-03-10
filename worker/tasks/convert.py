"""
Celery task for file conversion.

Fetches job from DB, downloads input from MinIO, runs the appropriate
processor, uploads the output back to MinIO, and updates job status.
"""

import os
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session as DBSession
from minio import Minio

from db_models import Job, Subscription, Plan
from tasks.processors import PROCESSORS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database setup (sync — worker uses psycopg2, not asyncpg)
# ---------------------------------------------------------------------------
_raw_dsn = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/pdf_platform",
)
# Replace asyncpg driver → psycopg2 for synchronous access
DATABASE_URL = _raw_dsn.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ---------------------------------------------------------------------------
# MinIO setup
# ---------------------------------------------------------------------------
INPUT_BUCKET = "input-files"
OUTPUT_BUCKET = "output-files"


def _get_minio_client() -> Minio:
    """Create a MinIO client from environment variables."""
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


# ---------------------------------------------------------------------------
# Output extension mapping
# ---------------------------------------------------------------------------
OUTPUT_EXTENSION: dict[str, str] = {
    "pdf_to_word": ".docx",
    "pdf_to_excel": ".xlsx",
    "pdf_to_image": ".jpg",
    "word_to_pdf": ".pdf",
    "pdf_merge": ".pdf",
    "pdf_split": ".pdf",
    "pdf_annotate": ".pdf",
    "pdf_watermark": ".pdf",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _update_job_status(
    session: DBSession,
    job: Job,
    *,
    status: str,
    output_file_path: str | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> None:
    """Persist a job status update."""
    job.status = status
    if output_file_path is not None:
        job.output_file_path = output_file_path
    if error_message is not None:
        job.error_message = error_message
    if started_at is not None:
        job.started_at = started_at
    if completed_at is not None:
        job.completed_at = completed_at
    session.commit()


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------
@shared_task(name="tasks.convert.convert_file", bind=True, max_retries=3)
def convert_file(self, job_id: str) -> dict:
    """
    Main conversion task.

    Args:
        job_id: UUID of the Job row to process.

    Returns:
        dict with job_id and final status.
    """
    session: DBSession = SessionLocal()
    minio = _get_minio_client()

    try:
        # 1. Load job ---------------------------------------------------
        job = session.execute(
            select(Job).where(Job.id == job_id)
        ).scalar_one_or_none()

        if job is None:
            logger.error(f"Job {job_id} not found")
            return {"job_id": job_id, "status": "failed", "error": "Job not found"}

        logger.info(f"Processing job {job_id} — type={job.job_type}")

        # 2. Mark as processing -----------------------------------------
        _update_job_status(
            session, job,
            status="processing",
            started_at=datetime.now(timezone.utc),
        )

        # 3. Validate conversion type -----------------------------------
        job_type = job.job_type
        if job_type not in PROCESSORS:
            raise ValueError(f"Unknown conversion type: {job_type}")

        # 4. Download input file from MinIO -----------------------------
        input_key = job.input_file_path  # e.g. jobs/{user_id}/{job_id}/file.pdf
        original_filename = Path(input_key).name

        tmp_dir = tempfile.mkdtemp(prefix="pdf_convert_")
        local_input_path = os.path.join(tmp_dir, original_filename)

        logger.info(f"Downloading {input_key} from {INPUT_BUCKET}")
        minio.fget_object(INPUT_BUCKET, input_key, local_input_path)

        # 5. Run processor ----------------------------------------------
        processor_fn = PROCESSORS[job_type]
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Running processor: {job_type}")
        local_output_path = processor_fn(local_input_path, output_dir)

        if not os.path.exists(local_output_path):
            raise FileNotFoundError(
                f"Processor did not create output file: {local_output_path}"
            )

        # 6. Upload output to MinIO ------------------------------------
        ext = OUTPUT_EXTENSION.get(job_type, ".bin")
        output_filename = f"output_{job_id}{ext}"
        output_key = f"jobs/{job_id}/{output_filename}"

        logger.info(f"Uploading {output_key} to {OUTPUT_BUCKET}")

        # Ensure output bucket exists
        if not minio.bucket_exists(OUTPUT_BUCKET):
            minio.make_bucket(OUTPUT_BUCKET)

        minio.fput_object(OUTPUT_BUCKET, output_key, local_output_path)

        # 7. Mark as completed -----------------------------------------
        _update_job_status(
            session, job,
            status="completed",
            output_file_path=output_key,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(f"Job {job_id} completed successfully")
        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.exception(f"Job {job_id} failed: {exc}")

        # Persist failure -----------------------------------------------
        try:
            if job is not None:
                _update_job_status(
                    session, job,
                    status="failed",
                    error_message=str(exc)[:500],
                    completed_at=datetime.now(timezone.utc),
                )
        except Exception:
            logger.exception("Failed to update job status after error")

        return {"job_id": job_id, "status": "failed", "error": str(exc)}

    finally:
        session.close()

        # Clean up temp files
        try:
            import shutil
            if "tmp_dir" in locals() and tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
