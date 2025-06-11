"""
Inspection repository.

Concrete repository implementation for inspection data access.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import Hive, Inspection
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class InspectionRepository:
    """Concrete repository for inspection data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, inspection: Inspection) -> Inspection:
        """Save an inspection to the repository."""

        try:
            self._session.add(inspection)
            await self._session.flush()  # Get the ID without committing

            return inspection

        except IntegrityError as e:
            logger.warning(
                "Inspection save failed due to integrity constraint",
                hive_id=inspection.hive_id,
                scheduled_for=inspection.scheduled_for.isoformat(),
                error=str(e.orig) if hasattr(e, "orig") else str(e),
            )
            # Re-raise IntegrityError to be handled by service layer
            raise

    async def get_hive_by_id(self, hive_id: int) -> Hive | None:
        """Get hive by ID."""
        result = await self._session.execute(select(Hive).where(Hive.id == hive_id))
        hive = result.scalar_one_or_none()

        return hive

    async def get_by_id(self, inspection_id: int) -> Inspection | None:
        """Get inspection by ID."""
        result = await self._session.execute(
            select(Inspection).where(Inspection.id == inspection_id)
        )
        inspection = result.scalar_one_or_none()

        return inspection

    async def get_by_hive_id(self, hive_id: int) -> list[Inspection]:
        """Get all inspections for a specific hive."""
        result = await self._session.execute(
            select(Inspection).where(Inspection.hive_id == hive_id)
        )
        inspections = result.scalars().all()

        return list(inspections)
