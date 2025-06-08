#!/bin/bash

set -euo pipefail

# Function to handle cleanup on exit
cleanup() {
    echo "Shutting down gracefully..."
    # Kill any background processes
    jobs -p | xargs -r kill
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT

# Function to wait for database using environment variables
wait_for_db() {
    echo "Waiting for database connection..."

    # Extract database connection details from DATABASE_URI
    local db_connection_info
    db_connection_info=$(python /app/scripts/db_connection_info.py)

    if [ $? -ne 0 ]; then
        return 1
    fi

    # Parse the connection info
    read -r DB_HOST DB_PORT DB_USER DB_NAME <<< "$db_connection_info"

    echo "Checking database connection to $DB_HOST:$DB_PORT (database: $DB_NAME, user: $DB_USER)..."

    # Use pg_isready for PostgreSQL connection check
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            echo "Database connection successful"
            return 0
        fi

        echo "Attempt $((attempt + 1))/$max_attempts: Database not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "Database connection failed after $max_attempts attempts"
    return 1
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    if command -v alembic >/dev/null 2>&1; then
        alembic upgrade head
    else
        echo "Alembic not found, skipping migrations"
    fi
}

# Function to start the application
start_app() {
    echo "Starting CityHive application..."
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
