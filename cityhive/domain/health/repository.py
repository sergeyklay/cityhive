"""
Health repository.

Repository for performing health checks against external systems and dependencies.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.infrastructure.logging import get_logger

from .exceptions import DatabaseHealthCheckError, TimeoutError
from .models import ComponentHealth, HealthStatus

logger = get_logger(__name__)


class HealthRepository:
    """Repository for performing health checks against external systems."""

    def __init__(self, db_timeout_seconds: float = 5.0) -> None:
        self.db_timeout_seconds = db_timeout_seconds
        self._logger = get_logger(self.__class__.__name__)

    async def check_database(self, db_session_factory: Any) -> ComponentHealth:
        """
        Check database connectivity and basic functionality with timeout protection.

        Args:
            db_session_factory: Factory function to create database sessions

        Returns:
            ComponentHealth object with database status

        Raises:
            TimeoutError: If database check times out
            DatabaseHealthCheckError: If database check fails
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Wrap the database operation in a timeout
            await asyncio.wait_for(
                self._perform_database_check(db_session_factory),
                timeout=self.db_timeout_seconds,
            )

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._logger.info(
                "Database health check passed",
                response_time_ms=response_time,
                timeout_seconds=self.db_timeout_seconds,
            )

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Connected successfully",
                response_time_ms=response_time,
            )

        except asyncio.TimeoutError as timeout_err:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._logger.warning(
                "Database health check timed out",
                timeout_seconds=self.db_timeout_seconds,
                response_time_ms=response_time,
            )

            raise TimeoutError("database", self.db_timeout_seconds) from timeout_err

        except Exception as e:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._logger.warning(
                "Database health check failed",
                error=str(e),
                error_type=type(e).__name__,
                response_time_ms=response_time,
                timeout_seconds=self.db_timeout_seconds,
            )

            raise DatabaseHealthCheckError(
                f"Connection failed: {type(e).__name__}",
                error=e,
            ) from e

    async def _perform_database_check(self, db_session_factory: Any) -> None:
        """Perform the actual database connectivity check."""
        async with db_session_factory() as session:
            session: AsyncSession
            # Simple query to test connectivity
            await session.execute(text("SELECT 1"))
