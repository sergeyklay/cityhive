"""
Unit tests for HiveRepository.

Tests the repository logic with mocked database operations.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.hive.repository import HiveRepository
from cityhive.domain.models import Hive, User


@pytest.fixture
def mock_session():
    """Mock async database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def hive_repository(mock_session):
    """Hive repository with mocked session."""
    return HiveRepository(mock_session)


@pytest.fixture
def sample_hive_data():
    """Sample hive data for testing."""
    return {
        "user_id": 1,
        "name": "Test Hive",
        "frame_type": "Langstroth",
    }


@pytest.fixture
def sample_hive(sample_hive_data):
    """Sample hive model."""
    hive = Hive(**sample_hive_data)
    hive.id = 1
    return hive


@pytest.fixture
def sample_user():
    """Sample user model."""
    user = User(name="Test User", email="test@example.com")
    user.id = 1
    return user


async def test_save_hive_with_valid_data_returns_hive_with_id(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
    sample_hive_data: dict,
):
    """Test successfully saving a hive."""
    hive = Hive(**sample_hive_data)

    mock_session.add.return_value = None
    mock_session.flush.return_value = None

    def set_hive_id():
        hive.id = 1

    mock_session.flush.side_effect = set_hive_id

    result = await hive_repository.save(hive)

    assert result is hive
    assert result.id == 1
    mock_session.add.assert_called_once_with(hive)
    mock_session.flush.assert_called_once()


async def test_save_hive_with_integrity_error_raises_exception(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
    sample_hive_data: dict,
):
    """Test that saving a hive with integrity constraint raises IntegrityError."""
    hive = Hive(**sample_hive_data)

    integrity_error = IntegrityError(
        "integrity constraint", None, Exception("constraint violation")
    )
    mock_session.flush.side_effect = integrity_error

    with pytest.raises(IntegrityError):
        await hive_repository.save(hive)

    mock_session.add.assert_called_once_with(hive)
    mock_session.flush.assert_called_once()


async def test_get_user_by_id_with_existing_user_returns_user(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
    sample_user: User,
):
    """Test getting user by ID when user exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_user_by_id(1)

    assert result is sample_user
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_user_by_id_with_nonexistent_user_returns_none(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
):
    """Test getting user by ID when user doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_user_by_id(999)

    assert result is None
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_id_with_existing_hive_returns_hive(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
    sample_hive: Hive,
):
    """Test getting hive by ID when hive exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_hive
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_by_id(1)

    assert result is sample_hive
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_id_with_nonexistent_hive_returns_none(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
):
    """Test getting hive by ID when hive doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_by_id(999)

    assert result is None
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_user_id_returns_list_of_hives(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
    sample_hive: Hive,
):
    """Test getting hives by user ID."""
    hives = [sample_hive]
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = hives
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_by_user_id(1)

    assert result == hives
    assert isinstance(result, list)
    mock_session.execute.assert_called_once()
    mock_result.scalars.assert_called_once()
    mock_scalars.all.assert_called_once()


async def test_get_by_user_id_with_no_hives_returns_empty_list(
    hive_repository: HiveRepository,
    mock_session: AsyncMock,
):
    """Test getting hives by user ID when user has no hives."""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await hive_repository.get_by_user_id(1)

    assert result == []
    assert isinstance(result, list)
    mock_session.execute.assert_called_once()
    mock_result.scalars.assert_called_once()
    mock_scalars.all.assert_called_once()
