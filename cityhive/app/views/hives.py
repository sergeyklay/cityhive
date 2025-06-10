"""
Hive API views for JSON responses.

These views handle hive-related REST API endpoints and return JSON responses.
All API views follow REST conventions and proper HTTP status codes.
"""

from aiohttp import web
from pydantic import ValidationError

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.domain.hive import (
    HiveCreationInput,
    InvalidLocationError,
    UserNotFoundError,
)
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key, hive_service_factory_key

logger = get_logger(__name__)


async def create_hive(request: web.Request) -> web.Response:
    """
    Create a new hive.

    Expected JSON payload:
    {
        "user_id": 1,
        "name": "Hive Alpha",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "frame_type": "Langstroth",
        "installed_at": "2024-01-15T10:30:00Z"
    }

    Returns:
    - 201: Hive created successfully
    - 400: Invalid request data or validation errors
    - 404: User not found
    - 500: Internal server error
    """
    try:
        data, parse_error = await parse_json_request(request)
        if parse_error:
            return create_error_response(parse_error, 400)

        if data is None:
            return create_error_response("Invalid JSON data", 400)

        try:
            creation_input = HiveCreationInput(**data)
        except ValidationError as e:
            logger.warning(
                "Hive creation validation failed",
                errors=e.errors(),
                data=data,
            )
            return create_error_response("Invalid input data", 400)

        async with request.app[db_key]() as session:
            try:
                hive_service_factory = request.app[hive_service_factory_key]
                hive_service = hive_service_factory.create_service(session)
                hive = await hive_service.create_hive(creation_input)

                await session.commit()

                logger.info(
                    "Hive creation API success",
                    hive_id=hive.id,
                    user_id=hive.user_id,
                    name=hive.name,
                )

                # Build response data with location coordinates if available
                hive_data = {
                    "id": hive.id,
                    "user_id": hive.user_id,
                    "name": hive.name,
                    "frame_type": hive.frame_type,
                    "installed_at": hive.installed_at.isoformat()
                    if hive.installed_at
                    else None,
                }

                # Add location data if available
                if hive.location:
                    # Extract coordinates from creation input
                    hive_data["location"] = {
                        "latitude": creation_input.latitude,
                        "longitude": creation_input.longitude,
                    }
                else:
                    hive_data["location"] = None

                return create_success_response(
                    {"hive": hive_data},
                    status=201,
                )

            except UserNotFoundError as e:
                await session.rollback()
                logger.warning(
                    "Hive creation failed - user not found",
                    user_id=e.user_id,
                )
                return create_error_response("User not found", 404)

            except InvalidLocationError as e:
                await session.rollback()
                logger.warning(
                    "Hive creation failed - invalid location",
                    error=e.message,
                )
                return create_error_response(e.message, 400)

            except Exception as e:
                await session.rollback()
                logger.exception(
                    "Unexpected error during hive creation",
                    user_id=creation_input.user_id,
                    error_type=type(e).__name__,
                )
                return create_error_response("Internal server error", 500)

    except Exception:
        logger.exception("Unexpected error in hive creation API")
        return create_error_response("Internal server error", 500)
