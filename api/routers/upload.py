"""
Upload router — file upload and job status endpoints.

POST /upload/files      → validate, scan, store, create job, dispatch task
GET  /upload/jobs/{id}  → job status + presigned download URL
"""

import os
import uuid
import logging
from datetime import datetime, timezone

import clamd
from celery import Celery as _Celery
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from db import Job, Subscription, get_db
from dependencies import get_current_user
from db.models import User
from schemas import JobStatusResponse, UploadResponse
from services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# ---------------------------------------------------------------------------
# Celery proxy — no direct worker imports
# ---------------------------------------------------------------------------
_celery_app = _Celery(
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
)

# ---------------------------------------------------------------------------
# ClamAV scanner
# ---------------------------------------------------------------------------
CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", "3310"))

# ---------------------------------------------------------------------------
# Allowed MIME → job_type mapping
# ---------------------------------------------------------------------------
MIME_TO_JOB_TYPE: dict[str, str] = {
    "application/pdf": "pdf_to_word",
    "application/msword": "word_to_pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word_to_pdf",
}


def _scan_file(file_bytes: bytes) -> None:
    """Scan file bytes with ClamAV. Raises HTTPException if infected."""
    import io
    try:
        scanner = clamd.ClamdNetworkSocket(host=CLAMAV_HOST, port=CLAMAV_PORT, timeout=30)
        result = scanner.instream(io.BytesIO(file_bytes))
        # result looks like: {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
        scan_status, signature = result.get("stream", ("ERROR", None))
        if scan_status == "FOUND":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File is infected: {signature}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"ClamAV scan failed (proceeding anyway): {exc}")


# ---------------------------------------------------------------------------
# POST /upload/files
# ---------------------------------------------------------------------------
@router.post("/files", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file for conversion.

    1. Validate MIME type
    2. Scan with ClamAV
    3. Upload to MinIO (input-files bucket)
    4. Create Job row
    5. Dispatch Celery task
    6. Return job_id
    """
    # 1. Read file -----------------------------------------------------------
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Detect MIME from content type header
    detected_mime = file.content_type or "application/octet-stream"

    # 2. Validate MIME type --------------------------------------------------
    if detected_mime not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {detected_mime}. Allowed: {settings.ALLOWED_MIME_TYPES}",
        )

    # 3. Scan with ClamAV ---------------------------------------------------
    _scan_file(file_bytes)

    # 4. Hourly session enforcement ------------------------------------------
    now = datetime.now(timezone.utc)
    sub_result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.user_id == current_user.id,
            Subscription.is_active == True,
            Subscription.expires_at > now,
        )
    )
    subscription = sub_result.scalars().first()

    if subscription and subscription.plan.name == "hourly":
        from services.session_timer import get_session_remaining, increment_session_files

        remaining = get_session_remaining(str(current_user.id))
        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SESSION_EXPIRED: Your 1-hour session has ended. Purchase a new session to continue.",
            )
        files_used = increment_session_files(str(current_user.id))
        if files_used > subscription.plan.max_files_per_month:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"FILE_LIMIT: Session file limit reached ({subscription.plan.max_files_per_month} files per session).",
            )

    # 5. Upload to MinIO ----------------------------------------------------
    job_id = uuid.uuid4()
    original_filename = file.filename or "upload"
    object_key = f"jobs/{current_user.id}/{job_id}/{original_filename}"

    storage = StorageService(bucket_name="input-files")
    storage.upload_file(file_bytes, object_key, content_type=detected_mime)

    # 5. Determine job_type from MIME ----------------------------------------
    job_type = "pdf_to_word"  # default
    if detected_mime in (
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        job_type = "word_to_pdf"

    # 6. Create Job ----------------------------------------------------------
    db_job = Job(
        id=job_id,
        user_id=current_user.id,
        job_type=job_type,
        status="queued",
        input_file_path=object_key,
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)

    # 7. Dispatch Celery task -----------------------------------------------
    _celery_app.send_task("tasks.convert.convert_file", args=[str(job_id)])

    logger.info(f"Job {job_id} created and dispatched — type={job_type}")

    return UploadResponse(
        job_id=job_id,
        status="queued",
        message="File queued for processing",
    )


# ---------------------------------------------------------------------------
# GET /upload/jobs/{job_id}/status
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get job status and download URL (if completed)."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Ownership check
    if str(job.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your job",
        )

    # Build download URL if completed
    download_url = None
    if job.status == "completed" and job.output_file_path:
        try:
            output_storage = StorageService(bucket_name="output-files")
            download_url = output_storage.get_presigned_download_url(
                job.output_file_path, expiry_seconds=3600
            )
        except Exception as exc:
            logger.warning(f"Failed to generate download URL: {exc}")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=100 if job.status == "completed" else 0,
        error_message=job.error_message,
        input_file_path=job.input_file_path,
        output_file_path=job.output_file_path,
        download_url=download_url,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
