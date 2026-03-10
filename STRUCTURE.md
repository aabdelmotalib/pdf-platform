# Project Structure Documentation

## Complete Directory Layout

```
/home/abdelmoteleb/pdf-platform/
│
├── docker-compose.yml              ✓ Main orchestration (8 services)
├── docker-compose.override.yml     ✓ Development overrides
├── .env                            ✓ Environment variables (configured)
├── .env.example                    ✓ Environment template
├── .dockerignore                   ✓ Docker build ignore patterns
├── .gitignore                      ✓ Git ignore patterns
├── requirements.txt                ✓ Python dependencies
│
├── README.md                       ✓ Main documentation
├── SETUP.md                        ✓ Installation instructions
├── TESTING.md                      ✓ Testing guide
├── STRUCTURE.md                    ✓ This file
│
├── api/                            ✓ FastAPI Application Service
│   ├── Dockerfile                  ✓ Python 3.12-slim base
│   ├── README.md                   ✓ API service documentation
│   └── README-extended.md          ✓ Extended API documentation
│
├── worker/                         ✓ Celery Worker Service
│   ├── Dockerfile                  ✓ With LibreOffice, Tesseract, Poppler
│   ├── README.md                   ✓ Worker service documentation
│   └── README-extended.md          ✓ Extended worker documentation
│
├── frontend/                       ✓ React.js Application
│   └── README.md                   ✓ Frontend documentation
│
├── nginx/                          ✓ Nginx Web Server
│   ├── nginx.conf                  ✓ Full config with:
│   │                                 - HTTPS/SSL setup
│   │                                 - Rate limiting (10 req/min upload)
│   │                                 - Proxy to api:8000
│   │                                 - Static file serving
│   │                                 - Security headers
│   │                                 - Internal port blocking
│   └── ssl/                        ✓ SSL certificates directory
│       ├── server.crt              (Generated on setup)
│       └── server.key              (Generated on setup)
│
├── docker/                         ✓ Docker utilities
│   └── .dockerignore              ✓ Docker ignore patterns
│
└── scripts/                        ✓ Utility Scripts
    ├── generate-ssl.sh             ✓ Generate self-signed certificates
    ├── docker-helper.sh            ✓ Docker helper commands
    └── init.sh                     ✓ First-time setup script
```

## Service Architecture

### Service Descriptions and Requirements

#### 1. PostgreSQL (postgres:15-alpine)
- **Port**: 5432
- **Volume**: `postgres_data` (data persistence)
- **Health Check**: pg_isready
- **Dependencies**: None
- **Purpose**: Relational database for users, jobs, and metadata

#### 2. Redis (redis:7-alpine)
- **Port**: 6379
- **Volume**: `redis_data` (RDB persistence)
- **Health Check**: redis-cli ping
- **Dependencies**: None
- **Purpose**: Cache and message broker for Celery

#### 3. MinIO (minio/minio:latest)
- **Ports**: 9000 (API), 9001 (Console)
- **Volume**: `minio_data` (S3 data)
- **Health Check**: mc ready local
- **Dependencies**: None
- **Purpose**: S3-compatible object storage for files

#### 4. ClamAV (clamav/clamav:latest)
- **Port**: 3310
- **Volume**: `clamav_data` (virus definitions)
- **Health Check**: clamscan --version
- **Dependencies**: None
- **Purpose**: Antivirus scanning on upload

#### 5. FastAPI (api service)
- **Port**: 8000
- **Image**: Built from `api/Dockerfile`
- **Volume**: `./api` (code mount)
- **Health Check**: curl /health
- **Dependencies**: postgres, redis, minio, clamav
- **Purpose**: Main API application with endpoints
- **Base**: Python 3.12-slim + FastAPI, Uvicorn, etc.

#### 6. Celery Worker (worker service)
- **Ports**: None exposed
- **Image**: Built from `worker/Dockerfile`
- **Volume**: `./worker` (code mount)
- **Dependencies**: postgres, redis, minio, clamav, api
- **Purpose**: Async task processing
- **Base**: Python 3.12-slim + LibreOffice, Tesseract, Poppler, Pyhanko

#### 7. Flower (mher/flower:latest)
- **Port**: 5555
- **Dependencies**: redis, worker
- **Purpose**: Celery task monitoring dashboard

#### 8. Nginx (nginx:alpine)
- **Ports**: 80 (HTTP redirect), 443 (HTTPS)
- **Volumes**: 
  - `nginx/nginx.conf` (configuration)
  - `nginx/ssl/` (SSL certificates)
  - `frontend/dist` (static files, read-only)
- **Health Check**: wget /health
- **Dependencies**: api
- **Purpose**: Reverse proxy, load balancing, SSL termination

## Environment Variable Configuration

### Docker Services Variables
```
POSTGRES_USER           Database user
POSTGRES_PASSWORD       Database password
POSTGRES_DB            Database name
POSTGRES_DSN           Full PostgreSQL connection string

REDIS_URL              Redis connection string
MINIO_ENDPOINT         MinIO server address
MINIO_ACCESS_KEY       MinIO access key
MINIO_SECRET_KEY       MinIO secret key
CELERY_BROKER_URL      Celery message broker URL
CELERY_RESULT_BACKEND  Celery result backend
CLAMAV_HOST            ClamAV server address
CLAMAV_PORT            ClamAV server port
```

