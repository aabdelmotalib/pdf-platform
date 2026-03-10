# API Extension - FastAPI Main Application Skeleton

This Dockerfile and supporting files are for the FastAPI API service.

## Structure

```
api/
├── Dockerfile          # Container definition
├── main.py            # FastAPI entry point
├── config.py          # Configuration loading
├── models/            # Database models
│   └── __init__.py
├── schemas/           # Pydantic schemas
│   └── __init__.py
├── routes/            # API route handlers
│   ├── __init__.py
│   ├── health.py      # Health check routes
│   ├── pdf.py         # PDF conversion routes
│   └── upload.py      # File upload routes
├── services/          # Business logic
│   ├── __init__.py
│   ├── pdf_service.py # PDF processing
│   └── storage.py     # MinIO integration
├── dependencies.py    # Dependency injection
└── utils/             # Utility functions
    ├── __init__.py
    ├── logger.py      # Logging configuration
    └── exceptions.py  # Custom exceptions
```

## Quick Start

The API runs on port 8000 and is proxied through Nginx on port 443.

### Access Points

- **API Root**: `https://localhost/api`
- **Swagger UI**: `https://localhost/api/docs`
- **ReDoc**: `https://localhost/api/redoc`
- **Health Check**: `https://localhost/health`

### Environment Variables

All needed variables are in the root `.env` file:

```
POSTGRES_DSN=postgresql://postgres:postgres@postgres:5432/pdf_platform
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
CELERY_BROKER_URL=redis://redis:6379/1
```

## Dependencies

See `../requirements.txt` for all Python packages. Key packages:

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **PyMuPDF**: PDF manipulation
- **Celery**: Task queue
- **Pydantic**: Data validation
- **python-jose**: JWT handling

## Development

```bash
# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/

# Lint code
flake8 .

# Format code
black .
```

## See Also

- [Main README](../README.md)
- [Setup Instructions](../SETUP.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
