"""
Hive domain service.

Business logic for hive operations including creation and management.
"""

from datetime import datetime, timezone

from geoalchemy2 import WKTElement
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cityhive.domain.hive.exceptions import InvalidLocationError, UserNotFoundError
from cityhive.domain.hive.repository import HiveRepository
from cityhive.domain.models import Hive
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class HiveCreationInput(BaseModel):
    """Input validation model for hive creation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int = Field(..., gt=0, description="ID of the user creating the hive")
    name: str = Field(..., min_length=1, max_length=100, description="Hive name")
    latitude: float | None = Field(
        None, ge=-90, le=90, description="Latitude coordinate"
    )
    longitude: float | None = Field(
        None, ge=-180, le=180, description="Longitude coordinate"
    )
    frame_type: str | None = Field(
        None, max_length=50, description="Type of frame used"
    )
    installed_at: datetime | None = Field(None, description="Installation timestamp")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates_together(cls, v, info):
        """Validate that both coordinates are provided together or both are None."""
        # This validator runs for each field individually,
        # so we need to check completeness in the service layer
        return v

    @field_validator("frame_type")
    @classmethod
    def validate_frame_type(cls, v):
        """Convert empty string to None for frame_type."""
        if v == "":
            return None
        return v


class HiveService:
    """Domain service for hive-related business logic."""

    def __init__(self, hive_repository: HiveRepository) -> None:
        """Initialize the hive service with its dependencies."""
        self._hive_repository = hive_repository

    async def create_hive(self, creation_input: HiveCreationInput) -> Hive:
        """
        Create a new hive.

        Args:
            creation_input: Validated hive creation data

        Returns:
            Hive model with complete hive information

        Raises:
            UserNotFoundError: If the specified user doesn't exist
            InvalidLocationError: If location coordinates are invalid
        """
        logger.info(
            "Starting hive creation",
            user_id=creation_input.user_id,
            name=creation_input.name,
            latitude=creation_input.latitude,
            longitude=creation_input.longitude,
        )

        # Verify user exists
        user = await self._hive_repository.get_user_by_id(creation_input.user_id)
        if not user:
            logger.warning(
                "Hive creation failed - user not found",
                user_id=creation_input.user_id,
            )
            raise UserNotFoundError(creation_input.user_id)

        # Validate coordinate completeness
        lat_provided = creation_input.latitude is not None
        lng_provided = creation_input.longitude is not None

        if lat_provided != lng_provided:
            missing_coord = "longitude" if lat_provided else "latitude"
            logger.warning(
                "Partial coordinates provided - both latitude and longitude required",
                latitude=creation_input.latitude,
                longitude=creation_input.longitude,
                missing=missing_coord,
            )
            raise InvalidLocationError(
                "Both latitude and longitude must be provided together. "
                f"Missing: {missing_coord}"
            )

        # Create location geometry if both coordinates provided
        location = None
        if lat_provided and lng_provided:
            try:
                # Create PostGIS POINT geometry from coordinates
                # SRID 4326 is WGS84 (GPS coordinates)
                location = WKTElement(
                    f"POINT({creation_input.longitude} {creation_input.latitude})",
                    srid=4326,
                )
            except Exception as e:
                logger.warning(
                    "Invalid location coordinates",
                    latitude=creation_input.latitude,
                    longitude=creation_input.longitude,
                    error=str(e),
                )
                raise InvalidLocationError("Invalid location coordinates") from e

        # Create new hive
        hive = Hive(
            user_id=creation_input.user_id,
            name=creation_input.name,
            location=location,
            frame_type=creation_input.frame_type,
            installed_at=creation_input.installed_at or datetime.now(timezone.utc),
        )

        # Save hive through repository
        try:
            saved_hive = await self._hive_repository.save(hive)
        except IntegrityError as e:
            logger.error(
                "Database integrity error during hive creation",
                user_id=creation_input.user_id,
                name=creation_input.name,
                error=str(e),
            )
            # Convert to domain exception
            raise InvalidLocationError(
                "Hive creation failed due to data conflict"
            ) from e

        logger.info(
            "Hive creation successful",
            hive_id=saved_hive.id,
            user_id=saved_hive.user_id,
            name=saved_hive.name,
            has_location=location is not None,
        )

        return saved_hive

    async def get_hive_by_id(self, hive_id: int) -> Hive | None:
        """
        Get hive by ID.

        Args:
            hive_id: Hive ID

        Returns:
            Hive model if found, None otherwise
        """
        logger.debug("Looking up hive by ID", hive_id=hive_id)

        hive = await self._hive_repository.get_by_id(hive_id)
        if not hive:
            logger.debug("Hive not found", hive_id=hive_id)
            return None

        logger.debug("Hive found", hive_id=hive_id, user_id=hive.user_id)
        return hive

    async def get_hives_by_user_id(self, user_id: int) -> list[Hive]:
        """
        Get all hives for a specific user.

        Args:
            user_id: User ID

        Returns:
            List of hives owned by the user
        """
        logger.debug("Looking up hives for user", user_id=user_id)

        hives = await self._hive_repository.get_by_user_id(user_id)
        logger.debug("User hives found", user_id=user_id, hive_count=len(hives))
        return hives


class HiveServiceFactory:
    """Factory for creating HiveService instances with proper session management."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize the factory with a session factory."""
        self._session_factory = session_factory

    def create_service(self, session: AsyncSession) -> HiveService:
        """
        Create a HiveService instance with a repository using the provided session.

        Args:
            session: Database session for the service

        Returns:
            HiveService instance configured with HiveRepository
        """
        hive_repository = HiveRepository(session)
        return HiveService(hive_repository)
