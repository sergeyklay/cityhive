"""
Unit tests for user views.

Tests the refactored user views using the new domain architecture with service factory.
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request

from cityhive.app.views.users import create_user
from cityhive.domain.models import User
from cityhive.domain.user.exceptions import DuplicateUserError
from cityhive.infrastructure.typedefs import db_key, user_service_factory_key


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
def mock_user_service_factory():
    """Create a mock user service factory."""
    mock_factory = AsyncMock()
    from unittest.mock import Mock

    mock_factory.create_service = Mock()
    return mock_factory


@pytest.fixture
def app_with_services(session_maker, mock_user_service_factory):
    """Mock app with database and services configured."""
    app = {}
    app[db_key] = session_maker
    app[user_service_factory_key] = mock_user_service_factory
    return app


@pytest.fixture
def valid_user_data():
    """Valid user registration data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
    }


@pytest.fixture
def sample_user():
    """Sample user model."""
    from datetime import datetime

    user = User(name="John Doe", email="john.doe@example.com")
    user.id = 1
    user.registered_at = datetime.now()
    return user


async def test_create_user_success(app_with_services, valid_user_data, sample_user):
    """Test successful user creation through the view using service factory."""
    request = make_mocked_request("POST", "/api/users", app=app_with_services)
    request.json = AsyncMock(return_value=valid_user_data)

    mock_service = AsyncMock()
    mock_service.register_user.return_value = sample_user

    mock_service_factory = app_with_services[user_service_factory_key]
    mock_service_factory.create_service.return_value = mock_service

    response = await create_user(request)

    assert response.status == 201

    mock_service_factory.create_service.assert_called_once()
    mock_service.register_user.assert_called_once()

    app_with_services[db_key]().session.commit.assert_awaited_once()


async def test_create_user_validation_error(app_with_services):
    """Test user creation with invalid data."""
    invalid_data = {"name": "", "email": "invalid-email"}
    request = make_mocked_request("POST", "/api/users", app=app_with_services)
    request.json = AsyncMock(return_value=invalid_data)

    response = await create_user(request)

    assert response.status == 400


async def test_create_user_duplicate_error(app_with_services, valid_user_data):
    """Test user creation when user already exists."""
    request = make_mocked_request("POST", "/api/users", app=app_with_services)
    request.json = AsyncMock(return_value=valid_user_data)

    mock_service = AsyncMock()
    mock_service.register_user.side_effect = DuplicateUserError("john.doe@example.com")

    mock_service_factory = app_with_services[user_service_factory_key]
    mock_service_factory.create_service.return_value = mock_service

    response = await create_user(request)

    assert response.status == 409

    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_user_json_parse_error(app_with_services):
    """Test user creation with invalid JSON."""
    request = make_mocked_request("POST", "/api/users", app=app_with_services)

    with patch("cityhive.app.views.users.parse_json_request") as mock_parse:
        mock_parse.return_value = (None, "Invalid JSON format")

        response = await create_user(request)

        assert response.status == 400


async def test_create_user_unexpected_error(app_with_services, valid_user_data):
    """Test user creation when unexpected error occurs."""
    request = make_mocked_request("POST", "/api/users", app=app_with_services)
    request.json = AsyncMock(return_value=valid_user_data)

    mock_service = AsyncMock()
    mock_service.register_user.side_effect = Exception("Database connection failed")

    mock_service_factory = app_with_services[user_service_factory_key]
    mock_service_factory.create_service.return_value = mock_service

    response = await create_user(request)

    assert response.status == 500

    app_with_services[db_key]().session.rollback.assert_called_once()
