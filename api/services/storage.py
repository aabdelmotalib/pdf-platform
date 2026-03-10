"""
Storage service for handling file uploads to MinIO and presigned URLs.

Provides:
- MinIO connection and bucket management
- File upload with key based on user_id/job_id/filename
- Presigned download URLs
- File deletion
"""

import io
from typing import Optional

from minio import Minio
from minio.error import S3Error
from config import settings


class StorageService:
    """Handle file storage operations with MinIO."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: str = "input-files"
    ):
        """
        Initialize MinIO storage service.

        Args:
            endpoint: MinIO endpoint (default from settings)
            access_key: MinIO access key (default from settings)
            secret_key: MinIO secret key (default from settings)
            bucket_name: Bucket name for file storage
        """
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket_name = bucket_name

        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=settings.MINIO_SECURE
        )

        # Bucket creation is lazy — called on first use

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✓ Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket {self.bucket_name}: {str(e)}")
            raise

    def upload_file(
        self,
        file_content: bytes,
        object_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO bucket.

        Args:
            file_content: File bytes to upload
            object_key: Object key (e.g., jobs/{user_id}/{job_id}/{filename})
            content_type: MIME type of file

        Returns:
            Object key (path) in MinIO

        Raises:
            S3Error: If upload fails
        """
        try:
            # Create file-like object
            file_stream = io.BytesIO(file_content)
            file_size = len(file_content)

            # Upload file
            self.client.put_object(
                self.bucket_name,
                object_key,
                file_stream,
                length=file_size,
                content_type=content_type
            )

            print(f"✓ Uploaded {object_key} ({file_size} bytes)")
            return object_key

        except S3Error as e:
            print(f"Error uploading file {object_key}: {str(e)}")
            raise

    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from MinIO bucket.

        Args:
            object_key: Object key to delete

        Returns:
            True if deleted successfully

        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.remove_object(self.bucket_name, object_key)
            print(f"✓ Deleted {object_key}")
            return True

        except S3Error as e:
            print(f"Error deleting file {object_key}: {str(e)}")
            raise

    def get_presigned_download_url(
        self,
        object_key: str,
        expiry_seconds: int = 3600
    ) -> str:
        """
        Generate presigned download URL for file.

        Args:
            object_key: Object key in bucket
            expiry_seconds: URL expiry time in seconds (default 1 hour)

        Returns:
            Presigned download URL

        Raises:
            S3Error: If URL generation fails
        """
        try:
            url = self.client.get_presigned_download_url(
                self.bucket_name,
                object_key,
                expires=expiry_seconds
            )
            print(f"✓ Generated presigned URL for {object_key}")
            return url

        except S3Error as e:
            print(f"Error generating presigned URL for {object_key}: {str(e)}")
            raise

    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in bucket.

        Args:
            object_key: Object key to check

        Returns:
            True if file exists
        """
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except S3Error:
            return False

    def get_file(self, object_key: str) -> Optional[bytes]:
        """
        Download file from MinIO bucket.

        Args:
            object_key: Object key to download

        Returns:
            File bytes if exists, None otherwise

        Raises:
            S3Error: If download fails
        """
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            content = response.read()
            response.close()
            print(f"✓ Downloaded {object_key} ({len(content)} bytes)")
            return content

        except S3Error as e:
            print(f"Error downloading file {object_key}: {str(e)}")
            raise


# Storage service singleton
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


async def upload_file_async(
    file_content: bytes,
    object_key: str,
    content_type: str = "application/octet-stream"
) -> str:
    """
    Async wrapper for file upload.

    Args:
        file_content: File bytes
        object_key: Object key in MinIO
        content_type: MIME type

    Returns:
        Object key in MinIO
    """
    storage = get_storage_service()
    return storage.upload_file(file_content, object_key, content_type)


async def delete_file_async(object_key: str) -> bool:
    """
    Async wrapper for file deletion.

    Args:
        object_key: Object key to delete

    Returns:
        True if deleted
    """
    storage = get_storage_service()
    return storage.delete_file(object_key)


async def get_presigned_url_async(
    object_key: str,
    expiry_seconds: int = 3600
) -> str:
    """
    Async wrapper for presigned URL generation.

    Args:
        object_key: Object key in MinIO
        expiry_seconds: URL expiry time

    Returns:
        Presigned download URL
    """
    storage = get_storage_service()
    return storage.get_presigned_download_url(object_key, expiry_seconds)
