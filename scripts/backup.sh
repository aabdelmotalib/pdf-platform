#!/bin/bash
# PDF Platform Database Backup Script
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="backup_${DATE}.sql.gz"

# Ensure script runs from project root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

echo "💾 Starting database backup..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres pdf_platform | gzip > /tmp/$FILENAME

# Upload to MinIO backups bucket (assuming 'backups' bucket exists)
echo "📤 Uploading to MinIO..."
# Using the minio alias 'local' which should be configured in mc
# If 'mc' is not installed on host, we can use a dockerized version or 
# assume the user has configured the environment.
# For simplicity, we use the 'minio' container's own 'mc' client if available
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T minio mc cp /tmp/$FILENAME local/backups/$FILENAME

# Delete backups older than 7 days (168h)
echo "🧹 Cleaning old backups..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T minio mc rm --recursive --force --older-than 168h local/backups/

rm /tmp/$FILENAME
echo "✅ Backup complete: $FILENAME"
