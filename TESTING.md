# Testing Guide - PDF Platform

Complete guide to testing the PDF Conversion Platform scaffold.

## Initial Setup Test

### 1. Verify Docker Installation

```bash
docker --version
docker-compose --version
```

Expected output:
```
Docker version 20.10+ (any recent version)
Docker Compose version 2.0+ (any recent version)
```

### 2. Verify File Structure

```bash
cd /home/abdelmoteleb/pdf-platform
ls -la

# Should show:
# api/
# worker/
# frontend/
# nginx/
# docker/
# scripts/
# docker-compose.yml
# docker-compose.override.yml
# .env
# README.md
# SETUP.md
```

### 3. Check SSL Certificates Generation

```bash
./scripts/generate-ssl.sh

# Should create:
# nginx/ssl/server.crt
# nginx/ssl/server.key
```

## Startup Test

### 1. Build Docker Images

```bash
docker-compose build

# Expected: All images build successfully
# This may take 10-15 minutes for first build
```

### 2. Start All Services

```bash
docker-compose up -d

# Wait 30-60 seconds for services to start
sleep 60
```

### 3. Check Service Status

```bash
# Method 1: Using helper script
./scripts/docker-helper.sh health-check

# Method 2: Direct docker-compose
docker-compose ps

# Method 3: Detailed status
docker-compose ps --format "table {{.Service}}\t{{.Status}}"
```

Expected output:
```
SERVICE         STATUS
pdf_postgres    Up (healthy)
pdf_redis       Up (healthy)
pdf_minio       Up (healthy)
pdf_clamav      Up (healthy)
pdf_api         Up (healthy)
pdf_worker      Up (healthy)
pdf_flower      Up (healthy)
pdf_nginx       Up (healthy)
```

## Service Connectivity Tests

### 1. Test PostgreSQL Connection

```bash
# Direct connection test
docker-compose exec postgres pg_isready

# Expected: accepting connections

# Query database
docker-compose exec postgres psql -U postgres -d pdf_platform -c "SELECT 1;"

# Expected: returns 1
```

### 2. Test Redis Connection

```bash
# Direct connection test
docker-compose exec redis redis-cli ping

# Expected: PONG

# Check database selection
docker-compose exec redis redis-cli INFO

# Should show redis_version and other info
```

### 3. Test MinIO Connection

```bash
# Check MinIO readiness
docker-compose exec minio mc ready local

# Expected: Status: UP

# List buckets
docker-compose exec minio mc ls local

# Should show bucket list (or "No buckets yet" if fresh)
```

### 4. Test ClamAV Connection

```bash
# Check ClamAV readiness
docker-compose exec clamav clamscan --version

# Expected: ClamAV <version>
```

### 5. Test API Service

```bash
# Health check endpoint
curl -k https://localhost/health

# Expected: {"status":"ok"} or similar healthy response

# API documentation
curl -k https://localhost/api/docs

# Expected: HTML response with Swagger UI
```

### 6. Test Flower Monitoring

```bash
# Access Flower dashboard
curl -k https://localhost/flower/

# Expected: HTML response (Flower dashboard)

# Check worker is registered
docker-compose exec worker celery -A tasks inspect active

# Expected: worker response with task info
```

## Network and Port Tests

### 1. Test Port Availability

```bash
# Check all ports are listening
netstat -tuln | grep LISTEN

# Should show:
# 80 (nginx http)
# 443 (nginx https)
# 8000 (api)
# 5555 (flower)
# 9000 (minio api)
# 9001 (minio console)
# 5432 (postgres)
# 6379 (redis)
# 3310 (clamav)
```

Or using lsof:
```bash
# For each port
lsof -i :80
lsof -i :443
lsof -i :8000
# etc.
```

### 2. Test Nginx Configuration

```bash
# Check Nginx syntax
docker-compose exec nginx nginx -t

# Expected: successful syntax validation

# Check Nginx is serving
curl -k -I https://localhost/

# Expected: HTTP/1.1 200 OK
```

### 3. Test Rate Limiting

```bash
# Make multiple rapid requests to upload endpoint
for i in {1..15}; do
  curl -k -s https://localhost/api/upload -X OPTIONS
done

# After 10 requests (rate limit), should see:
# HTTP 429 Too Many Requests
```

## Docker Networks and Volumes Test

### 1. Check Network Connectivity

```bash
# Services should be on pdf_network
docker network ls | grep pdf

# Inspect network
docker network inspect pdf_network

# Should list all containers as connected
```

### 2. Check Volumes

```bash
# List volumes
docker volume ls | grep pdf

# Should show:
# pdf_platform_postgres_data
# pdf_platform_redis_data
# pdf_platform_minio_data
# pdf_platform_clamav_data

# Inspect data persistence
docker volume inspect pdf_platform_postgres_data

# Should show mount point
```

## Log Inspection Tests

