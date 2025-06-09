## Base Image
FROM public.ecr.aws/docker/library/python:3.12-slim AS base

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

# Copy uv from the official distroless image
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    VIRTUAL_ENV=/opt/venv

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv \
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

# Add standard OCI labels
LABEL org.opencontainers.image.source="https://github.com/sergeyklay/cityhive" \
    org.opencontainers.image.description="Experimental aiohttp microservice for urban beehive management and technology exploration." \
    org.opencontainers.image.licenses=MIT

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && apt-get clean \
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

# Health check using liveness probe endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health/live || exit 1

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
