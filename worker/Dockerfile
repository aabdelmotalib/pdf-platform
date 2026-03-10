FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for PDF processing and document conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    libmagic1 \
    libreoffice \
    poppler-utils \
    tesseract-ocr \
    imagemagick \
    ghostscript \
    graphicsmagick \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    fonts-noto-cjk \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies (same as API + additional worker-specific packages)
RUN pip install \
    fastapi==0.104.1 \
    'uvicorn[standard]==0.24.0' \
    celery==5.3.4 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9 \
    pymupdf==1.23.8 \
    PyPDF2==3.0.1 \
    pypdf==3.17.4 \
    pdf2image==1.16.3 \
    pytesseract==0.3.10 \
    python-magic==0.4.27 \
    'python-jose[cryptography]==3.3.0' \
    'passlib[bcrypt]==1.7.4' \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    minio==7.2.0 \
    aiofiles==23.2.1 \
    pillow==10.1.0 \
    requests==2.31.0 \
    'sqlalchemy>=2.0.0,<3.0' \
    'alembic>=1.13.0' \
    python-multipart==0.0.6 \
    httpx==0.25.2 \
    pyhanko==0.22.0 \
    clamd==1.0.2 \
    python-docx==0.8.11 \
    openpyxl==3.1.5 \
    'librosa>=0.9.0'

# Create app user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=4"]
