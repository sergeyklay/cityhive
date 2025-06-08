"""
User domain service.

Business logic for user operations including registration and management.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import User
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserRegistrationData:
    """Data class for user registration input."""

    name: str
    email: str


@dataclass
class UserRegistrationResult:
    """Result of user registration operation."""

    success: bool
    user: User | None = None
    error_message: str | None = None


class UserService:
    """Domain service for user-related business logic."""

    async def register_user(
        self, session: AsyncSession, registration_data: UserRegistrationData
    ) -> UserRegistrationResult:
        """
        Register a new user.

        Args:
            session: Database session
            registration_data: User registration information

        Returns:
            UserRegistrationResult with success status and user data or error
        """
        logger.info(
            "Starting user registration",
            email=registration_data.email,
            name=registration_data.name,
        )

        try:
            # Check if user already exists
            existing_user = await self._get_user_by_email(
                session, registration_data.email
            )
            if existing_user:
                logger.warning(
                    "Registration failed - user already exists",
                    email=registration_data.email,
                )
                return UserRegistrationResult(
                    success=False, error_message="User with this email already exists"
                )

            # Create new user with auto-generated API key
            user = User(
                name=registration_data.name,
                email=registration_data.email,
            )

            session.add(user)
            await session.commit()

            logger.info(
                "User registration successful",
                user_id=user.id,
                email=user.email,
                api_key=str(user.api_key),
            )

            return UserRegistrationResult(success=True, user=user)

        except IntegrityError as e:
            await session.rollback()
            logger.error(
                "Database integrity error during registration",
                email=registration_data.email,
                error=str(e),
            )
            return UserRegistrationResult(
                success=False, error_message="Registration failed due to data conflict"
            )

        except Exception as e:
            await session.rollback()
            logger.exception(
                "Unexpected error during user registration",
                email=registration_data.email,
                error_type=type(e).__name__,
            )
            return UserRegistrationResult(
                success=False, error_message="Internal server error during registration"
            )

    async def _get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> User | None:
        """Get user by email address."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
