"""
Configuration settings for PDF Platform API

All settings are loaded from environment variables with sensible defaults.
For production, set these environment variables in .env or deployment config.
"""

import os
from datetime import timedelta


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "POSTGRES_DSN",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform"
    )
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

    # JWT Configuration
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-this-in-production-min-32-chars-ok"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # SMTP Configuration (Brevo)
    BREVO_SMTP_HOST: str = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
    BREVO_SMTP_PORT: int = int(os.getenv("BREVO_SMTP_PORT", "587"))
    BREVO_SMTP_USER: str = os.getenv("BREVO_SMTP_USER", "your-email@example.com")
    BREVO_SMTP_PASSWORD: str = os.getenv("BREVO_SMTP_PASSWORD", "your-brevo-smtp-key")
    BREVO_FROM_EMAIL: str = os.getenv("BREVO_FROM_EMAIL", "noreply@pdfplatform.com")
    BREVO_FROM_NAME: str = os.getenv("BREVO_FROM_NAME", "PDF Platform")

    # API Configuration
    API_TITLE: str = "PDF Conversion Platform"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "PDF conversion and processing platform for Egyptian market"
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/15minutes"  # 5 attempts per 15 minutes
    RATE_LIMIT_REGISTER: str = "10/hour"  # 10 attempts per hour

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ]

    # Cookie Settings
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", None)
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() != "false"
    COOKIE_SAME_SITE: str = os.getenv("COOKIE_SAME_SITE", "lax")

    # Password Requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # Email Verification Token Expiry (hours)
    EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS: int = 24

    # MinIO Storage Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_INPUT_FILES_BUCKET: str = "input-files"
    MINIO_OUTPUT_FILES_BUCKET: str = "output-files"

    # ClamAV Anti-virus Configuration
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "localhost")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))
    CLAMAV_TIMEOUT: int = 30  # Timeout for ClamAV scan

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 100  # Absolute maximum file size
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/jpeg",
        "image/png",
    ]

    # Subscription Defaults
    FREE_PLAN_ID: int = 1
    HOURLY_PLAN_ID: int = 2
    MONTHLY_PLAN_ID: int = 3

    # Paymob Configuration
    PAYMOB_API_KEY: str = os.getenv("PAYMOB_API_KEY", "")
    PAYMOB_HMAC_SECRET: str = os.getenv("PAYMOB_HMAC_SECRET", "")
    PAYMOB_INTEGRATION_ID_CARD: int = int(os.getenv("PAYMOB_INTEGRATION_ID_CARD", "0"))
    PAYMOB_INTEGRATION_ID_WALLET: int = int(os.getenv("PAYMOB_INTEGRATION_ID_WALLET", "0"))
    PAYMOB_INTEGRATION_ID_INSTAPAY: int = int(os.getenv("PAYMOB_INTEGRATION_ID_INSTAPAY", "0"))
    PAYMOB_INTEGRATION_ID_FAWRY: int = int(os.getenv("PAYMOB_INTEGRATION_ID_FAWRY", "0"))
    PAYMOB_TEST_MODE: bool = os.getenv("PAYMOB_TEST_MODE", "true").lower() == "true"
    PAYMOB_IFRAME_ID: int = int(os.getenv("PAYMOB_IFRAME_ID", "0")) # Added for URL building



# Create singleton settings instance
settings = Settings()
