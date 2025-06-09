"""Unit tests for HiveService domain logic."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy.exc import IntegrityError

from cityhive.domain.models import User
from cityhive.domain.services.hive import (
    HiveCreationData,
    HiveCreationErrorType,
    HiveService,
)


@pytest.fixture
def hive_service():
    """Create HiveService instance."""
    return HiveService()


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    from unittest.mock import Mock

    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def valid_creation_data():
    """Valid hive creation data."""
    return HiveCreationData(
        user_id=123,
        name="Test Hive",
        latitude=45.5152,
        longitude=-122.6784,
        frame_type="Langstroth",
        installed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    )


@pytest.fixture
def mock_user():
    """Mock user object."""
    user = User(id=123, email="beekeeper@example.com", name="John Beekeeper")
    return user


async def test_create_hive_success_with_location(
    hive_service, mock_session, valid_creation_data, mock_user, mocker
):
    """Test successful hive creation with location coordinates."""
    mock_get_user = mocker.patch.object(
        hive_service, "_get_user_by_id", return_value=mock_user
    )

    result = await hive_service.create_hive(mock_session, valid_creation_data)

    assert result.success is True
    assert result.hive is not None
    assert result.error_type is None
    assert result.error_message is None

    hive = result.hive
    assert hive.user_id == 123
    assert hive.name == "Test Hive"
    assert hive.frame_type == "Langstroth"
    assert hive.installed_at == valid_creation_data.installed_at
    assert hive.location is not None
    assert isinstance(hive.location, WKTElement)

    mock_get_user.assert_called_once_with(mock_session, 123)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


async def test_create_hive_success_without_location(
    hive_service, mock_session, mock_user, mocker
):
    """Test successful hive creation without location coordinates."""
    creation_data = HiveCreationData(
        user_id=123,
        name="Indoor Hive",
        frame_type="Top Bar",
    )
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)

    result = await hive_service.create_hive(mock_session, creation_data)

    assert result.success is True
    assert result.hive is not None
    hive = result.hive
    assert hive.location is None
    assert hive.installed_at is not None

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


async def test_create_hive_user_not_found(
    hive_service, mock_session, valid_creation_data, mocker
):
    """Test hive creation fails when user doesn't exist."""
    mock_get_user = mocker.patch.object(
        hive_service, "_get_user_by_id", return_value=None
    )

    result = await hive_service.create_hive(mock_session, valid_creation_data)

    assert result.success is False
    assert result.hive is None
    assert result.error_type == HiveCreationErrorType.USER_NOT_FOUND
    assert result.error_message == "User not found"

    mock_get_user.assert_called_once_with(mock_session, 123)
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.parametrize(
    "latitude,longitude,missing_coord",
    [
        (45.5152, None, "longitude"),
        (None, -122.6784, "latitude"),
    ],
)
async def test_create_hive_partial_coordinates(
    hive_service, mock_session, mock_user, mocker, latitude, longitude, missing_coord
):
    """Test hive creation fails with partial coordinates provided."""
    creation_data = HiveCreationData(
        user_id=123,
        name="Test Hive",
        latitude=latitude,
        longitude=longitude,
    )
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)

    result = await hive_service.create_hive(mock_session, creation_data)

    assert result.success is False
    assert result.hive is None
    assert result.error_type == HiveCreationErrorType.INVALID_LOCATION
    assert missing_coord in result.error_message
    assert (
        "Both latitude and longitude must be provided together" in result.error_message
    )

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


async def test_create_hive_invalid_coordinates(
    hive_service, mock_session, mock_user, mocker
):
    """Test hive creation fails with invalid coordinate values."""
    creation_data = HiveCreationData(
        user_id=123,
        name="Test Hive",
        latitude=999.0,
        longitude=999.0,
    )
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)

    mock_wkt = mocker.patch("cityhive.domain.services.hive.WKTElement")
    mock_wkt.side_effect = ValueError("Invalid coordinates")

    result = await hive_service.create_hive(mock_session, creation_data)

    assert result.success is False
    assert result.hive is None
    assert result.error_type == HiveCreationErrorType.INVALID_LOCATION
    assert result.error_message == "Invalid location coordinates"


async def test_create_hive_database_integrity_error(
    hive_service, mock_session, valid_creation_data, mock_user, mocker
):
    """Test hive creation fails with database integrity constraint violation."""
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)
    mock_session.commit.side_effect = IntegrityError(
        "duplicate key violation", "params", Exception("orig error")
    )

    result = await hive_service.create_hive(mock_session, valid_creation_data)

    assert result.success is False
    assert result.hive is None
    assert result.error_type == HiveCreationErrorType.INTEGRITY_VIOLATION
    assert result.error_message == "Hive creation failed due to data conflict"

    mock_session.rollback.assert_called_once()


async def test_create_hive_unexpected_database_error(
    hive_service, mock_session, valid_creation_data, mock_user, mocker
):
    """Test hive creation fails with unexpected database error."""
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)
    mock_session.commit.side_effect = Exception("Database connection lost")

    result = await hive_service.create_hive(mock_session, valid_creation_data)

    assert result.success is False
    assert result.hive is None
    assert result.error_type == HiveCreationErrorType.UNKNOWN_ERROR
    assert result.error_message == "Internal server error during hive creation"

    mock_session.rollback.assert_called_once()


async def test_create_hive_minimal_data(hive_service, mock_session, mock_user, mocker):
    """Test hive creation with minimal required data."""
    creation_data = HiveCreationData(user_id=123, name="Minimal Hive")
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)

    result = await hive_service.create_hive(mock_session, creation_data)

    assert result.success is True
    hive = result.hive
    assert hive.user_id == 123
    assert hive.name == "Minimal Hive"
    assert hive.location is None
    assert hive.frame_type is None
    assert hive.installed_at is not None


async def test_create_hive_coordinate_edge_cases(
    hive_service, mock_session, mock_user, mocker
):
    """Test hive creation with edge case coordinates."""
    creation_data = HiveCreationData(
        user_id=123,
        name="Edge Case Hive",
        latitude=0.0,
        longitude=0.0,
    )
    mocker.patch.object(hive_service, "_get_user_by_id", return_value=mock_user)

    result = await hive_service.create_hive(mock_session, creation_data)

    assert result.success is True
    hive = result.hive
    assert hive.location is not None
    assert isinstance(hive.location, WKTElement)
