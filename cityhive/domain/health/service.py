"""
Health service.

Business logic for health check operations including liveness and readiness checks.
"""

from datetime import datetime, timezone
from typing import Any

from cityhive.infrastructure.logging import get_logger

from .exceptions import DatabaseHealthCheckError, HealthCheckTimeoutError
from .models import ComponentHealth, HealthStatus, SystemHealth
from .repository import HealthRepository

logger = get_logger(__name__)


class HealthService:
    """Service for coordinating health check operations."""

    def __init__(
        self,
        health_repository: HealthRepository,
        service_name: str = "cityhive",
        version: str | None = None,
    ) -> None:
        self.service_name = service_name
        self.version = version
        self._health_repository = health_repository
        self._logger = get_logger(self.__class__.__name__)

    async def check_liveness(self) -> SystemHealth:
        """
        Perform liveness check - basic service health without external dependencies.

        Returns:
            SystemHealth indicating if the service is alive and running
        """
        self._logger.info("Performing liveness check")

        return SystemHealth(
            service=self.service_name,
            version=self.version,
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc),
            components=None,
        )

    async def check_readiness(self, db_session_factory: Any) -> SystemHealth:
        """
        Perform readiness check - service health including external dependencies.

        Args:
            db_session_factory: Factory function to create database sessions

        Returns:
            SystemHealth indicating if the service is ready to handle requests

        Raises:
            HealthCheckTimeoutError: If database check times out (propagated
                from repository)
            DatabaseHealthCheckError: If database check fails (propagated
                from repository)
        """
        self._logger.info("Performing readiness check")

        components = []

        try:
            db_health = await self._health_repository.check_database(db_session_factory)
            components.append(db_health)

        except (DatabaseHealthCheckError, HealthCheckTimeoutError) as e:
            self._logger.warning("Database health check failed", error=str(e))
            if isinstance(e, HealthCheckTimeoutError):
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

        overall_status = (
            HealthStatus.HEALTHY
            if all(component.status == HealthStatus.HEALTHY for component in components)
            else HealthStatus.UNHEALTHY
        )

        self._logger.info(
            "Readiness check completed",
            status=overall_status.value,
            components_count=len(components),
        )

        return SystemHealth(
            service=self.service_name,
            version=self.version,
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            components=components,
        )


class HealthServiceFactory:
    """Factory for creating HealthService instances."""

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
        """Create a HealthService instance with configured dependencies."""
        health_repository = HealthRepository(db_timeout_seconds=self.db_timeout_seconds)
        return HealthService(
            health_repository=health_repository,
            service_name=self.service_name,
            version=self.version,
        )
