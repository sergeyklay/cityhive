"""
User repository.

Concrete repository implementation for user data access.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import User
from cityhive.domain.user.exceptions import DuplicateUserError
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Concrete repository for user data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        logger.debug("Querying user by email", email=email)

        result = await self._session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        logger.debug(
            "User query completed",
            email=email,
            found=user is not None,
            user_id=user.id if user else None,
        )
        return user

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        user = await self.get_by_email(email)
        return user is not None

    async def save(self, user: User) -> User:
        """Save a user to the repository."""
        logger.debug(
            "Saving user",
            user_id=getattr(user, "id", None),
            email=user.email,
            is_new=user.id is None,
        )

        try:
            self._session.add(user)
            await self._session.flush()  # Get the ID without committing

            logger.debug(
                "User saved successfully",
                user_id=user.id,
                email=user.email,
            )
            return user

        except IntegrityError as e:
            logger.warning(
                "User save failed due to integrity constraint",
                email=user.email,
                error=str(e.orig) if hasattr(e, "orig") else str(e),
            )
            # Convert SQLAlchemy exception to domain exception
            raise DuplicateUserError(user.email) from e
