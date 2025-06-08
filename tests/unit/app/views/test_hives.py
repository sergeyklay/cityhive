"""
Tests for hive API views.

These tests cover the JSON API endpoints for hive creation using pure unit testing.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from cityhive.app.views.hives import create_hive
from cityhive.domain.models import Hive
from cityhive.domain.services.hive import (
    HiveCreationErrorType,
    HiveCreationResult,
)
from tests.unit.app.views.conftest import make_api_request


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
    return {"user_id": 1, "name": "Hive Alpha"}


@pytest.fixture
def mock_hive(mocker):
    hive = Hive(
        id=1,
        user_id=1,
        name="Hive Alpha",
        frame_type="Langstroth",
        installed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        location=None,
    )
    return hive


@pytest.fixture
def mock_hive_minimal(mocker):
    hive = Hive(
        id=1,
        user_id=1,
        name="Hive Alpha",
        frame_type=None,
        installed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        location=None,
    )
    return hive


async def test_create_hive_with_valid_data_returns_success(
    app_with_db, mocker, hive_data, mock_hive
):
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=hive_data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_with_minimal_data_returns_success(
    app_with_db, mocker, minimal_hive_data, mock_hive_minimal
):
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=minimal_hive_data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive_minimal)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_with_invalid_json_returns_bad_request(base_app, mocker):
    request = make_api_request("POST", "/api/hives", base_app)
    request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

    response = await create_hive(request)

    assert response.status == 400


@pytest.mark.parametrize(
    "test_data,description",
    [
        ({"name": "Hive Alpha"}, "missing user_id"),
        ({"user_id": None, "name": "Hive Alpha"}, "null user_id"),
        ({"user_id": "invalid", "name": "Hive Alpha"}, "invalid user_id type"),
    ],
)
async def test_create_hive_with_invalid_user_id_returns_validation_error(
    base_app, mocker, test_data, description
):
    request = make_api_request("POST", "/api/hives", base_app)
    request.json = AsyncMock(return_value=test_data)

    response = await create_hive(request)

    assert response.status == 400


@pytest.mark.parametrize(
    "test_data,description",
    [
        ({"user_id": 1}, "missing name"),
        ({"user_id": 1, "name": ""}, "empty name"),
        ({"user_id": 1, "name": "   "}, "whitespace name"),
    ],
)
async def test_create_hive_with_invalid_name_returns_validation_error(
    base_app, mocker, test_data, description
):
    request = make_api_request("POST", "/api/hives", base_app)
    request.json = AsyncMock(return_value=test_data)

    response = await create_hive(request)

    assert response.status == 400


async def test_create_hive_with_invalid_latitude_returns_success_without_coordinates(
    app_with_db, mocker, mock_hive_minimal
):
    data = {"user_id": 1, "name": "Hive Alpha", "latitude": "invalid"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive_minimal)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_with_invalid_longitude_returns_success_without_coordinates(
    app_with_db, mocker, mock_hive_minimal
):
    data = {"user_id": 1, "name": "Hive Alpha", "longitude": "invalid"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive_minimal)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


@pytest.mark.parametrize(
    "test_data,description",
    [
        ({"user_id": 1, "name": "Hive Alpha", "latitude": 40.7128}, "latitude only"),
        ({"user_id": 1, "name": "Hive Alpha", "longitude": -74.0060}, "longitude only"),
        (
            {"user_id": 1, "name": "Hive Alpha", "latitude": 91.0, "longitude": 0.0},
            "latitude out of range",
        ),
        (
            {"user_id": 1, "name": "Hive Alpha", "latitude": 0.0, "longitude": 181.0},
            "longitude out of range",
        ),
    ],
)
async def test_create_hive_with_invalid_coordinates_returns_validation_error(
    base_app, mocker, test_data, description
):
    request = make_api_request("POST", "/api/hives", base_app)
    request.json = AsyncMock(return_value=test_data)

    response = await create_hive(request)

    assert response.status == 400


async def test_create_hive_with_invalid_date_format_returns_validation_error(
    base_app, mocker
):
    data = {
        "user_id": 1,
        "name": "Hive Alpha",
        "installed_at": "not-a-date",
    }
    request = make_api_request("POST", "/api/hives", base_app)
    request.json = AsyncMock(return_value=data)

    response = await create_hive(request)

    assert response.status == 400


async def test_create_hive_trims_whitespace_from_name(app_with_db, mocker, mock_hive):
    data = {"user_id": 1, "name": "  Hive Alpha  "}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_trims_whitespace_from_frame_type(
    app_with_db, mocker, mock_hive
):
    data = {"user_id": 1, "name": "Hive Alpha", "frame_type": "  Langstroth  "}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_handles_empty_frame_type_as_none(
    app_with_db, mocker, mock_hive_minimal
):
    data = {"user_id": 1, "name": "Hive Alpha", "frame_type": ""}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive_minimal)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201


async def test_create_hive_with_user_not_found_returns_not_found(app_with_db, mocker):
    data = {"user_id": 999, "name": "Hive Alpha"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(
        success=False,
        error_type=HiveCreationErrorType.USER_NOT_FOUND,
        error_message="User not found",
    )
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 404


async def test_create_hive_with_invalid_location_returns_validation_error(
    app_with_db, mocker
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(
        success=False,
        error_type=HiveCreationErrorType.INVALID_LOCATION,
        error_message="Invalid location coordinates",
    )
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 400


async def test_create_hive_with_database_error_returns_server_error(
    app_with_db, mocker
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(
        success=False,
        error_type=HiveCreationErrorType.DATABASE_ERROR,
        error_message="Database connection failed",
    )
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 500


async def test_create_hive_with_unexpected_exception_returns_internal_error(
    app_with_db, mocker
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(side_effect=Exception("Unexpected error"))
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 500


async def test_create_hive_returns_correct_content_type_header(
    app_with_db, mocker, mock_hive
):
    data = {"user_id": 1, "name": "Hive Alpha"}
    request = make_api_request("POST", "/api/hives", app_with_db)
    request.json = AsyncMock(return_value=data)

    mock_result = HiveCreationResult(success=True, hive=mock_hive)
    mock_hive_service = mocker.patch("cityhive.app.views.hives.HiveService")
    create_hive_mock = AsyncMock(return_value=mock_result)
    mock_hive_service.return_value.create_hive = create_hive_mock

    response = await create_hive(request)

    assert response.status == 201
    assert response.content_type == "application/json"
