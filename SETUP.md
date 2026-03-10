# Installation and Setup Instructions

## Prerequisites

Ensure you have the following installed on your Ubuntu system:

### 1. Docker Installation

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

Verify:
```bash
docker --version
docker run hello-world
```

### 2. Docker Compose Installation

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Verify:
```bash
docker-compose --version
```

### 3. Git Installation

```bash
sudo apt update
sudo apt install -y git
```

### 4. OpenSSL (for certificate generation)

```bash
sudo apt install -y openssl
```

## First Time Setup

### Step 1: Navigate to Project

```bash
cd /home/abdelmoteleb/pdf-platform
```

### Step 2: Initialize SSL Certificates

```bash
./scripts/generate-ssl.sh
```

This creates self-signed certificates in `nginx/ssl/` for development.

### Step 3: Review Environment Variables

```bash
cat .env
```

Edit `.env` if needed:
```bash
nano .env
```

Key variables to configure:
- `POSTGRES_PASSWORD` - Database password
- `JWT_SECRET` - JWT signing secret
- `MINIO_SECRET_KEY` - MinIO secret
- `SMTP_PASSWORD` - Email credentials
- `PAYMOB_API_KEY` - Payment API key

### Step 4: Build Docker Images

```bash
docker-compose build
```

This may take 10-15 minutes as it downloads base images and installs dependencies.

### Step 5: Start Services

```bash
docker-compose up -d
```

Monitor startup:
```bash
docker-compose ps
docker-compose logs -f
```

Wait until all services show "healthy" status (typically 30-60 seconds).

### Step 6: Verify Installation

```bash
# Check all services are running
./scripts/docker-helper.sh health-check

# Test API endpoint
curl -k https://localhost/health

# Check database
docker-compose exec postgres pg_isready

# Check Redis
docker-compose exec redis redis-cli ping

# Check MinIO
docker-compose exec minio mc ready local
```

## Quick Start Commands

```bash
# Start platform
./scripts/docker-helper.sh up

# Stop platform
./scripts/docker-helper.sh down

# View logs
./scripts/docker-helper.sh logs api

# SSH into a container
./scripts/docker-helper.sh shell api

# View service status
./scripts/docker-helper.sh ps
```

## Configuration Files

### .env
Contains all environment variables for the stack. Edit this for your configuration.

### nginx/nginx.conf
Nginx configuration with routing, SSL, rate limiting, and security headers.

### docker-compose.yml
Main orchestration file with all 8 services.

### docker-compose.override.yml
Development-specific overrides (volume mounts, debug info, extra ports).

## Troubleshooting Installation

### Port Already in Use
```bash
# Find what's using the port
lsof -i :443
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Permission Denied
```bash
# Make sure you're in docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Disk Space Issues
```bash
# Check free space
df -h

# Clean up Docker
docker system prune -a
```

### Out of Memory
```bash
# Check available memory
free -h

# Increase Docker memory limit (if using Docker Desktop)
# Edit Docker Desktop settings or /etc/docker/daemon.json
```

### Can't Connect to Docker Daemon
```bash
# Start Docker service
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker
```

## Next Steps

1. **API Development**: Create endpoints in `api/main.py`
2. **Worker Tasks**: Define Celery tasks in `worker/tasks.py`
3. **Database**: Create SQLAlchemy models in `api/models/`
4. **Frontend**: Set up React app in `frontend/`
5. **Testing**: Add unit tests in `tests/` directory

## Performance Tips

- Use `docker-compose up -d` to run in background
- Use `--scale worker=n` to scale worker processes
- Monitor with Flower: https://localhost/flower
- Check logs regularly: `docker-compose logs -f api`
- Use health checks: `./scripts/docker-helper.sh health-check`

## Useful References

- FastAPI: https://fastapi.tiangolo.com/
- Celery: https://docs.celeryproject.org/
- Docker Compose: https://docs.docker.com/compose/
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/documentation
- MinIO: https://docs.min.io/
- Nginx: https://nginx.org/en/docs/

---

For additional help, check the main README.md file.
