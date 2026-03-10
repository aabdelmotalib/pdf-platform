#!/bin/bash
# Generate self-signed SSL certificate for development

set -e

CERT_DIR="/home/abdelmoteleb/pdf-platform/nginx/ssl"
CERT_FILE="$CERT_DIR/server.crt"
KEY_FILE="$CERT_DIR/server.key"

echo "Generating self-signed SSL certificate for development..."

# Create ssl directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_FILE" \
    -keyout "$KEY_FILE" \
    -days 365 \
    -subj "/CN=localhost/O=PDF Platform/C=EG"

echo "✓ SSL certificate generated:"
echo "  Certificate: $CERT_FILE"
echo "  Key: $KEY_FILE"
echo ""
echo "Note: This is a self-signed certificate for development only."
echo "For production, use a proper SSL certificate from a trusted CA."
