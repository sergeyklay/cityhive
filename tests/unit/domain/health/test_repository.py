"""
Unit tests for HealthRepository.

Tests the repository layer responsible for performing health checks
against external systems and dependencies.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from cityhive.domain.health.exceptions import DatabaseHealthCheckError, TimeoutError
from cityhive.domain.health.models import ComponentHealth, HealthStatus
from cityhive.domain.health.repository import HealthRepository


@pytest.fixture
def health_repository() -> HealthRepository:
    """Create a HealthRepository instance for testing."""
    return HealthRepository(db_timeout_seconds=1.0)


@pytest.fixture
def mock_db_session_factory() -> Mock:
    """Create a mock database session factory."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    mock_factory = Mock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    return mock_factory


async def test_check_database_success(
    health_repository: HealthRepository,
    mock_db_session_factory: Mock,
) -> None:
    """Test successful database health check."""
    result = await health_repository.check_database(mock_db_session_factory)

    assert isinstance(result, ComponentHealth)
    assert result.name == "database"
    assert result.status == HealthStatus.HEALTHY
    assert result.message == "Connected successfully"
    assert result.response_time_ms is not None
    assert result.response_time_ms > 0

    mock_session = await mock_db_session_factory.return_value.__aenter__()
    mock_session.execute.assert_called_once()


async def test_check_database_timeout(
    health_repository: HealthRepository,
) -> None:
    """Test database health check timeout."""

    class SlowAsyncContextManager:
        async def __aenter__(self):
            await asyncio.sleep(2.0)
            return AsyncMock()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_factory = Mock()
    mock_factory.return_value = SlowAsyncContextManager()

    with pytest.raises(TimeoutError) as exc_info:
        await health_repository.check_database(mock_factory)

    assert exc_info.value.component == "database"
    assert exc_info.value.timeout_seconds == 1.0


async def test_check_database_connection_error(
    health_repository: HealthRepository,
) -> None:
    """Test database health check with connection error."""

    class FailingAsyncContextManager:
        async def __aenter__(self):
            raise ConnectionError("Database connection failed")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_factory = Mock()
    mock_factory.return_value = FailingAsyncContextManager()

    with pytest.raises(DatabaseHealthCheckError) as exc_info:
        await health_repository.check_database(mock_factory)

    assert "Connection failed: ConnectionError" in exc_info.value.message
    assert isinstance(exc_info.value.original_error, ConnectionError)


async def test_check_database_query_error(
    health_repository: HealthRepository,
    mock_db_session_factory: Mock,
) -> None:
    """Test database health check with query execution error."""
    mock_session = AsyncMock()
    mock_session.execute.side_effect = RuntimeError("Query failed")

    mock_db_session_factory.return_value.__aenter__.return_value = mock_session

    with pytest.raises(DatabaseHealthCheckError) as exc_info:
        await health_repository.check_database(mock_db_session_factory)

    assert "Connection failed: RuntimeError" in exc_info.value.message
    assert isinstance(exc_info.value.original_error, RuntimeError)


@patch("cityhive.domain.health.repository.datetime")
async def test_check_database_response_time_calculation(
    mock_datetime: Mock,
    health_repository: HealthRepository,
    mock_db_session_factory: Mock,
) -> None:
    """Test that response time is calculated correctly."""
    start_time = MagicMock()
    end_time = MagicMock()

    mock_datetime.now.side_effect = [start_time, end_time]

    time_delta = Mock()
    time_delta.total_seconds.return_value = 0.150

    end_time.__sub__ = Mock(return_value=time_delta)

    result = await health_repository.check_database(mock_db_session_factory)

    assert result.response_time_ms == 150.0


async def test_repository_timeout_configuration() -> None:
    """Test that repository respects timeout configuration."""
    custom_timeout = 3.5
    repository = HealthRepository(db_timeout_seconds=custom_timeout)

    assert repository.db_timeout_seconds == custom_timeout
