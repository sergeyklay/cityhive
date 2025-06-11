"""
User domain service.

Business logic for user operations including registration and management.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cityhive.domain.models import User
from cityhive.domain.user.exceptions import DuplicateUserError
from cityhive.domain.user.repository import UserRepository
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class UserRegistrationInput(BaseModel):
    """Input validation model for user registration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")


class UserService:
    """Domain service for user-related business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize the user service with its dependencies."""
        self._user_repository = user_repository

    async def register_user(self, registration_input: UserRegistrationInput) -> User:
        """
        Register a new user.

        Args:
            registration_input: Validated user registration data

        Returns:
            User model with complete user information

        Raises:
            DuplicateUserError: If user with email already exists
        """
        logger.info(
            "Starting user registration",
            email=registration_input.email,
            name=registration_input.name,
        )

        # Check if user already exists
        if await self._user_repository.exists_by_email(registration_input.email):
            logger.warning(
                "Registration failed - user already exists",
                email=registration_input.email,
            )
            raise DuplicateUserError(registration_input.email)

        # Create new user with auto-generated API key
        user = User(
            name=registration_input.name,
            email=registration_input.email,
        )

        # Save user through repository
        saved_user = await self._user_repository.save(user)

        logger.info(
            "User registration successful",
            user_id=saved_user.id,
            email=saved_user.email,
            api_key=str(saved_user.api_key),
        )

        return saved_user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User model if found, None otherwise
        """
        user = await self._user_repository.get_by_email(email)
        if not user:
            return None

        return user


class UserServiceFactory:
    """Factory for creating UserService instances with proper session management."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize the factory with a session factory."""
        self._session_factory = session_factory

    def create_service(self, session: AsyncSession) -> UserService:
        """
        Create a UserService instance with a repository using the provided session.

        Args:
            session: Database session for the service

        Returns:
            UserService instance configured with UserRepository
        """
        user_repository = UserRepository(session)
        return UserService(user_repository)
