"""
Health domain package.

Contains all health check related domain logic including models, service,
and exceptions.
"""

from .exceptions import (
    DatabaseHealthCheckError,
    HealthCheckError,
    HealthCheckTimeoutError,
)
from .models import ComponentHealth, HealthStatus, SystemHealth
from .service import HealthService, HealthServiceFactory

__all__ = [
    "HealthCheckError",
    "DatabaseHealthCheckError",
    "HealthCheckTimeoutError",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    "HealthService",
    "HealthServiceFactory",
]
