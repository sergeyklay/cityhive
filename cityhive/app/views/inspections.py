"""
Inspection API views for JSON responses.

These views handle inspection-related REST API endpoints and return JSON responses.
All API views follow REST conventions and proper HTTP status codes.
"""

from aiohttp import web
from pydantic import ValidationError

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.domain.inspection import (
    HiveNotFoundError,
    InspectionCreationInput,
    InvalidScheduleError,
)
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key, inspection_service_factory_key

logger = get_logger(__name__)


async def create_inspection(request: web.Request) -> web.Response:
    """
    Create a new inspection.

    Expected JSON payload:
    {
        "hive_id": 42,
        "scheduled_for": "2025-06-15",
        "notes": "Check the condition of the wax and add a new frame"
    }

    Returns:
    - 201: Inspection created successfully
    - 400: Invalid request data or validation errors
    - 404: Hive not found
    - 500: Internal server error
    """
    try:
        data, parse_error = await parse_json_request(request)
        if parse_error:
            return create_error_response(parse_error, 400)

        if data is None:
            return create_error_response("Invalid JSON data", 400)

        try:
            creation_input = InspectionCreationInput(**data)
        except ValidationError as e:
            logger.warning(
                "Inspection creation validation failed",
                errors=e.errors(),
                data=data,
            )
            return create_error_response("Invalid input data", 400)

        async with request.app[db_key]() as session:
            try:
                inspection_service_factory = request.app[inspection_service_factory_key]
                inspection_service = inspection_service_factory.create_service(session)
                inspection = await inspection_service.create_inspection(creation_input)

                await session.commit()

                logger.info(
                    "Inspection creation API success",
                    inspection_id=inspection.id,
                    hive_id=inspection.hive_id,
                    scheduled_for=inspection.scheduled_for.isoformat(),
                )

                # Build response data
                inspection_data = {
                    "id": inspection.id,
                    "hive_id": inspection.hive_id,
                    "scheduled_for": inspection.scheduled_for.isoformat(),
                    "notes": inspection.notes,
                    "created_at": inspection.created_at.isoformat(),
                }

                return create_success_response(
                    inspection_data,
                    status=201,
                )

            except HiveNotFoundError as e:
                await session.rollback()
                logger.warning(
                    "Inspection creation failed - hive not found",
                    hive_id=e.hive_id,
                )
                return create_error_response("Hive not found", 404)

            except InvalidScheduleError as e:
                await session.rollback()
                logger.warning(
                    "Inspection creation failed - invalid schedule",
                    error=e.message,
                )
                return create_error_response(e.message, 400)

            except Exception as e:
                await session.rollback()
                logger.exception(
                    "Unexpected error during inspection creation",
                    hive_id=creation_input.hive_id,
                    error_type=type(e).__name__,
                )
                return create_error_response("Internal server error", 500)

    except Exception:
        logger.exception("Unexpected error in inspection creation API")
        return create_error_response("Internal server error", 500)
