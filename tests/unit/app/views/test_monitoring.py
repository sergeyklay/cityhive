"""
Unit tests for monitoring views.

Tests the web layer handlers for health check endpoints.
"""

import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from cityhive.app.views.monitoring import liveness_check, readiness_check
from cityhive.domain.health.models import ComponentHealth, HealthStatus, SystemHealth
from cityhive.domain.health.service import HealthService, HealthServiceFactory
from cityhive.infrastructure.typedefs import db_key, health_service_factory_key


class TestLivenessCheck:
    """Test cases for liveness check endpoint."""

    @pytest.fixture
    def mock_health_service(self) -> Mock:
        """Create a mock health service."""
        return Mock(spec=HealthService)

    @pytest.fixture
    def mock_health_service_factory(self, mock_health_service: Mock) -> Mock:
        """Create a mock health service factory."""
        factory = Mock(spec=HealthServiceFactory)
        factory.create.return_value = mock_health_service
        return factory

    @pytest.fixture
    def mock_request(self, mock_health_service_factory: Mock) -> web.Request:
        """Create a mock request with app context."""
        app = web.Application()
        app[health_service_factory_key] = mock_health_service_factory

        return make_mocked_request("GET", "/health/liveness", app=app)

    async def test_liveness_check_healthy(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test successful liveness check."""
        # Arrange
        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            version="1.0.0",
        )

        mock_health_service.check_liveness.return_value = health_result

        # Act
        response = await liveness_check(mock_request)

        # Assert
        assert response.status == 200
        assert response.content_type == "application/json"

        # Verify response data
        assert response.text is not None
        response_data = json.loads(response.text)
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "cityhive"
        assert response_data["version"] == "1.0.0"
        assert response_data["timestamp"] == "2024-01-01T12:00:00+00:00"

        # Verify service was called
        mock_health_service.check_liveness.assert_called_once()

    async def test_liveness_check_healthy_no_version(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test liveness check without version."""
        # Arrange
        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            version=None,
        )

        mock_health_service.check_liveness.return_value = health_result

        # Act
        response = await liveness_check(mock_request)

        # Assert
        assert response.status == 200

        assert response.text is not None
        response_data = json.loads(response.text)
        assert "version" not in response_data

    async def test_liveness_check_unhealthy(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test unhealthy liveness check."""
        # Arrange
        health_result = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
        )

        mock_health_service.check_liveness.return_value = health_result

        # Act
        response = await liveness_check(mock_request)

        # Assert
        assert response.status == 503

        assert response.text is not None
        response_data = json.loads(response.text)
        assert response_data["status"] == "unhealthy"


class TestReadinessCheck:
    """Test cases for readiness check endpoint."""

    @pytest.fixture
    def mock_health_service(self) -> Mock:
        """Create a mock health service."""
        return Mock(spec=HealthService)

    @pytest.fixture
    def mock_health_service_factory(self, mock_health_service: Mock) -> Mock:
        """Create a mock health service factory."""
        factory = Mock(spec=HealthServiceFactory)
        factory.create.return_value = mock_health_service
        return factory

    @pytest.fixture
    def mock_db_session_factory(self) -> Mock:
        """Create a mock database session factory."""
        return Mock()

    @pytest.fixture
    def mock_request(
        self,
        mock_health_service_factory: Mock,
        mock_db_session_factory: Mock,
    ) -> web.Request:
        """Create a mock request with app context."""
        app = web.Application()
        app[health_service_factory_key] = mock_health_service_factory
        app[db_key] = mock_db_session_factory

        return make_mocked_request("GET", "/health/readiness", app=app)

    async def test_readiness_check_healthy_with_components(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
        mock_db_session_factory: Mock,
    ) -> None:
        """Test successful readiness check with healthy components."""
        # Arrange
        db_component = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Connected successfully",
            response_time_ms=45.0,
        )

        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            version="2.0.0",
            components=[db_component],
        )

        mock_health_service.check_readiness.return_value = health_result

        # Act
        response = await readiness_check(mock_request)

        # Assert
        assert response.status == 200
        assert response.content_type == "application/json"

        assert response.text is not None
        response_data = json.loads(response.text)
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "cityhive"
        assert response_data["version"] == "2.0.0"
        assert response_data["timestamp"] == "2024-01-01T12:00:00+00:00"

        # Verify components
        assert "components" in response_data
        assert len(response_data["components"]) == 1

        component_data = response_data["components"][0]
        assert component_data["name"] == "database"
        assert component_data["status"] == "healthy"
        assert component_data["message"] == "Connected successfully"
        assert component_data["response_time_ms"] == 45.0

        # Verify service was called with correct parameters
        mock_health_service.check_readiness.assert_called_once_with(
            mock_db_session_factory
        )

    async def test_readiness_check_unhealthy_with_metadata(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test readiness check with unhealthy component and metadata."""
        # Arrange
        db_component = ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message="Connection timeout",
            response_time_ms=5000.0,
            metadata={"timeout_seconds": 5.0, "error_type": "TimeoutError"},
        )

        health_result = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            components=[db_component],
        )

        mock_health_service.check_readiness.return_value = health_result

        # Act
        response = await readiness_check(mock_request)

        # Assert
        assert response.status == 503

        assert response.text is not None
        response_data = json.loads(response.text)
        assert response_data["status"] == "unhealthy"

        component_data = response_data["components"][0]
        assert component_data["status"] == "unhealthy"
        assert component_data["metadata"] == {
            "timeout_seconds": 5.0,
            "error_type": "TimeoutError",
        }

    async def test_readiness_check_no_components(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test readiness check with no components."""
        # Arrange
        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            components=None,
        )

        mock_health_service.check_readiness.return_value = health_result

        # Act
        response = await readiness_check(mock_request)

        # Assert
        assert response.status == 200

        assert response.text is not None
        response_data = json.loads(response.text)
        assert "components" not in response_data

    async def test_readiness_check_empty_components(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test readiness check with empty components list."""
        # Arrange
        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            components=[],
        )

        mock_health_service.check_readiness.return_value = health_result

        # Act
        response = await readiness_check(mock_request)

        # Assert
        assert response.status == 200

        assert response.text is not None
        response_data = json.loads(response.text)
        assert response_data["components"] == []

    async def test_readiness_check_component_without_metadata(
        self,
        mock_request: web.Request,
        mock_health_service: Mock,
    ) -> None:
        """Test readiness check with component that has no metadata."""
        # Arrange
        db_component = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="OK",
            response_time_ms=30.0,
            metadata=None,
        )

        health_result = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service="cityhive",
            components=[db_component],
        )

        mock_health_service.check_readiness.return_value = health_result

        # Act
        response = await readiness_check(mock_request)

        # Assert
        assert response.text is not None
        response_data = json.loads(response.text)
        component_data = response_data["components"][0]

        # Should not have metadata field when metadata is None
        assert "metadata" not in component_data
