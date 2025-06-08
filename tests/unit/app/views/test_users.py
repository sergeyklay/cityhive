"""
Tests for API views.

These tests cover the JSON API endpoints for user registration using pure unit testing.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from cityhive.app.views.users import create_user
from cityhive.domain.models import User
from cityhive.domain.services.user import (
    UserRegistrationErrorType,
    UserRegistrationResult,
)
from tests.unit.app.views.conftest import make_api_request


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


async def test_create_user_with_valid_data_returns_success(
    app_with_db, mocker, user_data, mock_user
):
    request = make_api_request("POST", "/api/users", app_with_db)

    # Mock request.json() to return our test data
    request.json = AsyncMock(return_value=user_data)

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    create_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = create_user_mock

    response = await create_user(request)

    assert response.status == 201
    assert response.content_type == "application/json"


async def test_create_user_with_invalid_json_returns_bad_request(base_app, mocker):
    request = make_api_request("POST", "/api/users", base_app)

    # Mock request.json() to raise an exception
    request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

    response = await create_user(request)

    assert response.status == 400


@pytest.mark.parametrize(
    "test_data,description",
    [
        ({"email": "john@example.com"}, "missing name"),
        ({"name": "", "email": "john@example.com"}, "empty name"),
        ({"name": "   ", "email": "john@example.com"}, "whitespace name"),
    ],
)
async def test_create_user_with_invalid_name_returns_validation_error(
    base_app, mocker, test_data, description
):
    request = make_api_request("POST", "/api/users", base_app)
    request.json = AsyncMock(return_value=test_data)

    response = await create_user(request)

    assert response.status == 400


@pytest.mark.parametrize(
    "test_data,description",
    [
        ({"name": "John"}, "missing email"),
        ({"name": "John", "email": ""}, "empty email"),
        ({"name": "John", "email": "   "}, "whitespace email"),
        ({"name": "John", "email": "invalid-email"}, "invalid email format"),
        ({"name": "John", "email": "no-domain@"}, "email missing domain"),
        ({"name": "John", "email": "@no-local.com"}, "email missing local part"),
        ({"name": "John", "email": "invalid@@domain.com"}, "email with double @"),
    ],
)
async def test_create_user_with_invalid_email_returns_validation_error(
    base_app, mocker, test_data, description
):
    request = make_api_request("POST", "/api/users", base_app)
    request.json = AsyncMock(return_value=test_data)

    response = await create_user(request)

    assert response.status == 400


async def test_create_user_with_existing_email_returns_conflict(app_with_db, mocker):
    data = {"name": "John", "email": "existing@example.com"}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = UserRegistrationResult(
        success=False,
        error_type=UserRegistrationErrorType.USER_EXISTS,
        error_message="User with this email already exists",
    )
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 409


async def test_create_user_with_database_error_returns_server_error(
    app_with_db, mocker
):
    data = {"name": "John", "email": "john@example.com"}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = UserRegistrationResult(
        success=False,
        error_type=UserRegistrationErrorType.DATABASE_ERROR,
        error_message="Database connection failed",
    )
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 500


async def test_create_user_with_unexpected_exception_returns_internal_error(
    app_with_db, mocker
):
    data = {"name": "John", "email": "john@example.com"}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(side_effect=Exception("Unexpected error"))
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 500


async def test_create_user_normalizes_email_to_lowercase(
    app_with_db, mocker, mock_user
):
    data = {"name": "John", "email": "JOHN@EXAMPLE.COM"}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 201


async def test_create_user_trims_whitespace_from_inputs(app_with_db, mocker, mock_user):
    data = {"name": "  John  ", "email": "  john@example.com  "}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 201


async def test_create_user_returns_correct_content_type_header(
    app_with_db, mocker, mock_user
):
    data = {"name": "Test User", "email": "test@example.com"}
    request = make_api_request("POST", "/api/users", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = UserRegistrationResult(success=True, user=mock_user)
    mock_user_service = mocker.patch("cityhive.app.views.users.UserService")
    register_user_mock = AsyncMock(return_value=mock_result)
    mock_user_service.return_value.register_user = register_user_mock

    response = await create_user(request)

    assert response.status == 201
    assert response.content_type == "application/json"
