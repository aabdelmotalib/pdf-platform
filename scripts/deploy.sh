#!/bin/bash
set -e

echo "🚀 === PDF Platform Deployment ==="
# Ensure we are in the project root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build frontend
echo "🏗️ Building frontend..."
cd frontend
npm install
# VITE_API_URL=https://dblockhub.com/api npm run build
npm run build -- --mode production
cd ..

# Build and restart API and Worker only
echo "📦 Building images..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build api worker

echo "♻️ Restarting API..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api

echo "⚙️ Running migrations..."
sleep 5
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api alembic upgrade head

echo "♻️ Restarting Worker..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps worker

echo "🩺 Checking health..."
sleep 5
# Note: Using localhost:8000 because nginx might not be up or configured yet
curl -f http://localhost:8000/health && echo " ✅ API healthy" || echo " ❌ API unhealthy"

echo "🗄️ Initializing MinIO..."
# Wait for Minio to be ready
sleep 5
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T minio mc alias set local http://localhost:9000 pdf_admin cf3b6598fe6af28047f53ace639d9f7e || true
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T minio mc mb local/backups || true
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T minio mc mb local/uploads || true

echo "✨ === Deployment complete ==="
