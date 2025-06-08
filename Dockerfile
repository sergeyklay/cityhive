## Base Image
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

## Builder stage
FROM base AS builder

ENV UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv \
    && uv sync \
    --locked \
    --no-install-project \
    --compile-bytecode \
    --no-editable \
    --no-group dev \
    --no-group testing \
    --active

## Production stage
FROM base AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:/opt/venv/lib/python3.12" \
    DOCKER=true

WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Prepare entrypoint script
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Health check using curl to hit the health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
