"""
Health domain models.

Domain entities and value objects for health checking functionality.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class ComponentHealth:
    """Health status of a single component."""

    name: str
    status: HealthStatus
    message: str | None = None
    response_time_ms: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class SystemHealth:
    """Overall system health status."""

    status: HealthStatus
    timestamp: datetime
    service: str
    version: str | None = None
    components: list[ComponentHealth] | None = None

    @property
    def is_healthy(self) -> bool:
        """Check if the system is considered healthy."""
        return self.status == HealthStatus.HEALTHY