### 1. Check Service Logs

```bash
# API logs
./scripts/docker-helper.sh logs api

# Worker logs
./scripts/docker-helper.sh logs worker

# Postgres logs
./scripts/docker-helper.sh logs postgres

# Nginx logs
./scripts/docker-helper.sh logs nginx

# All logs
./scripts/docker-helper.sh logs
```

Expected:
- No ERROR level messages
- Services report as ready/started
- Health checks passing

## Environment Variables Test

### 1. Verify .env File

```bash
cat .env | head -20

# Should show all environment variables loaded
```

### 2. Check Variables in Containers

```bash
# Check API environment
docker-compose exec api env | grep POSTGRES_DSN

# Should show PostgreSQL connection string

# Check Worker environment
docker-compose exec worker env | grep CELERY_BROKER_URL

# Should show Celery broker URL
```

## Data Persistence Test

### 1. Write and Verify Data

```bash
# Insert test data into PostgreSQL
docker-compose exec postgres psql -U postgres -d pdf_platform << EOF
CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, data VARCHAR(100));
INSERT INTO test (data) VALUES ('Test data');
SELECT * FROM test;
EOF

# Expected: Should see inserted row
```

### 2. Stop and Restart Services

```bash
# Stop services but keep volumes
docker-compose stop

# Restart services
docker-compose start

# Verify data persisted
docker-compose exec postgres psql -U postgres -d pdf_platform -c "SELECT * FROM test;"

# Expected: Should show same test data
```

## Helper Scripts Test

### 1. Test docker-helper.sh Commands

```bash
# Test all commands
./scripts/docker-helper.sh help
./scripts/docker-helper.sh up
./scripts/docker-helper.sh ps
./scripts/docker-helper.sh health-check
./scripts/docker-helper.sh logs api
./scripts/docker-helper.sh shell api
# (type 'exit' to leave shell)
```

### 2. Test generate-ssl.sh

```bash
# Verify certificate exists
ls -la nginx/ssl/

# Should show:
# server.crt
# server.key

# Verify certificate details
openssl x509 -in nginx/ssl/server.crt -text -noout | head -20
```

## Complete End-to-End Test

### Quick Test Sequence

```bash
#!/bin/bash
echo "=== Starting Complete Test ==="

echo "1. Health checks..."
./scripts/docker-helper.sh health-check

echo "2. Testing database..."
docker-compose exec postgres pg_isready

echo "3. Testing cache..."
docker-compose exec redis redis-cli ping

echo "4. Testing storage..."
docker-compose exec minio mc ready local

echo "5. Testing API..."
curl -k https://localhost/health

echo "6. Testing Celery worker..."
docker-compose exec worker celery -A tasks inspect ping

echo "7. Testing Nginx..."
curl -k -I https://localhost/

echo "=== All Tests Complete ==="
```

Save as `test-all.sh`, make executable, and run:
```bash
chmod +x test-all.sh
./test-all.sh
```

## Troubleshooting Failed Tests

### Service Won't Start

```bash
# Check detailed logs
docker-compose logs <service>

# Common issues:
# - Port already in use
# - Missing environment variables
# - Insufficient memory
# - Failed healthcheck

# Solution: Fix issue and run `docker-compose restart <service>`
```

### Connection Refused

```bash
# Check if service is running
docker-compose ps <service>

# If not running, check logs
docker-compose logs <service>

# Restart service
docker-compose restart <service>
```

### File Permission Issues

```bash
# Check file permissions
ls -la nginx/ssl/
ls -la scripts/

# Fix permissions
chmod 755 scripts/*.sh
chmod 644 nginx/ssl/*
```

### Out of Memory

```bash
# Check available memory
free -h

# Check Docker memory usage
docker stats

# If needed, increase Docker's memory allocation
# or reduce number of workers
```

## Performance Benchmarks

After successful startup, expected:

| Metric | Expected |
|--------|----------|
| Time to all services healthy | 30-60 seconds |
| Health check response time | < 100ms |
| Database query response time | < 50ms |
| API startup time | 5-10 seconds |
| Worker startup time | 5-10 seconds |

## Success Criteria

✅ All tests should pass if:

1. ✓ All 8 services running and healthy
2. ✓ All ports accessible and listening
3. ✓ Database connections working
4. ✓ Cache connections working
5. ✓ Storage connections working
6. ✓ API health check passing
7. ✓ Nginx reverse proxy working
8. ✓ Rate limiting active
9. ✓ SSL/TLS working
10. ✓ Logs show no errors
11. ✓ Volumes persisting data
12. ✓ Helper scripts functional

---

For additional debugging, always check:
1. `docker-compose ps` - Service status
2. `docker-compose logs -f <service>` - Service logs
3. `.env` file - Environment configuration
4. Docker disk space - `docker system df`
5. System resources - `free -h`, `df -h`
