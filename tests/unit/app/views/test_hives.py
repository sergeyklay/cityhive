"""Unit tests for hive API views."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp.test_utils import make_mocked_request

from cityhive.app.views.hives import create_hive
from cityhive.domain.hive import InvalidLocationError, UserNotFoundError
from cityhive.domain.models import Hive
from cityhive.infrastructure.typedefs import db_key, hive_service_factory_key


class MockAsyncContextManager:
    """Mock async context manager for database sessions."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def session_maker(mock_session):
    """Create a session maker function that returns a context manager."""

    def _session_maker():
        return MockAsyncContextManager(mock_session)

    return _session_maker


@pytest.fixture
def mock_hive_service_factory():
    """Create a mock hive service factory."""
    mock_factory = AsyncMock()
    mock_factory.create_service = Mock()
    return mock_factory


@pytest.fixture
def app_with_services(session_maker, mock_hive_service_factory):
    """Mock app with database and services configured."""
    app = {}
    app[db_key] = session_maker
    app[hive_service_factory_key] = mock_hive_service_factory
    return app


@pytest.fixture
def hive_data():
    return {
        "user_id": 1,
        "name": "Hive Alpha",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "frame_type": "Langstroth",
        "installed_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def minimal_hive_data():
    return {"user_id": 1, "name": "Minimal Hive"}


@pytest.fixture
def mock_hive():
    hive = Hive(
        user_id=1,
        name="Hive Alpha",
        frame_type="Langstroth",
        installed_at=datetime(2024, 1, 15, 10, 30),
    )
    hive.id = 1
    return hive


@pytest.fixture
def mock_hive_minimal():
    hive = Hive(user_id=1, name="Minimal Hive")
    hive.id = 1
    return hive


async def test_create_hive_with_valid_data_returns_success(
    app_with_services, hive_data, mock_hive
):
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=hive_data)

    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.return_value = mock_hive

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 201
    mock_service_factory.create_service.assert_called_once()
    mock_hive_service.create_hive.assert_called_once()
    app_with_services[db_key]().session.commit.assert_awaited_once()


async def test_create_hive_with_minimal_data_returns_success(
    app_with_services, minimal_hive_data, mock_hive_minimal
):
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=minimal_hive_data)

    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.return_value = mock_hive_minimal

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 201
    mock_service_factory.create_service.assert_called_once()
    mock_hive_service.create_hive.assert_called_once()
    app_with_services[db_key]().session.commit.assert_awaited_once()


async def test_create_hive_with_user_not_found_returns_not_found(app_with_services):
    data = {"user_id": 999, "name": "Hive Alpha"}
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    # Mock the service factory and service to raise UserNotFoundError
    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.side_effect = UserNotFoundError(999)

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 404
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_hive_with_invalid_location_returns_validation_error(
    app_with_services,
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.side_effect = InvalidLocationError(
        "Invalid location coordinates"
    )

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 400
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_hive_with_unexpected_exception_returns_internal_error(
    app_with_services,
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.side_effect = Exception("Unexpected error")

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 500
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_hive_returns_correct_content_type_header(
    app_with_services, mock_hive
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_mocked_request("POST", "/api/hives", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_hive_service = AsyncMock()
    mock_hive_service.create_hive.return_value = mock_hive

    mock_service_factory = app_with_services[hive_service_factory_key]
    mock_service_factory.create_service.return_value = mock_hive_service

    response = await create_hive(request)

    assert response.status == 201
    assert response.content_type == "application/json"
