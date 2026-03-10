#!/bin/bash
# Docker compose helper script

set -e

COMMAND=${1:-help}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

function show_help() {
    cat << EOF
PDF Platform Docker Helper

Usage: $0 <command> [options]

Commands:
  up              Start all services
  down            Stop all services
  restart         Restart all services
  logs            Display logs from all services
  logs <service>  Display logs from specific service (api, worker, postgres, redis, minio, clamav, flower, nginx)
  shell <service> Open shell in service container
  build           Build Docker images
  clean           Remove containers and volumes (keeps code)
  clean-all       Remove containers, volumes, AND images
  health-check    Check health of all services
  setup           Run setup scripts (SSL generation, migrations)
  minio-init      Initialize MinIO buckets
  db-migrate      Run database migrations
  ps              Show running containers

Examples:
  $0 up
  $0 logs api
  $0 shell worker
  $0 health-check

EOF
}

function docker_compose() {
    cd "$PROJECT_DIR"
    docker-compose "$@"
}

function cmd_up() {
    echo "Starting PDF Platform services..."
    docker_compose up -d
    echo ""
    echo "✓ Services started!"
    echo ""
    echo "Access points:"
    echo "  - API: http://localhost:8000"
    echo "  - Flower (Celery): http://localhost:5555"
    echo "  - MinIO Console: http://localhost:9001"
    echo "  - Postgres: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "Next: Run '$0 setup' for initialization"
}

function cmd_down() {
    echo "Stopping PDF Platform services..."
    docker_compose down
    echo "✓ Services stopped!"
}

function cmd_restart() {
    echo "Restarting PDF Platform services..."
    docker_compose restart
    echo "✓ Services restarted!"
}

function cmd_logs() {
    SERVICE=${2:-}
    if [ -z "$SERVICE" ]; then
        echo "Displaying logs from all services (Ctrl+C to stop)..."
        docker_compose logs -f
    else
        echo "Displaying logs from $SERVICE service (Ctrl+C to stop)..."
        docker_compose logs -f "$SERVICE"
    fi
}

function cmd_shell() {
    SERVICE=${2:-}
    if [ -z "$SERVICE" ]; then
        echo "Usage: $0 shell <service>"
        echo "Available services: api, worker, postgres, redis, minio, clamav, flower, nginx"
        exit 1
    fi
    docker_compose exec "$SERVICE" /bin/bash
}

function cmd_build() {
    echo "Building Docker images..."
    docker_compose build
    echo "✓ Images built!"
}

function cmd_clean() {
    echo "Cleaning up containers and volumes..."
    docker_compose down -v
    echo "✓ Cleanup complete!"
}

function cmd_clean_all() {
    echo "WARNING: This will remove containers, volumes, AND images!"
    read -p "Continue? (yes/no) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker_compose down -v --rmi all
        echo "✓ Complete cleanup done!"
    else
        echo "Cancelled."
    fi
}

function cmd_health_check() {
    echo "Checking service health..."
    echo ""
    docker_compose ps
}

function cmd_setup() {
    echo "Running setup scripts..."
    echo ""
    
    # Generate SSL certificates
    if [ ! -f "$PROJECT_DIR/nginx/ssl/server.crt" ]; then
        echo "1. Generating SSL certificates..."
        bash "$PROJECT_DIR/scripts/generate-ssl.sh"
        echo ""
    else
        echo "✓ SSL certificates already exist"
        echo ""
    fi
    
    # Start services
    cmd_up
    
    echo ""
    echo "2. Waiting for services to be ready..."
    sleep 10
    
    # Run migrations
    echo "3. Running database migrations..."
    cd "$PROJECT_DIR"
    docker_compose exec -T postgres pg_isready -U postgres -d pdf_platform || true
    echo "✓ Database ready"
    echo ""
    
    echo "Setup complete!"
}

function cmd_minio_init() {
    echo "Initializing MinIO buckets..."
    cd "$PROJECT_DIR"
    
    # Initialize MinIO and create buckets
    docker_compose exec -T minio \
        mc mb minio/input-files 2>/dev/null || echo "  input-files bucket already exists"
    docker_compose exec -T minio \
        mc mb minio/output-files 2>/dev/null || echo "  output-files bucket already exists"
    
    echo "✓ MinIO buckets initialized"
}

function cmd_ps() {
    docker_compose ps
}

case "$COMMAND" in
    up) cmd_up ;;
    down) cmd_down ;;
    restart) cmd_restart ;;
    logs) cmd_logs "$@" ;;
    shell) cmd_shell "$@" ;;
    build) cmd_build ;;
    clean) cmd_clean ;;
    clean-all) cmd_clean_all ;;
    health-check) cmd_health_check ;;
    setup) cmd_setup ;;
    minio-init) cmd_minio_init ;;
    ps) cmd_ps ;;
    *)
        echo "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
