"""
Health domain exceptions.

Business-layer exceptions for health check operations.
"""


class HealthCheckError(Exception):
    """Base exception for health check related errors."""

    pass


class DatabaseHealthCheckError(HealthCheckError):
    """Raised when database health check fails."""

    def __init__(self, message: str, error: Exception | None = None) -> None:
        self.message = message
        self.original_error = error
        super().__init__(message)


class HealthCheckTimeoutError(HealthCheckError):
    """Raised when health check operations timeout."""

    def __init__(self, component: str, timeout_seconds: float) -> None:
        self.component = component
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{component} health check timed out after {timeout_seconds}s")
