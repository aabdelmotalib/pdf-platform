#!/bin/bash
set -e
DOMAIN=$1
if [ -z "$DOMAIN" ]; then echo "Usage: $0 yourdomain.com"; exit 1; fi

# Install certbot
apt-get update
apt-get install -y certbot

# Stop nginx to free port 80 for certbot standalone
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx

# Request certificate
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

# Start nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml start nginx

# Add renewal cron
echo "0 3 * * * root certbot renew --quiet --deploy-hook 'docker compose -f /root/pdf-platform/docker-compose.prod.yml restart nginx'" > /etc/cron.d/certbot-renew

echo "✅ SSL certificate installed for $DOMAIN"
