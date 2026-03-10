#!/bin/bash
# Initialize the PDF Platform project

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "================================"
echo "PDF Platform - Project Setup"
echo "================================"
echo ""

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$PROJECT_DIR/scripts/"*.sh
echo "✓ Scripts are executable"
echo ""

# Generate SSL certificates
echo "Generating SSL certificates for development..."
bash "$PROJECT_DIR/scripts/generate-ssl.sh"
echo ""

# Build images
echo "Building Docker images..."
cd "$PROJECT_DIR"
docker-compose build --no-cache
echo "✓ Images built successfully"
echo ""

echo "================================"
echo "Setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Run: ./scripts/docker-helper.sh up"
echo "2. Wait for services to start (30-60 seconds)"
echo "3. Check status: ./scripts/docker-helper.sh health-check"
echo ""
echo "After starting, access:"
echo "  - API Documentation: https://localhost/api/docs"
echo "  - Flower Monitoring: https://localhost/flower"
echo "  - MinIO Console: https://localhost:9001"
echo ""
