FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install \
    fastapi==0.104.1 \
    'uvicorn[standard]==0.24.0' \
    celery==5.3.4 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9 \
    pymupdf==1.23.8 \
    PyPDF2==3.0.1 \
    pytesseract==0.3.10 \
    python-magic==0.4.27 \
    'python-jose[cryptography]==3.3.0' \
    'passlib[bcrypt]==1.7.4' \
    'pydantic[email]==2.5.0' \
    pydantic-settings==2.1.0 \
    minio==7.2.0 \
    aiofiles==23.2.1 \
    pillow==10.1.0 \
    requests==2.31.0 \
    'sqlalchemy>=2.0.0,<3.0' \
    'alembic>=1.13.0' \
    python-multipart==0.0.6 \
    httpx==0.25.2 \
    clamd==1.0.2 \
    pyclamd==0.4.0 \
    asyncpg==0.29.0 \
    bcrypt==3.2.2 \
    slowapi==0.1.9
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
