"""
Inspection domain service.

Business logic for inspection operations including creation and management.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.inspection.exceptions import (
    HiveNotFoundError,
    InvalidScheduleError,
)
from cityhive.domain.inspection.repository import InspectionRepository
from cityhive.domain.models import Inspection
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class InspectionCreationInput(BaseModel):
    """Input validation model for inspection creation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    hive_id: int = Field(..., gt=0, description="ID of the hive to inspect")
    scheduled_for: date = Field(..., description="Date when inspection is scheduled")
    notes: str | None = Field(
        None, max_length=1000, description="Optional inspection notes"
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v):
        """Convert empty string to None for notes."""
        if v == "":
            return None
        return v

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, v):
        """Validate that scheduled_for is not in the past."""
        if v < date.today():
            raise ValueError("Scheduled date cannot be in the past")
        return v


class InspectionService:
    """Domain service for inspection-related business logic."""

    def __init__(self, inspection_repository: InspectionRepository) -> None:
        """Initialize the inspection service with its dependencies."""
        self._inspection_repository = inspection_repository

    async def create_inspection(
        self, creation_input: InspectionCreationInput
    ) -> Inspection:
        """
        Create a new inspection.

        Args:
            creation_input: Validated inspection creation data

        Returns:
            Inspection model with complete inspection information

        Raises:
            HiveNotFoundError: If the specified hive doesn't exist
            InvalidScheduleError: If the schedule date is invalid
        """
        logger.info(
            "Starting inspection creation",
            hive_id=creation_input.hive_id,
            scheduled_for=creation_input.scheduled_for.isoformat(),
            has_notes=creation_input.notes is not None,
        )

        # Verify hive exists
        hive = await self._inspection_repository.get_hive_by_id(creation_input.hive_id)
        if not hive:
            logger.warning(
                "Inspection creation failed - hive not found",
                hive_id=creation_input.hive_id,
            )
            raise HiveNotFoundError(creation_input.hive_id)

        # Additional validation - ensure not scheduling too far in the future
        today = date.today()
        if (creation_input.scheduled_for - today).days > 365:
            logger.warning(
                "Inspection scheduled too far in the future",
                hive_id=creation_input.hive_id,
                scheduled_for=creation_input.scheduled_for.isoformat(),
                days_ahead=(creation_input.scheduled_for - today).days,
            )
            raise InvalidScheduleError(
                "Inspection cannot be scheduled more than 1 year in advance"
            )

        # Create new inspection
        inspection = Inspection(
            hive_id=creation_input.hive_id,
            scheduled_for=creation_input.scheduled_for,
            notes=creation_input.notes,
        )

        # Save inspection through repository
        try:
            saved_inspection = await self._inspection_repository.save(inspection)
        except IntegrityError as e:
            logger.error(
                "Database integrity error during inspection creation",
                hive_id=creation_input.hive_id,
                scheduled_for=creation_input.scheduled_for.isoformat(),
                error=str(e),
            )
            # Convert to domain exception
            raise InvalidScheduleError(
                "Inspection creation failed due to data conflict"
            ) from e

        # TODO: Schedule notification for upcoming inspection
        # This is a stub as requested - would integrate with notification service
        await self._schedule_inspection_notification(saved_inspection)

        logger.info(
            "Inspection creation successful",
            inspection_id=saved_inspection.id,
            hive_id=saved_inspection.hive_id,
            scheduled_for=saved_inspection.scheduled_for.isoformat(),
        )

        return saved_inspection

    async def _schedule_inspection_notification(self, inspection: Inspection) -> None:
        """
        Schedule notification for inspection reminder.

        TODO: Implement actual notification scheduling logic.
        This is a stub for future notification system integration.
        """
        # Future implementation would:
        # 1. Calculate reminder date (e.g., 1 day before)
        # 2. Schedule background task with aiocron or similar
        # 3. Send email/SMS/push notification when due

    async def get_inspection_by_id(self, inspection_id: int) -> Inspection | None:
        """
        Get inspection by ID.

        Args:
            inspection_id: Inspection ID

        Returns:
            Inspection model if found, None otherwise
        """
        inspection = await self._inspection_repository.get_by_id(inspection_id)
        if not inspection:
            return None

        return inspection

    async def get_inspections_by_hive_id(self, hive_id: int) -> list[Inspection]:
        """
        Get all inspections for a specific hive.

        Args:
            hive_id: Hive ID

        Returns:
            List of inspections for the hive
        """
        inspections = await self._inspection_repository.get_by_hive_id(hive_id)

        return inspections


class InspectionServiceFactory:
    """Factory for creating InspectionService instances with session management."""

    def create_service(self, session: AsyncSession) -> InspectionService:
        """
        Create an InspectionService instance with a repository.

        Args:
            session: Database session for the service

        Returns:
            InspectionService instance configured with InspectionRepository
        """
        inspection_repository = InspectionRepository(session)
        return InspectionService(inspection_repository)
