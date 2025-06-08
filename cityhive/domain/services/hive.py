"""
Hive domain service.

Business logic for hive operations including creation and management.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.models import Hive, User
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


class HiveCreationErrorType(Enum):
    """Enumeration of hive creation error types."""

    USER_NOT_FOUND = "user_not_found"
    INVALID_LOCATION = "invalid_location"
    DATABASE_ERROR = "database_error"
    INTEGRITY_VIOLATION = "integrity_violation"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class HiveCreationData:
    """Data class for hive creation input."""

    user_id: int
    name: str
    latitude: float | None = None
    longitude: float | None = None
    frame_type: str | None = None
    installed_at: datetime | None = None


@dataclass
class HiveCreationResult:
    """Result of hive creation operation."""

    success: bool
    hive: Hive | None = None
    error_type: HiveCreationErrorType | None = None
    error_message: str | None = None


class HiveService:
    """Domain service for hive-related business logic."""

    async def create_hive(
        self, session: AsyncSession, creation_data: HiveCreationData
    ) -> HiveCreationResult:
        """
        Create a new hive.

        Args:
            session: Database session
            creation_data: Hive creation information

        Returns:
            HiveCreationResult with success status and hive data or structured error
        """
        logger.info(
            "Starting hive creation",
            user_id=creation_data.user_id,
            name=creation_data.name,
            latitude=creation_data.latitude,
            longitude=creation_data.longitude,
        )

        try:
            # Verify user exists
            user = await self._get_user_by_id(session, creation_data.user_id)
            if not user:
                logger.warning(
                    "Hive creation failed - user not found",
                    user_id=creation_data.user_id,
                )
                return HiveCreationResult(
                    success=False,
                    error_type=HiveCreationErrorType.USER_NOT_FOUND,
                    error_message="User not found",
                )

            # Validate coordinate completeness - both or neither must be provided
            lat_provided = creation_data.latitude is not None
            lng_provided = creation_data.longitude is not None

            if lat_provided != lng_provided:
                # Exactly one coordinate provided - this is invalid
                missing_coord = "longitude" if lat_provided else "latitude"
                logger.warning(
                    (
                        "Partial coordinates provided - both latitude and longitude "
                        "required"
                    ),
                    latitude=creation_data.latitude,
                    longitude=creation_data.longitude,
                    missing=missing_coord,
                )
                return HiveCreationResult(
                    success=False,
                    error_type=HiveCreationErrorType.INVALID_LOCATION,
                    error_message=(
                        "Both latitude and longitude must be provided together. "
                        f"Missing: {missing_coord}"
                    ),
                )

            # Create location geometry if both coordinates provided
            location = None
            if lat_provided and lng_provided:
                try:
                    # Create PostGIS POINT geometry from coordinates
                    # SRID 4326 is WGS84 (GPS coordinates)
                    location = WKTElement(
                        f"POINT({creation_data.longitude} {creation_data.latitude})",
                        srid=4326,
                    )
                except Exception as e:
                    logger.warning(
                        "Invalid location coordinates",
                        latitude=creation_data.latitude,
                        longitude=creation_data.longitude,
                        error=str(e),
                    )
                    return HiveCreationResult(
                        success=False,
                        error_type=HiveCreationErrorType.INVALID_LOCATION,
                        error_message="Invalid location coordinates",
                    )

            # Create new hive
            hive = Hive(
                user_id=creation_data.user_id,
                name=creation_data.name,
                location=location,
                frame_type=creation_data.frame_type,
                installed_at=creation_data.installed_at or datetime.now(timezone.utc),
            )

            session.add(hive)
            await session.commit()

            logger.info(
                "Hive creation successful",
                hive_id=hive.id,
                user_id=hive.user_id,
                name=hive.name,
                has_location=location is not None,
            )

            return HiveCreationResult(success=True, hive=hive)

        except IntegrityError as e:
            await session.rollback()
            logger.error(
                "Database integrity error during hive creation",
                user_id=creation_data.user_id,
                name=creation_data.name,
                error=str(e),
            )
            return HiveCreationResult(
                success=False,
                error_type=HiveCreationErrorType.INTEGRITY_VIOLATION,
                error_message="Hive creation failed due to data conflict",
            )

        except Exception as e:
            await session.rollback()
            logger.exception(
                "Unexpected error during hive creation",
                user_id=creation_data.user_id,
                name=creation_data.name,
                error_type=type(e).__name__,
            )
            return HiveCreationResult(
                success=False,
                error_type=HiveCreationErrorType.UNKNOWN_ERROR,
                error_message="Internal server error during hive creation",
            )

    async def _get_user_by_id(self, session: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
