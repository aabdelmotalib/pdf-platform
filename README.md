# PDF Conversion Platform - Egyptian Market Edition

A comprehensive PDF conversion platform built with FastAPI, Celery, PostgreSQL, Redis, MinIO, and more. Designed for the Egyptian market with PAYMOB payment integration support.

## Features

- **PDF Processing**: Convert, merge, split, and extract text from PDFs
- **Antivirus Scanning**: ClamAV integration for malware detection
- **Task Queue**: Celery workers for async PDF processing
- **File Storage**: MinIO for S3-compatible object storage
- **Real-time Monitoring**: Flower dashboard for Celery monitoring
- **Security**: Rate limiting, HTTPS support, JWT authentication
- **Scalability**: Docker-based microservices architecture
- **Payment Integration**: PAYMOB for Egyptian market

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **File Storage**: MinIO (S3-compatible)
- **Antivirus**: ClamAV
- **Frontend**: React.js
- **Web Server**: Nginx
- **Container Orchestration**: Docker Compose
- **Monitoring**: Flower

## Prerequisites

- Ubuntu Linux (18.04+)
- Docker 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

### 1. Clone and Setup

```bash
cd /home/abdelmoteleb/pdf-platform
git init
git add .
git commit -m "Initial commit"
```

### 2. Generate SSL Certificates

```bash
./scripts/generate-ssl.sh
```

### 3. Start Services

```bash
./scripts/docker-helper.sh up
```

Wait for all services to become healthy (30-60 seconds).

### 4. Verify Health

```bash
./scripts/docker-helper.sh health-check
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| API | https://localhost/api | FastAPI endpoints |
| API Docs | https://localhost/api/docs | Swagger UI documentation |
| Health Check | https://localhost/health | Service health |
| Flower Monitor | https://localhost/flower | Celery task monitoring |
| MinIO Console | https://localhost:9001 | S3 storage console |
| Frontend | https://localhost | React app (serve from /frontend/dist) |

### Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| MinIO | minioadmin | minioadmin |
| PostgreSQL | postgres | postgres |
| Flower | - | - (no auth by default) |

## Project Structure

```
pdf-platform/
├── api/                    # FastAPI application
│   ├── Dockerfile         # API service container
│   ├── main.py           # FastAPI entry point
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── routes/           # API endpoints
│   └── services/         # Business logic
├── worker/                # Celery worker service
│   ├── Dockerfile        # Worker service container
│   ├── main.py          # Celery app initialization
│   ├── tasks.py         # Task definitions
│   └── pdf_processor.py # PDF processing logic
├── frontend/              # React.js application
│   ├── src/             # React source code
│   ├── dist/            # Build output (served by Nginx)
│   └── package.json
├── nginx/                 # Nginx web server
│   ├── nginx.conf       # Nginx configuration
│   └── ssl/             # SSL certificates for HTTPS
├── docker/                # Docker-related files
├── scripts/               # Utility scripts
│   ├── init.sh          # Initial setup script
│   ├── generate-ssl.sh  # SSL certificate generator
│   └── docker-helper.sh # Docker helper commands
├── docker-compose.yml     # Services orchestration
├── .env                   # Environment variables
├── .dockerignore         # Docker build ignore
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Common Commands

```bash
# Start all services
./scripts/docker-helper.sh up

# Stop all services
./scripts/docker-helper.sh down

# View logs
./scripts/docker-helper.sh logs api

# Open shell in container
./scripts/docker-helper.sh shell api

# Health check
./scripts/docker-helper.sh health-check

# Restart services
./scripts/docker-helper.sh restart

# Clean up (keep data)
./scripts/docker-helper.sh clean

# Clean up completely (remove data)
./scripts/docker-helper.sh clean-all

# Initialize MinIO buckets
./scripts/docker-helper.sh minio-init
```

## Service Port Mapping

