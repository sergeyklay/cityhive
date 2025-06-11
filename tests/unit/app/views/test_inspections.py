"""Unit tests for inspection API views."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy.exc import IntegrityError

from cityhive.app.views.inspections import create_inspection
from cityhive.domain.inspection import HiveNotFoundError, InvalidScheduleError
from cityhive.domain.models import Inspection
from cityhive.infrastructure.typedefs import db_key, inspection_service_factory_key


class MockAsyncContextManager:
    """Mock async context manager for database sessions."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def session_maker():
    """Mock session maker."""
    session = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    session_maker = Mock()
    session_maker.return_value = MockAsyncContextManager(session)
    return session_maker


@pytest.fixture
def mock_inspection_service_factory():
    """Create a mock inspection service factory."""
    mock_factory = AsyncMock()
    mock_factory.create_service = Mock()
    return mock_factory


@pytest.fixture
def app_with_services(session_maker, mock_inspection_service_factory):
    """Mock app with database and services configured."""
    app = {}
    app[db_key] = session_maker
    app[inspection_service_factory_key] = mock_inspection_service_factory
    return app


@pytest.fixture
def inspection_data():
    """Sample inspection creation data."""
    return {
        "hive_id": 42,
        "scheduled_for": "2025-06-15",
        "notes": "Check the condition of the wax and add a new frame",
    }


@pytest.fixture
def minimal_inspection_data():
    """Minimal inspection creation data."""
    return {
        "hive_id": 42,
        "scheduled_for": "2025-06-15",
    }


@pytest.fixture
def mock_inspection():
    """Mock inspection model."""
    inspection = Mock(spec=Inspection)
    inspection.id = 123
    inspection.hive_id = 42
    inspection.scheduled_for = date(2025, 6, 15)
    inspection.notes = "Check the condition of the wax and add a new frame"
    inspection.created_at = datetime(2025, 6, 10, 14, 20, tzinfo=timezone.utc)
    return inspection


@pytest.fixture
def mock_inspection_minimal():
    """Mock minimal inspection model."""
    inspection = Mock(spec=Inspection)
    inspection.id = 123
    inspection.hive_id = 42
    inspection.scheduled_for = date(2025, 6, 15)
    inspection.notes = None
    inspection.created_at = datetime(2025, 6, 10, 14, 20, tzinfo=timezone.utc)
    return inspection


async def test_create_inspection_with_valid_data_returns_success(
    app_with_services, inspection_data, mock_inspection
):
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=inspection_data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.return_value = mock_inspection

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 201
    mock_service_factory.create_service.assert_called_once()
    mock_inspection_service.create_inspection.assert_called_once()
    app_with_services[db_key]().session.commit.assert_awaited_once()


async def test_create_inspection_with_minimal_data_returns_success(
    app_with_services, minimal_inspection_data, mock_inspection_minimal
):
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=minimal_inspection_data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.return_value = mock_inspection_minimal

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 201
    mock_service_factory.create_service.assert_called_once()
    mock_inspection_service.create_inspection.assert_called_once()
    app_with_services[db_key]().session.commit.assert_awaited_once()


async def test_create_inspection_with_hive_not_found_returns_not_found(
    app_with_services,
):
    data = {"hive_id": 999, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.side_effect = HiveNotFoundError(999)

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 404
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_inspection_with_invalid_schedule_returns_bad_request(
    app_with_services,
):
    data = {"hive_id": 42, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.side_effect = InvalidScheduleError(
        "Inspection cannot be scheduled more than 1 year in advance"
    )

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 400
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_inspection_with_invalid_json_returns_bad_request(
    app_with_services,
):
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

    response = await create_inspection(request)

    assert response.status == 400


async def test_create_inspection_with_missing_required_field_returns_bad_request(
    app_with_services,
):
    data = {"scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    response = await create_inspection(request)

    assert response.status == 400


async def test_create_inspection_with_integrity_error_returns_conflict(
    app_with_services,
):
    """Test that IntegrityError returns 409 conflict instead of 500."""
    data = {"hive_id": 42, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.side_effect = IntegrityError(
        "duplicate key value violates unique constraint", "params", Exception("orig")
    )

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 409
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_inspection_with_integrity_error_during_commit_returns_conflict(
    app_with_services, mock_inspection
):
    """Test that IntegrityError during commit returns 409 conflict instead of 500."""
    data = {"hive_id": 42, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.return_value = mock_inspection

    app_with_services[db_key]().session.commit.side_effect = IntegrityError(
        "deferred constraint violation", "params", Exception("deferred check")
    )

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 409
    app_with_services[db_key]().session.rollback.assert_called_once()


async def test_create_inspection_returns_correct_content_type_header(
    app_with_services, mock_inspection
):
    data = {"hive_id": 42, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.return_value = mock_inspection

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 201
    assert response.content_type == "application/json"


async def test_create_inspection_returns_expected_response_structure(
    app_with_services, inspection_data, mock_inspection
):
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=inspection_data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.return_value = mock_inspection

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    response = await create_inspection(request)

    assert response.status == 201


async def test_create_inspection_with_programming_error_raises_exception(
    app_with_services,
):
    """Test that programming errors are re-raised instead of being silently caught."""
    data = {"hive_id": 42, "scheduled_for": "2025-06-15"}
    request = make_mocked_request("POST", "/api/inspections", app=app_with_services)
    request.json = AsyncMock(return_value=data)

    mock_inspection_service = AsyncMock()
    mock_inspection_service.create_inspection.side_effect = AttributeError(
        "'NoneType' object has no attribute 'some_method'"
    )

    mock_service_factory = app_with_services[inspection_service_factory_key]
    mock_service_factory.create_service.return_value = mock_inspection_service

    with pytest.raises(AttributeError):
        await create_inspection(request)

    app_with_services[db_key]().session.rollback.assert_called_once()
