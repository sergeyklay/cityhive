"""
Health check domain service.

Centralizes all health check logic following clean architecture principles.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


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


class HealthCheckService:
    """Service responsible for performing system health checks."""

    def __init__(self, service_name: str = "cityhive", version: str | None = None):
        self.service_name = service_name
        self.version = version
        self._logger = get_logger(self.__class__.__name__)

    async def check_liveness(self) -> SystemHealth:
        """
        Liveness probe - checks if the application is running.

        This should be a fast check that only verifies the application
        itself is responsive, not its dependencies.
        """
        return SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc),
            service=self.service_name,
            version=self.version,
        )

    async def check_readiness(self, db_session_factory: Any) -> SystemHealth:
        """
        Readiness probe - checks if the application is ready to serve traffic.

        This includes checking all critical dependencies like database.
        """
        components: list[ComponentHealth] = []
        overall_status = HealthStatus.HEALTHY

        # Check database connectivity
        db_health = await self._check_database(db_session_factory)
        components.append(db_health)

        if db_health.status != HealthStatus.HEALTHY:
            overall_status = HealthStatus.UNHEALTHY

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            service=self.service_name,
            version=self.version,
            components=components,
        )

    async def _check_database(self, db_session_factory: Any) -> ComponentHealth:
        """Check database connectivity and basic functionality."""
        start_time = datetime.now(timezone.utc)

        try:
            async with db_session_factory() as session:
                session: AsyncSession
                # Simple query to test connectivity
                await session.execute(text("SELECT 1"))

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._logger.info(
                "Database health check passed",
                response_time_ms=response_time,
            )

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Connected successfully",
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._logger.warning(
                "Database health check failed",
                error=str(e),
                error_type=type(e).__name__,
                response_time_ms=response_time,
            )

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {type(e).__name__}",
                response_time_ms=response_time,
                metadata={"error": str(e)},
            )