| Service | Port | Purpose |
|---------|------|---------|
| Nginx HTTP | 80 | Redirect to HTTPS |
| Nginx HTTPS | 443 | Main entry point |
| FastAPI | 8000 | API service |
| Flower | 5555 | Celery monitoring |
| MinIO API | 9000 | S3-compatible API |
| MinIO Console | 9001 | Storage management |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Message broker |
| ClamAV | 3310 | Antivirus service |

## Configuration

### Environment Variables

Edit `.env` to customize configuration:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pdf_platform

# Authentication
JWT_SECRET=your-secret-key

# S3 Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Email notifications
SMTP_HOST=smtp-relay.brevo.com
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password

# Payment (Egyptian market)
PAYMOB_API_KEY=your-api-key
PAYMOB_HMAC_SECRET=your-secret
```

## Health Checks

All services have built-in health checks. Monitor them with:

```bash
# Watch container health
docker-compose ps

# Check specific service
docker-compose exec api curl http://localhost:8000/health

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f api
```

## Testing

### API Endpoints

```bash
# Health check
curl https://localhost/health

# API documentation
curl https://localhost/api/docs

# Example API call
curl -X GET https://localhost/api/status
```

### Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d pdf_platform

# Example queries
\dt              # List tables
SELECT * FROM users;  # View users
```

### Celery Tasks

```bash
# View tasks in Flower
# Open: https://localhost/flower

# Check active tasks
docker-compose exec worker celery -A tasks inspect active

# Purge tasks
docker-compose exec worker celery -A tasks purge
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs api
docker-compose logs worker
docker-compose logs postgres

# Rebuild images
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database connection errors

```bash
# Ensure postgres is running
docker-compose exec postgres pg_isready

# Check PostgreSQL logs
docker-compose logs postgres
```

### MinIO connection issues

```bash
# Check MinIO is running
docker-compose exec minio mc ready local

# View MinIO logs
docker-compose logs minio
```

### Rate limiting not working

Verify Nginx is correctly proxying requests and has active rate limiting zones.

### SSL Certificate issues

```bash
# Regenerate certificates
./scripts/generate-ssl.sh

# Verify certificate
openssl x509 -in nginx/ssl/server.crt -text -noout
```

## Docker Commands Reference

```bash
# View all containers
docker-compose ps

# View container health
docker-compose ps --format "table {{.Service}}\t{{.Status}}"

# Execute command in container
docker-compose exec <service> <command>

# View container logs
docker-compose logs <service> -f

# Stop specific service
docker-compose stop <service>

# Restart specific service
docker-compose restart <service>

# Remove containers (keep volumes)
docker-compose down

# Remove everything
docker-compose down -v --rmi all
```

## Next Steps

1. **Implement API Routes**: Add PDF conversion endpoints in `api/routes/`
2. **Create Celery Tasks**: Define processing tasks in `worker/tasks.py`
3. **Build Frontend**: Develop React components in `frontend/src/`
4. **Database Models**: Define schemas in `api/models/`
5. **Authentication**: Implement JWT auth in `api/services/auth.py`
6. **Testing**: Add unit and integration tests
7. **Deployment**: Configure for production environment

## Development Tips

- Use `docker-compose logs -f` to monitor all services in real-time
- Access Flower at https://localhost/flower for task monitoring
- Use PostgreSQL Admin (pgAdmin) UI for database management
- Keep `.env` file secure and never commit credentials
- Use health checks frequently during development

## Production Considerations

1. **SSL Certificates**: Use real certificates from a trusted CA
2. **Environment**: Set `ENVIRONMENT=production` and `DEBUG=false`
3. **Secrets**: Use a secrets manager for sensitive data
4. **Database**: Use managed PostgreSQL service or backup strategy
5. **Storage**: Configure S3-compatible storage properly
6. **Rate Limiting**: Adjust limits based on your needs
7. **Monitoring**: Set up proper logging and monitoring
8. **Backups**: Implement database and file backup strategies

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
1. Check logs: `./scripts/docker-helper.sh logs`
2. Verify health: `./scripts/docker-helper.sh health-check`
3. Check .env configuration
4. Review service documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Created for the Egyptian PDF conversion market** ✨
