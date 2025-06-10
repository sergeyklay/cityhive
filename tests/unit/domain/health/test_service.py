"""
Unit tests for HealthService.

Tests the service layer responsible for coordinating health check operations
and implementing business logic.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from cityhive.domain.health.exceptions import DatabaseHealthCheckError, TimeoutError
from cityhive.domain.health.models import ComponentHealth, HealthStatus, SystemHealth
from cityhive.domain.health.repository import HealthRepository
from cityhive.domain.health.service import HealthService, HealthServiceFactory


@pytest.fixture
def mock_health_repository() -> Mock:
    """Create a mock health repository."""
    return Mock(spec=HealthRepository)


@pytest.fixture
def health_service(mock_health_repository: Mock) -> HealthService:
    """Create a HealthService instance for testing."""
    return HealthService(
        health_repository=mock_health_repository,
        service_name="test-service",
        version="1.0.0",
    )


async def test_check_liveness_success(health_service: HealthService) -> None:
    """Test successful liveness check."""
    result = await health_service.check_liveness()

    assert isinstance(result, SystemHealth)
    assert result.status == HealthStatus.HEALTHY
    assert result.service == "test-service"
    assert result.version == "1.0.0"
    assert result.components is None
    assert result.is_healthy is True
    assert isinstance(result.timestamp, datetime)


async def test_check_readiness_success(
    health_service: HealthService,
    mock_health_repository: Mock,
) -> None:
    """Test successful readiness check."""
    mock_db_session_factory = Mock()

    healthy_component = ComponentHealth(
        name="database",
        status=HealthStatus.HEALTHY,
        message="Connected successfully",
        response_time_ms=50.0,
    )

    mock_health_repository.check_database = AsyncMock(return_value=healthy_component)

    result = await health_service.check_readiness(mock_db_session_factory)

    assert isinstance(result, SystemHealth)
    assert result.status == HealthStatus.HEALTHY
    assert result.service == "test-service"
    assert result.version == "1.0.0"
    assert result.is_healthy is True

    assert result.components is not None
    assert len(result.components) == 1
    assert result.components[0] == healthy_component

    mock_health_repository.check_database.assert_called_once_with(
        mock_db_session_factory
    )


async def test_check_readiness_database_unhealthy(
    health_service: HealthService,
    mock_health_repository: Mock,
) -> None:
    """Test readiness check with unhealthy database."""
    mock_db_session_factory = Mock()

    unhealthy_component = ComponentHealth(
        name="database",
        status=HealthStatus.UNHEALTHY,
        message="Connection failed",
        response_time_ms=100.0,
    )

    mock_health_repository.check_database = AsyncMock(return_value=unhealthy_component)

    result = await health_service.check_readiness(mock_db_session_factory)

    assert result.status == HealthStatus.UNHEALTHY
    assert result.is_healthy is False
    assert result.components is not None
    assert len(result.components) == 1
    assert result.components[0] == unhealthy_component


async def test_check_readiness_database_timeout_exception(
    health_service: HealthService,
    mock_health_repository: Mock,
) -> None:
    """Test readiness check with database timeout exception."""
    mock_db_session_factory = Mock()
    timeout_error = TimeoutError("database", 5.0)

    mock_health_repository.check_database = AsyncMock(side_effect=timeout_error)

    result = await health_service.check_readiness(mock_db_session_factory)

    assert result.status == HealthStatus.UNHEALTHY
    assert result.is_healthy is False
    assert result.components is not None
    assert len(result.components) == 1

    db_component = result.components[0]
    assert db_component.name == "database"
    assert db_component.status == HealthStatus.UNHEALTHY
    assert db_component.message is not None
    assert "Connection timed out after 5.0s" in db_component.message
    assert db_component.metadata == {"timeout_seconds": 5.0}


async def test_check_readiness_database_check_exception(
    health_service: HealthService,
    mock_health_repository: Mock,
) -> None:
    """Test readiness check with database check exception."""
    mock_db_session_factory = Mock()
    original_error = ConnectionError("Database unavailable")
    db_error = DatabaseHealthCheckError(
        "Connection failed: ConnectionError", original_error
    )

    mock_health_repository.check_database = AsyncMock(side_effect=db_error)

    result = await health_service.check_readiness(mock_db_session_factory)

    assert result.status == HealthStatus.UNHEALTHY
    assert result.is_healthy is False
    assert result.components is not None
    assert len(result.components) == 1

    db_component = result.components[0]
    assert db_component.name == "database"
    assert db_component.status == HealthStatus.UNHEALTHY
    assert db_component.message == "Connection failed: ConnectionError"
    assert db_component.metadata == {"error": "Database unavailable"}


async def test_check_readiness_database_check_exception_no_original_error(
    health_service: HealthService,
    mock_health_repository: Mock,
) -> None:
    """Test readiness check with database check exception without original error."""
    mock_db_session_factory = Mock()
    db_error = DatabaseHealthCheckError("Connection failed", None)

    mock_health_repository.check_database = AsyncMock(side_effect=db_error)

    result = await health_service.check_readiness(mock_db_session_factory)

    assert result.status == HealthStatus.UNHEALTHY
    assert result.components is not None
    db_component = result.components[0]
    assert db_component.metadata == {"error": None}


def test_service_initialization(mock_health_repository: Mock) -> None:
    """Test service initialization with custom parameters."""
    service = HealthService(
        health_repository=mock_health_repository,
        service_name="custom-service",
        version="2.1.0",
    )

    assert service.service_name == "custom-service"
    assert service.version == "2.1.0"
    assert service._health_repository == mock_health_repository


def test_service_initialization_defaults(mock_health_repository: Mock) -> None:
    """Test service initialization with default parameters."""
    service = HealthService(health_repository=mock_health_repository)

    assert service.service_name == "cityhive"
    assert service.version is None


def test_factory_initialization() -> None:
    """Test factory initialization with custom parameters."""
    factory = HealthServiceFactory(
        service_name="test-app",
        version="3.0.0",
        db_timeout_seconds=10.0,
    )

    assert factory.service_name == "test-app"
    assert factory.version == "3.0.0"
    assert factory.db_timeout_seconds == 10.0


def test_factory_initialization_defaults() -> None:
    """Test factory initialization with default parameters."""
    factory = HealthServiceFactory()

    assert factory.service_name == "cityhive"
    assert factory.version is None
    assert factory.db_timeout_seconds == 5.0


def test_create_service() -> None:
    """Test factory creates service with proper configuration."""
    factory = HealthServiceFactory(
        service_name="factory-test",
        version="1.5.0",
        db_timeout_seconds=8.0,
    )

    service = factory.create()

    assert isinstance(service, HealthService)
    assert service.service_name == "factory-test"
    assert service.version == "1.5.0"

    assert isinstance(service._health_repository, HealthRepository)
    assert service._health_repository.db_timeout_seconds == 8.0
