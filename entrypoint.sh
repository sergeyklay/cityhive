#!/bin/bash

set -euo pipefail

# Function to handle cleanup on exit
cleanup() {
    # Kill any background processes
    jobs -p | xargs -r kill
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT

# Function to wait for database using centralized health check
wait_for_db() {
    python /app/scripts/wait_for_db.py
}

# Function to run database migrations
run_migrations() {
    if command -v alembic >/dev/null 2>&1; then
        alembic upgrade head
    fi
}

# Function to start the application
start_app() {
    exec python -m cityhive.app
}

# Main execution
case "${1:-start}" in
    start)
        wait_for_db
        run_migrations
        start_app
        ;;
    migrate)
        wait_for_db
        run_migrations
        ;;
    shell)
        exec python
        ;;
    *)
        echo "Usage: $0 {start|migrate|shell}"
        echo "  start   - Start the application (default)"
        echo "  migrate - Run database migrations only"
        echo "  shell   - Start Python shell"
        exit 1
        ;;
esac
