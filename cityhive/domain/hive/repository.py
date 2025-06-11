"""
Hive repository.

Concrete repository implementation for hive data access.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import Hive, User
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class HiveRepository:
    """Concrete repository for hive data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, hive: Hive) -> Hive:
        """Save a hive to the repository."""

        try:
            self._session.add(hive)
            await self._session.flush()  # Get the ID without committing

            return hive

        except IntegrityError as e:
            logger.warning(
                "Hive save failed due to integrity constraint",
                user_id=hive.user_id,
                name=hive.name,
                error=str(e.orig) if hasattr(e, "orig") else str(e),
            )
            # Re-raise IntegrityError to be handled by service layer
            raise

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        return user

    async def get_by_id(self, hive_id: int) -> Hive | None:
        """Get hive by ID."""
        result = await self._session.execute(select(Hive).where(Hive.id == hive_id))
        hive = result.scalar_one_or_none()

        return hive

    async def get_by_user_id(self, user_id: int) -> list[Hive]:
        """Get all hives for a specific user."""
        result = await self._session.execute(
            select(Hive).where(Hive.user_id == user_id)
        )
        hives = result.scalars().all()

        return list(hives)
