# API Extension - Celery Worker Service Skeleton

This Dockerfile and supporting files are for the Celery Worker service.

## Structure

```
worker/
├── Dockerfile          # Container definition
├── main.py            # Celery app initialization
├── config.py          # Celery configuration
├── tasks.py           # Task definitions
├── pdf_processor.py   # PDF processing logic
├── converters/        # Format-specific converters
│   ├── __init__.py
│   ├── pdf_to_image.py
│   ├── pdf_to_text.py
│   ├── pdf_merge.py
│   └── pdf_split.py
└── utils/             # Worker utilities
    ├── __init__.py
    ├── logger.py
    └── exceptions.py
```

## System Dependencies

The worker container includes extra system packages:

- **LibreOffice**: Document format conversion
- **Poppler**: PDF rendering
- **Tesseract**: OCR (text extraction)
- **ImageMagick**: Image processing
- **Ghostscript**: PostScript/PDF handling

## Quick Start

Workers process asynchronous tasks from the Redis message broker.

### Monitoring

Access Flower monitoring dashboard:
- **Flower UI**: `https://localhost/flower`
- Shows active tasks, completed tasks, worker status

## Environment Variables

Workers use the same `.env` file variables:

```
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
MINIO_ENDPOINT=minio:9000
CLAMAV_HOST=clamav
```

## Dependencies

Key packages for task processing:

- **Celery**: Distributed task queue
- **PyMuPDF**: PDF manipulation
- **pytesseract**: OCR integration
- **pyhanko**: PDF signing
- **python-docx**: DOCX generation
- **openpyxl**: XLSX manipulation

## Development

```bash
# Run worker locally
celery -A tasks worker --loglevel=info

# Inspect active tasks
celery -A tasks inspect active

# View task stats
celery -A tasks inspect stats

# Purge all tasks
celery -A tasks purge
```

## Scaling Workers

To run multiple workers:

```bash
# Scale to 4 workers
docker-compose up -d --scale worker=4

# View all workers
docker-compose ps | grep worker
```

## See Also

- [Main README](../README.md)
- [Setup Instructions](../SETUP.md)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Flower Documentation](https://flower.readthedocs.io/)
