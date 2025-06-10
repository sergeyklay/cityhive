"""
Unit tests for HiveService.

Tests demonstrate improved testability with dependency injection and mocking.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from cityhive.domain.hive.exceptions import InvalidLocationError, UserNotFoundError
from cityhive.domain.hive.repository import HiveRepository
from cityhive.domain.hive.service import HiveCreationInput, HiveService
from cityhive.domain.models import Hive, User


@pytest.fixture
def mock_hive_repository():
    """Mock hive repository for testing."""
    return AsyncMock(spec=HiveRepository)


@pytest.fixture
def hive_service(mock_hive_repository):
    """Hive service with mocked dependencies."""
    return HiveService(mock_hive_repository)


@pytest.fixture
def valid_creation_input():
    """Valid hive creation input."""
    return HiveCreationInput(
        user_id=1,
        name="Test Hive",
        latitude=40.7128,
        longitude=-74.0060,
        frame_type="Langstroth",
        installed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
    )


@pytest.fixture
def minimal_creation_input():
    """Minimal hive creation input."""
    return HiveCreationInput(
        user_id=1,
        name="Minimal Hive",
        latitude=None,
        longitude=None,
        frame_type=None,
        installed_at=None,
    )


@pytest.fixture
def sample_user():
    """Sample user model."""
    user = User(name="Test User", email="test@example.com")
    user.id = 1
    return user


@pytest.fixture
def sample_hive():
    """Sample hive model."""
    hive = Hive(
        user_id=1,
        name="Test Hive",
        frame_type="Langstroth",
        installed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
    )
    hive.id = 1
    return hive


async def test_create_hive_success_with_location(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    valid_creation_input: HiveCreationInput,
    sample_user: User,
    sample_hive: Hive,
):
    """Test successful hive creation with location coordinates."""
    mock_hive_repository.get_user_by_id.return_value = sample_user
    mock_hive_repository.save.return_value = sample_hive

    result = await hive_service.create_hive(valid_creation_input)

    assert isinstance(result, Hive)
    assert result.id == sample_hive.id
    assert result.user_id == sample_hive.user_id
    assert result.name == sample_hive.name

    mock_hive_repository.get_user_by_id.assert_called_once_with(1)
    mock_hive_repository.save.assert_called_once()


async def test_create_hive_success_without_location(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    minimal_creation_input: HiveCreationInput,
    sample_user: User,
    sample_hive: Hive,
):
    """Test successful hive creation without location coordinates."""
    mock_hive_repository.get_user_by_id.return_value = sample_user
    mock_hive_repository.save.return_value = sample_hive

    result = await hive_service.create_hive(minimal_creation_input)

    assert isinstance(result, Hive)
    assert result.id == sample_hive.id

    mock_hive_repository.get_user_by_id.assert_called_once_with(1)
    mock_hive_repository.save.assert_called_once()


async def test_create_hive_user_not_found(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    valid_creation_input: HiveCreationInput,
):
    """Test hive creation fails when user doesn't exist."""
    mock_hive_repository.get_user_by_id.return_value = None

    with pytest.raises(UserNotFoundError) as exc_info:
        await hive_service.create_hive(valid_creation_input)

    assert exc_info.value.user_id == 1

    mock_hive_repository.get_user_by_id.assert_called_once_with(1)
    mock_hive_repository.save.assert_not_called()


async def test_create_hive_partial_coordinates_latitude_only(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    sample_user: User,
):
    """Test hive creation fails with only latitude provided."""
    creation_input = HiveCreationInput(
        user_id=1,
        name="Test Hive",
        latitude=40.7128,
        longitude=None,
        frame_type=None,
        installed_at=None,
    )
    mock_hive_repository.get_user_by_id.return_value = sample_user

    with pytest.raises(InvalidLocationError) as exc_info:
        await hive_service.create_hive(creation_input)

    assert "longitude" in str(exc_info.value)
    mock_hive_repository.save.assert_not_called()


async def test_create_hive_partial_coordinates_longitude_only(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    sample_user: User,
):
    """Test hive creation fails with only longitude provided."""
    creation_input = HiveCreationInput(
        user_id=1,
        name="Test Hive",
        latitude=None,
        longitude=-74.0060,
        frame_type=None,
        installed_at=None,
    )
    mock_hive_repository.get_user_by_id.return_value = sample_user

    with pytest.raises(InvalidLocationError) as exc_info:
        await hive_service.create_hive(creation_input)

    assert "latitude" in str(exc_info.value)
    mock_hive_repository.save.assert_not_called()


async def test_create_hive_database_integrity_error(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    valid_creation_input: HiveCreationInput,
    sample_user: User,
):
    """Test hive creation fails with database integrity constraint violation."""
    mock_hive_repository.get_user_by_id.return_value = sample_user
    mock_hive_repository.save.side_effect = IntegrityError(
        "duplicate key violation", "params", Exception("orig error")
    )

    with pytest.raises(InvalidLocationError) as exc_info:
        await hive_service.create_hive(valid_creation_input)

    assert "data conflict" in str(exc_info.value)
    mock_hive_repository.save.assert_called_once()


async def test_get_hive_by_id_found(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    sample_hive: Hive,
):
    """Test successful hive lookup by ID."""
    mock_hive_repository.get_by_id.return_value = sample_hive

    result = await hive_service.get_hive_by_id(1)

    assert isinstance(result, Hive)
    assert result.id == sample_hive.id
    assert result.user_id == sample_hive.user_id

    mock_hive_repository.get_by_id.assert_called_once_with(1)


async def test_get_hive_by_id_not_found(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
):
    """Test hive lookup when hive doesn't exist."""
    mock_hive_repository.get_by_id.return_value = None

    result = await hive_service.get_hive_by_id(999)

    assert result is None
    mock_hive_repository.get_by_id.assert_called_once_with(999)


async def test_get_hives_by_user_id_with_hives(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
    sample_hive: Hive,
):
    """Test getting hives for a user who has hives."""
    hives = [sample_hive]
    mock_hive_repository.get_by_user_id.return_value = hives

    result = await hive_service.get_hives_by_user_id(1)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == sample_hive

    mock_hive_repository.get_by_user_id.assert_called_once_with(1)


async def test_get_hives_by_user_id_no_hives(
    hive_service: HiveService,
    mock_hive_repository: AsyncMock,
):
    """Test getting hives for a user who has no hives."""
    mock_hive_repository.get_by_user_id.return_value = []

    result = await hive_service.get_hives_by_user_id(1)

    assert isinstance(result, list)
    assert len(result) == 0

    mock_hive_repository.get_by_user_id.assert_called_once_with(1)
