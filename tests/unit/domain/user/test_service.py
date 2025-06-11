"""
Unit tests for UserService.

Tests demonstrate improved testability with dependency injection and mocking.
"""

from unittest.mock import AsyncMock

import pytest

from cityhive.domain.models import User
from cityhive.domain.user.exceptions import DuplicateUserError
from cityhive.domain.user.repository import UserRepository
from cityhive.domain.user.service import UserRegistrationInput, UserService


@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing."""
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repository):
    """User service with mocked dependencies."""
    return UserService(mock_user_repository)


@pytest.fixture
def valid_registration_input():
    """Valid user registration input."""
    return UserRegistrationInput(
        name="John Doe",
        email="john.doe@example.com",
    )


@pytest.fixture
def sample_user():
    """Sample user model."""
    user = User(name="John Doe", email="john.doe@example.com")
    user.id = 1
    return user


async def test_register_user_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    valid_registration_input: UserRegistrationInput,
    sample_user: User,
):
    """Test successful user registration."""
    mock_user_repository.exists_by_email.return_value = False
    mock_user_repository.save.return_value = sample_user

    result = await user_service.register_user(valid_registration_input)

    assert isinstance(result, User)
    assert result.id == sample_user.id
    assert result.name == sample_user.name
    assert result.email == sample_user.email
    assert result.api_key == sample_user.api_key

    mock_user_repository.exists_by_email.assert_called_once_with(
        valid_registration_input.email
    )
    mock_user_repository.save.assert_called_once()


async def test_register_user_duplicate_email(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    valid_registration_input: UserRegistrationInput,
):
    """Test registration with duplicate email raises exception."""
    mock_user_repository.exists_by_email.return_value = True

    with pytest.raises(DuplicateUserError) as exc_info:
        await user_service.register_user(valid_registration_input)

    assert exc_info.value.email == valid_registration_input.email

    mock_user_repository.exists_by_email.assert_called_once_with(
        valid_registration_input.email
    )
    mock_user_repository.save.assert_not_called()


async def test_register_user_repository_error_propagated(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    valid_registration_input: UserRegistrationInput,
):
    """Test that repository errors are properly propagated."""
    mock_user_repository.exists_by_email.return_value = False
    mock_user_repository.save.side_effect = DuplicateUserError(
        valid_registration_input.email
    )

    with pytest.raises(DuplicateUserError):
        await user_service.register_user(valid_registration_input)


async def test_get_user_by_email_found(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    sample_user: User,
):
    """Test successful user lookup by email."""
    mock_user_repository.get_by_email.return_value = sample_user

    result = await user_service.get_user_by_email(sample_user.email)

    assert isinstance(result, User)
    assert result.id == sample_user.id
    assert result.email == sample_user.email

    mock_user_repository.get_by_email.assert_called_once_with(sample_user.email)


async def test_get_user_by_email_not_found(
    user_service: UserService,
    mock_user_repository: AsyncMock,
):
    """Test user lookup when user doesn't exist."""
    email = "nonexistent@example.com"
    mock_user_repository.get_by_email.return_value = None

    result = await user_service.get_user_by_email(email)

    assert result is None
    mock_user_repository.get_by_email.assert_called_once_with(email)
