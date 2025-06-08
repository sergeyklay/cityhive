"""
Unit tests for health check service.

Tests the centralized health check logic and domain models.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.services.health import (
    ComponentHealth,
    HealthCheckService,
    HealthStatus,
    SystemHealth,
)


class MockAsyncContextManager:
    """Mock async context manager for database sessions."""

    def __init__(self, session_mock):
        self.session_mock = session_mock

    async def __aenter__(self):
        return self.session_mock

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


def test_health_status_has_expected_values():
    """Test that health status enumeration has expected values."""
    assert HealthStatus.HEALTHY == "healthy"
    assert HealthStatus.UNHEALTHY == "unhealthy"
    assert HealthStatus.DEGRADED == "degraded"


def test_component_health_creation_with_all_fields():
    """Test creating component health instance with all fields."""
    component = ComponentHealth(
        name="database",
        status=HealthStatus.HEALTHY,
        message="Connected successfully",
        response_time_ms=45.2,
        metadata={"version": "14.0"},
    )

    assert component.name == "database"
    assert component.status == HealthStatus.HEALTHY
    assert component.message == "Connected successfully"
    assert component.response_time_ms == 45.2
    assert component.metadata == {"version": "14.0"}


def test_component_health_creation_with_minimal_fields():
    """Test creating component health instance with minimal required fields."""
    component = ComponentHealth(
        name="database",
        status=HealthStatus.UNHEALTHY,
    )

    assert component.name == "database"
    assert component.status == HealthStatus.UNHEALTHY
    assert component.message is None
    assert component.response_time_ms is None
    assert component.metadata is None


def test_system_health_creation_with_components():
    """Test creating system health instance with components."""
    timestamp = datetime.now(timezone.utc)
    components = [
        ComponentHealth(name="database", status=HealthStatus.HEALTHY),
    ]

    health = SystemHealth(
        status=HealthStatus.HEALTHY,
        timestamp=timestamp,
        service="cityhive",
        version="1.0.0",
        components=components,
    )

    assert health.status == HealthStatus.HEALTHY
    assert health.timestamp == timestamp
    assert health.service == "cityhive"
    assert health.version == "1.0.0"
    assert health.components == components


@pytest.mark.parametrize(
    "status,expected_healthy",
    [
        (HealthStatus.HEALTHY, True),
        (HealthStatus.UNHEALTHY, False),
        (HealthStatus.DEGRADED, False),
    ],
)
def test_system_health_is_healthy_property(status, expected_healthy):
    """Test system health is_healthy property for different statuses."""
    timestamp = datetime.now(timezone.utc)
    health = SystemHealth(
        status=status,
        timestamp=timestamp,
        service="cityhive",
    )
    assert health.is_healthy is expected_healthy


def test_health_check_service_initialization_with_defaults():
    """Test health check service initialization with default values."""
    service = HealthCheckService()
    assert service.service_name == "cityhive"
    assert service.version is None


def test_health_check_service_initialization_with_custom_values():
    """Test health check service initialization with custom values."""
    service = HealthCheckService(service_name="test-service", version="2.0.0")
    assert service.service_name == "test-service"
    assert service.version == "2.0.0"


@pytest.mark.asyncio
async def test_check_liveness_returns_healthy_status():
    """Test that liveness check always returns healthy status."""
    service = HealthCheckService(service_name="test-service", version="1.0.0")
    health = await service.check_liveness()

    assert health.status == HealthStatus.HEALTHY
    assert health.service == "test-service"
    assert health.version == "1.0.0"
    assert health.components is None
    assert health.is_healthy is True
    assert isinstance(health.timestamp, datetime)


@pytest.mark.asyncio
async def test_check_readiness_with_healthy_database():
    """Test readiness check returns healthy when database is available."""
    mock_session = AsyncMock(spec=AsyncSession)

    def mock_session_factory():
        return MockAsyncContextManager(mock_session)

    service = HealthCheckService(service_name="test-service", version="1.0.0")
    health = await service.check_readiness(mock_session_factory)

    assert health.status == HealthStatus.HEALTHY
    assert health.service == "test-service"
    assert health.version == "1.0.0"
    assert health.is_healthy is True
    assert health.components is not None
    assert len(health.components) == 1

    db_component = health.components[0]
    assert db_component.name == "database"
    assert db_component.status == HealthStatus.HEALTHY
    assert db_component.message == "Connected successfully"
    assert isinstance(db_component.response_time_ms, float)


@pytest.mark.asyncio
async def test_check_readiness_with_database_connection_failure():
    """Test readiness check returns unhealthy when database connection fails."""

    def mock_session_factory():
        raise Exception("Connection failed")

    service = HealthCheckService(service_name="test-service", version="1.0.0")
    health = await service.check_readiness(mock_session_factory)

    assert health.status == HealthStatus.UNHEALTHY
    assert health.service == "test-service"
    assert health.version == "1.0.0"
    assert health.is_healthy is False
    assert health.components is not None
    assert len(health.components) == 1

    db_component = health.components[0]
    assert db_component.name == "database"
    assert db_component.status == HealthStatus.UNHEALTHY
    assert db_component.message is not None
    assert "Connection failed" in db_component.message
    assert isinstance(db_component.response_time_ms, float)


@pytest.mark.asyncio
async def test_check_readiness_with_database_query_failure():
    """Test readiness check handles database query execution failures."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.side_effect = Exception("Query failed")

    def mock_session_factory():
        return MockAsyncContextManager(mock_session)

    service = HealthCheckService()
    health = await service.check_readiness(mock_session_factory)

    assert health.status == HealthStatus.UNHEALTHY
    assert health.components is not None
    assert len(health.components) == 1

    db_component = health.components[0]
    assert db_component.name == "database"
    assert db_component.status == HealthStatus.UNHEALTHY
    assert db_component.message is not None
    assert "Exception" in db_component.message
    assert db_component.metadata is not None
    assert "Query failed" in db_component.metadata["error"]
    assert isinstance(db_component.response_time_ms, float)


@pytest.mark.asyncio
async def test_database_check_measures_response_time():
    """Test that database health check measures and reports response time."""
    mock_session = AsyncMock(spec=AsyncSession)

    def mock_session_factory():
        return MockAsyncContextManager(mock_session)

    service = HealthCheckService()
    health = await service.check_readiness(mock_session_factory)

    assert health.components is not None
    db_component = health.components[0]
    assert db_component.response_time_ms is not None
    assert db_component.response_time_ms >= 0
