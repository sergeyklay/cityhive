"""
Unit tests for UserRepository.

Tests the repository logic with mocked database operations.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import User
from cityhive.domain.user.exceptions import DuplicateUserError
from cityhive.domain.user.repository import UserRepository


@pytest.fixture
def mock_session():
    """Mock async database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    """User repository with mocked session."""
    return UserRepository(mock_session)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_user(sample_user_data):
    """Sample user model."""
    user = User(**sample_user_data)
    user.id = 1
    return user


async def test_save_user_with_valid_data_returns_user_with_id(
    user_repository: UserRepository,
    mock_session: AsyncMock,
    sample_user_data: dict,
):
    """Test successfully saving a user."""
    user = User(**sample_user_data)

    mock_session.add.return_value = None
    mock_session.flush.return_value = None

    def set_user_id():
        user.id = 1

    mock_session.flush.side_effect = set_user_id

    result = await user_repository.save(user)

    assert result is user
    assert result.id == 1
    mock_session.add.assert_called_once_with(user)
    mock_session.flush.assert_called_once()


async def test_save_user_with_duplicate_email_raises_duplicate_user_error(
    user_repository: UserRepository,
    mock_session: AsyncMock,
    sample_user_data: dict,
):
    """Test that saving a user with duplicate email raises DuplicateUserError."""
    user = User(**sample_user_data)

    integrity_error = IntegrityError("duplicate key", None, Exception("duplicate key"))
    mock_session.flush.side_effect = integrity_error

    with pytest.raises(DuplicateUserError) as exc_info:
        await user_repository.save(user)

    assert exc_info.value.email == sample_user_data["email"]
    mock_session.add.assert_called_once_with(user)
    mock_session.flush.assert_called_once()


async def test_get_by_email_with_existing_user_returns_user(
    user_repository: UserRepository,
    mock_session: AsyncMock,
    sample_user: User,
):
    """Test getting user by email when user exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_by_email("test@example.com")

    assert result is sample_user
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_email_with_nonexistent_user_returns_none(
    user_repository: UserRepository,
    mock_session: AsyncMock,
):
    """Test getting user by email when user doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_by_email("nonexistent@example.com")

    assert result is None
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_exists_by_email_with_existing_user_returns_true(
    user_repository: UserRepository,
    mock_session: AsyncMock,
    sample_user: User,
):
    """Test checking if user exists by email when user exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.exists_by_email("test@example.com")

    assert result is True
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_exists_by_email_with_nonexistent_user_returns_false(
    user_repository: UserRepository,
    mock_session: AsyncMock,
):
    """Test checking if user exists by email when user doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.exists_by_email("nonexistent@example.com")

    assert result is False
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_save_user_with_database_error_propagates_exception(
    user_repository: UserRepository,
    mock_session: AsyncMock,
    sample_user_data: dict,
):
    """Test that unexpected database errors are propagated."""
    user = User(**sample_user_data)

    database_error = RuntimeError("Database connection failed")
    mock_session.flush.side_effect = database_error

    with pytest.raises(RuntimeError, match="Database connection failed"):
        await user_repository.save(user)

    mock_session.add.assert_called_once_with(user)
    mock_session.flush.assert_called_once()
