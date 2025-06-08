"""
Tests for API views.

These tests cover the JSON API endpoints for user registration.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from aiohttp import web

from cityhive.app.views.api import create_user
from cityhive.domain.models import User
from cityhive.domain.services.user import (
    UserRegistrationErrorType,
    UserRegistrationResult,
)
from cityhive.infrastructure.typedefs import db_key


class MockAsyncContextManager:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def user_data():
    return {"name": "John Beekeeper", "email": "john@example.com"}


@pytest.fixture
def mock_user(mocker):
    user = User(
        id=1,
        name="John Beekeeper",
        email="john@example.com",
        api_key=uuid.UUID("12345678-1234-5678-9012-123456789abc"),
    )
    user.registered_at = mocker.MagicMock()
    user.registered_at.isoformat.return_value = "2025-06-08T16:00:00Z"
    return user


@pytest.fixture
def mock_session_maker():
    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    return session_maker, session


async def test_create_user_with_valid_data_returns_success(
    aiohttp_client, mocker, user_data, mock_user
):
    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post("/api/users", json=user_data) as response:
        assert response.status == 201

        data = await response.json()
        assert data["success"] is True
        assert data["user"]["id"] == 1
        assert data["user"]["name"] == "John Beekeeper"
        assert data["user"]["email"] == "john@example.com"
        assert data["user"]["api_key"] == "12345678-1234-5678-9012-123456789abc"


async def test_create_user_with_invalid_json_returns_bad_request(aiohttp_client):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post("/api/users", data="invalid json") as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Invalid JSON format"


async def test_create_user_with_missing_name_returns_validation_error(aiohttp_client):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"email": "test@example.com"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Name is required"


async def test_create_user_with_empty_name_returns_validation_error(aiohttp_client):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "", "email": "test@example.com"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Name is required"


async def test_create_user_with_whitespace_name_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "   ", "email": "test@example.com"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Name is required"


async def test_create_user_with_missing_email_returns_validation_error(aiohttp_client):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post("/api/users", json={"name": "John"}) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Email is required"


async def test_create_user_with_empty_email_returns_validation_error(aiohttp_client):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": ""}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Email is required"


async def test_create_user_with_whitespace_email_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "   "}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Email is required"


async def test_create_user_with_invalid_email_format_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "invalid-email"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Invalid email format"


async def test_create_user_with_email_missing_domain_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "no-domain@"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Invalid email format"


async def test_create_user_with_email_missing_local_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "@no-local.com"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Invalid email format"


async def test_create_user_with_email_missing_tld_returns_validation_error(
    aiohttp_client,
):
    app = web.Application()
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "no-tld@domain"}
    ) as response:
        assert response.status == 400

        data = await response.json()
        assert data["error"] == "Invalid email format"


async def test_create_user_with_existing_email_returns_conflict(aiohttp_client, mocker):
    mock_result = UserRegistrationResult(
        success=False,
        error_type=UserRegistrationErrorType.USER_EXISTS,
        error_message="User with this email already exists",
    )
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "existing@example.com"}
    ) as response:
        assert response.status == 409

        data = await response.json()
        assert data["success"] is False
        assert data["error"] == "User with this email already exists"


async def test_create_user_with_database_error_returns_server_error(
    aiohttp_client, mocker
):
    mock_result = UserRegistrationResult(
        success=False,
        error_type=UserRegistrationErrorType.DATABASE_ERROR,
        error_message="Database connection failed",
    )
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "john@example.com"}
    ) as response:
        assert response.status == 500

        data = await response.json()
        assert data["success"] is False
        assert data["error"] == "Database connection failed"


async def test_create_user_with_unexpected_exception_returns_internal_error(
    aiohttp_client, mocker
):
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    mock_user_service.return_value.register_user.side_effect = Exception(
        "Unexpected error"
    )

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "john@example.com"}
    ) as response:
        assert response.status == 500

        data = await response.json()
        assert data["error"] == "Internal server error"


async def test_create_user_normalizes_email_to_lowercase(aiohttp_client, mocker):
    mock_user = User(
        id=1,
        name="John Beekeeper",
        email="john@example.com",
        api_key=uuid.UUID("12345678-1234-5678-9012-123456789abc"),
    )
    mock_user.registered_at = mocker.MagicMock()
    mock_user.registered_at.isoformat.return_value = "2025-06-08T16:00:00Z"

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "John", "email": "JOHN@EXAMPLE.COM"}
    ) as response:
        assert response.status == 201

        call_args = mock_user_service.return_value.register_user.call_args
        assert call_args[0][1].email == "john@example.com"


async def test_create_user_trims_whitespace_from_inputs(aiohttp_client, mocker):
    mock_user = User(
        id=1,
        name="John Beekeeper",
        email="john@example.com",
        api_key=uuid.UUID("12345678-1234-5678-9012-123456789abc"),
    )
    mock_user.registered_at = mocker.MagicMock()
    mock_user.registered_at.isoformat.return_value = "2025-06-08T16:00:00Z"

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users",
        json={"name": "  John Beekeeper  ", "email": "  john@example.com  "},
    ) as response:
        assert response.status == 201

        call_args = mock_user_service.return_value.register_user.call_args
        assert call_args[0][1].name == "John Beekeeper"
        assert call_args[0][1].email == "john@example.com"


async def test_create_user_returns_correct_content_type_header(aiohttp_client, mocker):
    mock_user = User(
        id=1,
        name="Test User",
        email="test@example.com",
        api_key=uuid.UUID("12345678-1234-5678-9012-123456789abc"),
    )
    mock_user.registered_at = mocker.MagicMock()
    mock_user.registered_at.isoformat.return_value = "2025-06-08T16:00:00Z"

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.api.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    session = AsyncMock()

    def session_maker():
        return MockAsyncContextManager(session)

    app = web.Application()
    app[db_key] = session_maker  # type: ignore
    app.router.add_post("/api/users", create_user)

    client = await aiohttp_client(app)

    async with client.post(
        "/api/users", json={"name": "Test User", "email": "test@example.com"}
    ) as response:
        assert response.status == 201
        assert response.headers["Content-Type"] == "application/json; charset=utf-8"
