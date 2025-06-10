"""
Health service.

Business logic for health check operations.
"""

from datetime import datetime, timezone
from typing import Any

from cityhive.infrastructure.logging import get_logger

from .exceptions import DatabaseHealthCheckError, TimeoutError
from .models import ComponentHealth, HealthStatus, SystemHealth
from .repository import HealthRepository

logger = get_logger(__name__)


class HealthService:
    """Service responsible for performing system health checks."""

    def __init__(
        self,
        health_repository: HealthRepository,
        service_name: str = "cityhive",
        version: str | None = None,
    ) -> None:
        self._health_repository = health_repository
        self.service_name = service_name
        self.version = version
        self._logger = get_logger(self.__class__.__name__)

    async def check_liveness(self) -> SystemHealth:
        """
        Liveness probe - checks if the application is running.

        This should be a fast check that only verifies the application
        itself is responsive, not its dependencies.

        Returns:
            SystemHealth object with liveness status
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

        Args:
            db_session_factory: Factory function to create database sessions

        Returns:
            SystemHealth object with readiness status including component details

        Raises:
            DatabaseHealthCheckError: If database check fails (propagated from
                repository)
            TimeoutError: If database check times out (propagated from repository)
        """
        components: list[ComponentHealth] = []
        overall_status = HealthStatus.HEALTHY

        try:
            # Check database connectivity
            db_health = await self._health_repository.check_database(db_session_factory)
            components.append(db_health)

            if db_health.status != HealthStatus.HEALTHY:
                overall_status = HealthStatus.UNHEALTHY

        except (DatabaseHealthCheckError, TimeoutError) as e:
            # Convert exceptions to unhealthy component status
            if isinstance(e, TimeoutError):
                db_health = ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Connection timed out after {e.timeout_seconds}s",
                    metadata={"timeout_seconds": e.timeout_seconds},
                )
            else:
                db_health = ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message=e.message,
                    metadata={
                        "error": str(e.original_error) if e.original_error else None
                    },
                )

            components.append(db_health)
            overall_status = HealthStatus.UNHEALTHY

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            service=self.service_name,
            version=self.version,
            components=components,
        )


class HealthServiceFactory:
    """Factory for creating HealthService instances with proper dependencies."""

    def __init__(
        self,
        service_name: str = "cityhive",
        version: str | None = None,
        db_timeout_seconds: float = 5.0,
    ) -> None:
        self.service_name = service_name
        self.version = version
        self.db_timeout_seconds = db_timeout_seconds

    def create(self) -> HealthService:
        """Create a new HealthService instance with all dependencies."""
        health_repository = HealthRepository(db_timeout_seconds=self.db_timeout_seconds)

        return HealthService(
            health_repository=health_repository,
            service_name=self.service_name,
            version=self.version,
        )