### Application Variables
```
API_HOST               FastAPI listen address (0.0.0.0)
API_PORT               FastAPI listen port (8000)
LOG_LEVEL              Logging level (info, debug)
SECRET_KEY             JWT signing key
JWT_SECRET             JWT secret key
ALGORITHM              JWT algorithm (HS256)
```

## Network Configuration

### Docker Network
- **Name**: `pdf_network`
- **Driver**: bridge
- **Scope**: Internal container-to-container communication

### Port Mapping (Host → Container)
```
80 → nginx:80               (HTTP redirect)
443 → nginx:443             (HTTPS)
8000 → api:8000             (FastAPI)
5555 → flower:5555          (Flower monitoring)
9000 → minio:9000           (MinIO API)
9001 → minio:9001           (MinIO Console)
5432 → postgres:5432        (PostgreSQL)
6379 → redis:6379           (Redis)
3310 → clamav:3310          (ClamAV)
```

## Volume Mapping

### Named Volumes
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis RDB dump and AOF files
- `minio_data`: MinIO object storage
- `clamav_data`: ClamAV virus definitions

### Bind Mounts
- `./api:/app` → API source code
- `./worker:/app` → Worker source code
- `./nginx/nginx.conf` → Nginx configuration
- `./nginx/ssl/` → SSL certificates
- `./frontend/dist/` → Built React app

## Dockerfile Technology Details

### API Dockerfile
- **Base**: python:3.12-slim
- **Key Packages**:
  - FastAPI, Uvicorn
  - Celery, Redis
  - SQLAlchemy, Psycopg2
  - PyMuPDF, PyPDF2, Pytesseract
  - python-magic, python-jose
  - Passlib, Pydantic
  - MinIO, Clamd
  - Aiofiles, Pillow, Requests
- **User**: appuser (1000)

### Worker Dockerfile
- **Base**: python:3.12-slim
- **System Packages Added**:
  - libreoffice-headless
  - poppler-utils
  - tesseract-ocr
  - imagemagick
  - ghostscript
  - fonts (DejaVu, Liberation, Noto, Noto CJK)
- **All API packages** + extra:
  - PyHanko (PDF signing)
  - python-docx (DOCX generation)
  - openpyxl (XLSX handling)
  - librosa (audio processing)
- **User**: appuser (1000)

## Nginx Configuration

### Features Implemented
1. **SSL/TLS**
   - Self-signed certificate for development
   - Path: `nginx/ssl/server.crt` and `server.key`

2. **Rate Limiting**
   - General API: 30 req/min (5 burst)
   - Upload endpoint: 10 req/min (2 burst)
   - Download endpoint: 20 req/min (3 burst)

3. **Proxy Configuration**
   - `/api/*` → `http://api:8000`
   - `/` → `/frontend/dist` (React app)
   - `/flower/*` → `http://flower:5555` (restricted)

4. **Security Headers**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: enabled
   - Content-Security-Policy: set
   - Referrer-Policy: restricted

5. **Access Control**
   - Blocks external access to internal ports (9000, 9001, 5555, 3310, 6379, 5432)
   - Flower restricted to localhost/Docker network
   - Denies hidden files (.*) and backups (~)

## Health Checks Configuration

All services include health checks with:
- **`interval`**: 10s (check every 10 seconds)
- **`timeout`**: 5s (timeout per check)
- **`retries`**: 3-5 retries before marked unhealthy

### Health Check Methods
- **postgres**: `pg_isready`
- **redis**: `redis-cli ping`
- **minio**: `mc ready local`
- **clamav**: `clamscan --version`
- **api**: `curl http://localhost:8000/health`
- **nginx**: `wget http://localhost/health`

## Scaling Strategy

### Horizontal Scaling
```bash
# Scale workers to 4 instances
docker-compose up -d --scale worker=4

# Each worker processes tasks independently
# Celery automatically distributes work via Redis broker
```

### Resource Limits (Can add to docker-compose.yml)
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Development Overrides

The `docker-compose.override.yml` provides:
- **Volume mounts** for hot-reload code development
- **Environment variables** for debug logging
- **Exposed ports** for direct service access
- **Extended timeouts** for debugging

## Database Schema

PostgreSQL is initialized with empty state. Create tables in:
1. `api/models/` - Define SQLAlchemy models
2. Run migrations with Alembic

## Celery Configuration

- **Broker**: Redis (database 1)
- **Backend**: Redis (database 2)
- **Worker Concurrency**: 4 processes
- **Auto-discover**: Tasks from `worker/tasks.py`
- **Monitoring**: Flower on port 5555

## MinIO Configuration

- **Buckets to create**: `input-files`, `output-files`
- **Access**: HTTP (non-SSL) for internal communication
- **Console**: Available at `http://localhost:9001`
- **API**: Available at `http://localhost:9000`

## Frontend Integration

- **Build output**: Must be in `frontend/dist/`
- **Served by**: Nginx at `/`
- **Static assets**: Cached for 30 days
- **SPA routing**: `try_files $uri $uri/ /index.html`

---

**Project created for Egyptian PDF conversion market** ✨
