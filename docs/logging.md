# Logging

CityHive uses [structlog](https://www.structlog.org/) for structured logging with JSON output to stdout. This provides consistent, machine-readable logs that are ideal for production environments and log aggregation systems.

## Overview

The logging system is configured at the infrastructure level (`cityhive/infrastructure/logging.py`) and provides:

- **JSON-only output** to stdout for 12-factor app compliance
- **Structured logging** with key-value pairs instead of string formatting
- **Request-scoped context** using contextvars
- **Exception handling** with structured tracebacks
- **Performance optimized** with caching and filtering

## Quick Start

### Basic Usage

```python
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Structured logging with key-value pairs
logger.info("User created", user_id=12345, email="user@example.com")
logger.warning("Rate limit exceeded", user_id=12345, limit=100, current=105)
logger.error("Database connection failed", error="timeout", retry_count=3)
```

### Context Binding

```python
# Bind context to logger for related operations
user_logger = logger.bind(user_id=12345, session_id="abc-123")

user_logger.info("Login attempt", success=True)
user_logger.info("Page viewed", page="/dashboard")
user_logger.info("Logout", duration_seconds=1800)
```

### Exception Handling

```python
try:
    risky_operation()
except Exception as e:
    logger.exception(
        "Operation failed",
        operation="data_processing",
        error_type=type(e).__name__,
        user_id=user_id,
    )
```

## Configuration

### Application Setup

The logging system is automatically configured when the application starts:

```python
# In cityhive/app/app.py
from cityhive.infrastructure.logging import setup_logging

def main() -> None:
    # Setup structured logging with JSON output
    setup_logging(force_json=True)
    # ... rest of application startup
```

### Environment-Based Configuration

The system can auto-detect the environment:

```python
# Force JSON output (production)
setup_logging(force_json=True)

# Auto-detect: JSON for non-TTY, pretty print for terminal
setup_logging(force_json=False)
```

## Request Context

The logging middleware automatically adds request-scoped context to all log messages within a request:

```python
# Automatically added by logging_middleware:
# - request_id: Unique UUID for each request
# - method: HTTP method (GET, POST, etc.)
# - path: Request path
# - remote: Client IP address
# - user_agent: Client user agent
```

### Manual Context Management

```python
from cityhive.infrastructure.logging import (
    bind_request_context,
    clear_request_context,
)

# Clear existing context
clear_request_context()

# Bind request-specific data
bind_request_context(
    request_id="req-12345",
    user_id=67890,
    operation="api_call",
)

# All subsequent log messages will include this context
logger.info("Processing started")  # Includes request_id, user_id, operation
```

## Log Output Format

All logs are output as JSON to stdout with the following structure:

```json
{
  "event": "User created successfully",
  "level": "info",
  "timestamp": "2025-06-08T12:00:00.000000Z",
  "logger": "cityhive.domain.users",
  "filename": "users.py",
  "func_name": "create_user",
  "lineno": 42,
  "user_id": 12345,
  "email": "user@example.com",
  "request_id": "req-abc-123"
}
```

### Standard Fields

Every log entry includes:

- `event`: The log message
- `level`: Log level (info, warning, error, etc.)
- `timestamp`: ISO 8601 timestamp in UTC
- `logger`: Logger name (usually module name)
- `filename`: Source file name
- `func_name`: Function name where log was called
- `lineno`: Line number where log was called

### Custom Fields

Add any additional structured data as keyword arguments:

```python
logger.info(
    "Database query executed",
    query_type="SELECT",
    table="users",
    duration_ms=45.2,
    rows_returned=150,
)
```

## Best Practices

### 1. Use Structured Data

❌ **Don't use string formatting:**
```python
logger.info(f"User {user_id} created with email {email}")
```

✅ **Do use structured fields:**
```python
logger.info("User created", user_id=user_id, email=email)
```

### 2. Consistent Field Names

Use consistent field names across your application:

```python
# Good: consistent naming
logger.info("Request started", user_id=123, request_id="req-456")
logger.info("Request completed", user_id=123, request_id="req-456")

# Bad: inconsistent naming
logger.info("Request started", userId=123, reqId="req-456")
logger.info("Request completed", user_id=123, request_id="req-456")
```

### 3. Appropriate Log Levels

- `debug`: Detailed diagnostic information
- `info`: General information about application flow
- `warning`: Something unexpected but not an error
- `error`: Error conditions that should be investigated
- `critical`: Serious errors that may cause the application to stop

### 4. Context Binding for Related Operations

```python
# Bind context for a series of related operations
transaction_logger = logger.bind(
    transaction_id="tx-789",
    user_id=12345,
    amount=100.50,
)

transaction_logger.info("Transaction started")
transaction_logger.info("Payment processed")
transaction_logger.info("Transaction completed", status="success")
```

### 5. Exception Logging

Always use `logger.exception()` for exceptions to get structured tracebacks:

```python
try:
    process_payment(amount)
except PaymentError as e:
    logger.exception(
        "Payment processing failed",
        amount=amount,
        error_code=e.code,
        payment_method="credit_card",
    )
```

## Middleware Integration

The logging middleware (`cityhive/app/middlewares.py`) automatically:

1. **Generates unique request IDs** for tracing requests
2. **Binds request context** (method, path, remote IP, user agent)
3. **Logs request start and completion** with timing information
4. **Handles exceptions** with structured error logging
5. **Cleans up context** after request completion

Example middleware output:

```json
{"event": "Request started", "method": "POST", "path": "/api/users", "remote": "192.168.1.100", "request_id": "req-abc-123", ...}
{"event": "Request completed", "method": "POST", "path": "/api/users", "status": 201, "duration_seconds": 0.045, "request_id": "req-abc-123", ...}
```

## Performance Considerations

The logging system is optimized for production use:

- **Logger caching**: Loggers are cached on first use
- **Level filtering**: Log messages below the configured level are filtered early
- **Efficient JSON serialization**: Uses optimized JSON rendering
- **Context variables**: Efficient request-scoped context using Python's contextvars

## Integration with External Systems

The JSON output format is compatible with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd/Fluent Bit**
- **Datadog**
- **New Relic**
- **CloudWatch Logs**
- **Google Cloud Logging**

## Testing

To test the logging system, run the demonstration script:

```bash
uv run python scripts/test_logging.py
```

This will show examples of:
- Basic structured logging
- Context binding
- Request context simulation
- Exception handling
