"""
Hive API views for JSON responses.

These views handle hive-related REST API endpoints and return JSON responses.
All API views follow REST conventions and proper HTTP status codes.
"""

from datetime import datetime

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.app.helpers.validation import (
    sanitize_numeric_field,
    sanitize_string_field,
    validate_coordinates,
    validate_required_field,
)
from cityhive.domain.services.hive import (
    HiveCreationData,
    HiveCreationErrorType,
    HiveService,
)
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


def _validate_and_parse_hive_data(
    data: dict,
) -> tuple[HiveCreationData | None, web.Response | None]:
    """
    Validate and parse hive creation data.

    Returns:
        Tuple of (HiveCreationData, None) on success
        or (None, error_response) on failure
    """
    # Extract and sanitize input fields
    user_id = data.get("user_id")
    name = sanitize_string_field(data.get("name"))
    latitude = sanitize_numeric_field(data.get("latitude"))
    longitude = sanitize_numeric_field(data.get("longitude"))
    frame_type = sanitize_string_field(data.get("frame_type"))
    installed_at_str = sanitize_string_field(data.get("installed_at"))

    # Validate required fields
    if user_id is None:
        return None, create_error_response("User ID is required", 400)

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None, create_error_response("User ID must be a valid integer", 400)

    name_validation = validate_required_field(name, "Name")
    if not name_validation.is_valid:
        return None, create_error_response(
            name_validation.error_message or "Name validation failed", 400
        )

    # Validate coordinates if provided
    coordinates_validation = validate_coordinates(latitude, longitude)
    if not coordinates_validation.is_valid:
        return None, create_error_response(
            coordinates_validation.error_message or "Coordinate validation failed", 400
        )

    # Parse installation date if provided
    installed_at = None
    if installed_at_str:
        try:
            installed_at = datetime.fromisoformat(
                installed_at_str.replace("Z", "+00:00")
            )
        except ValueError:
            return None, create_error_response(
                "Invalid installation date format. Use ISO 8601 format", 400
            )

    # Set frame_type to None if empty string
    if frame_type == "":
        frame_type = None

    # Create hive data
    creation_data = HiveCreationData(
        user_id=user_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        frame_type=frame_type,
        installed_at=installed_at,
    )

    return creation_data, None


def _handle_hive_creation_error(result, creation_data) -> web.Response:
    """Handle hive creation error and return appropriate response."""
    # Determine appropriate HTTP status code based on structured error type
    status_code = 400  # Default to client error
    if result.error_type == HiveCreationErrorType.USER_NOT_FOUND:
        status_code = 404
    elif result.error_type == HiveCreationErrorType.INTEGRITY_VIOLATION:
        status_code = 409  # Conflict - client caused integrity violation
    elif result.error_type in (
        HiveCreationErrorType.DATABASE_ERROR,
        HiveCreationErrorType.UNKNOWN_ERROR,
    ):
        status_code = 500

    logger.warning(
        "Hive creation failed",
        user_id=creation_data.user_id,
        name=creation_data.name,
        error_type=result.error_type.value if result.error_type else None,
        error=result.error_message,
    )

    return create_error_response(
        result.error_message or "Hive creation failed", status_code
    )


async def create_hive(request: web.Request) -> web.Response:
    """
    Create a new hive.

    Expected JSON payload:
    {
        "user_id": 1,
        "name": "Hive Alpha",
        "latitude": 40.7128,         // Optional
        "longitude": -74.0060,       // Optional
        "frame_type": "Langstroth",  // Optional
        "installed_at": "2024-01-15T10:30:00Z"  // Optional, ISO format
    }

    Returns:
    - 201: Hive created successfully
    - 400: Invalid request data
    - 404: User not found
    - 500: Internal server error
    """
    try:
        # Parse JSON request with proper error handling
        data, parse_error = await parse_json_request(request)
        if parse_error:
            return create_error_response(parse_error, 400)

        # Ensure data is not None after successful parsing
        if data is None:
            return create_error_response("Invalid JSON data", 400)

        # Validate and parse hive data
        creation_data, validation_error = _validate_and_parse_hive_data(data)
        if validation_error:
            return validation_error

        # Ensure creation_data is not None (defensive programming)
        if creation_data is None:
            return create_error_response("Failed to process hive data", 500)

        # Create hive through domain service
        async with request.app[db_key]() as session:
            session: AsyncSession
            hive_service = HiveService()
            result = await hive_service.create_hive(session, creation_data)

            if result.success and result.hive:
                logger.info(
                    "Hive creation API success",
                    hive_id=result.hive.id,
                    user_id=result.hive.user_id,
                    name=result.hive.name,
                )

                # Build response data with location coordinates if available
                hive_data = {
                    "id": result.hive.id,
                    "user_id": result.hive.user_id,
                    "name": result.hive.name,
                    "frame_type": result.hive.frame_type,
                    "installed_at": result.hive.installed_at.isoformat()
                    if result.hive.installed_at
                    else None,
                }

                # Add location data if available
                if result.hive.location:
                    # Extract coordinates from creation data
                    hive_data["location"] = {
                        "latitude": creation_data.latitude,
                        "longitude": creation_data.longitude,
                    }
                else:
                    hive_data["location"] = None

                return create_success_response(
                    {"hive": hive_data},
                    status=201,
                )

            return _handle_hive_creation_error(result, creation_data)

    except Exception:
        logger.exception("Unexpected error in hive creation API")
        return create_error_response("Internal server error", 500)
