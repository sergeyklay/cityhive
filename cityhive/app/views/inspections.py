"""
Inspection API views for JSON responses.

These views handle inspection-related REST API endpoints and return JSON responses.
All API views follow REST conventions and proper HTTP status codes.
"""

from typing import Any, Awaitable, Callable

from aiohttp import web
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.domain.inspection import (
    DatabaseConflictError,
    HiveNotFoundError,
    InspectionCreationInput,
    InvalidScheduleError,
)
from cityhive.domain.models import Inspection
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key, inspection_service_factory_key

logger = get_logger(__name__)


async def _parse_and_validate(
    request: web.Request,
) -> InspectionCreationInput | web.Response:
    """
    Parse and validate JSON request data for inspection creation.

    Args:
        request: The HTTP request object containing the JSON data

    Returns:
        A validated InspectionCreationInput object or a web.Response error
    """
    data, parse_error = await parse_json_request(request)
    if parse_error:
        return create_error_response(parse_error, 400)

    if data is None:
        return create_error_response("Invalid JSON data", 400)

    try:
        return InspectionCreationInput(**data)
    except ValidationError as e:
        logger.warning(
            "Inspection creation validation failed",
            errors=e.errors(),
            data=data,
        )
        return create_error_response("Invalid input data", 400)


async def _handle_domain_errors(
    session: AsyncSession, func: Callable[[], Awaitable[Any]]
) -> Any | web.Response:
    """
    Execute domain logic function and map domain exceptions to HTTP responses.

    Args:
        session: The database session
        func: The domain logic function to execute

    Returns:
        The function result or a web.Response error
    """
    # Error mapping for domain exceptions
    error_mapping = {
        HiveNotFoundError: (404, "Hive not found"),
        InvalidScheduleError: (400, lambda e: e.message),
        DatabaseConflictError: (
            409,
            "Database constraint violation - operation conflicts with existing data",
        ),
    }

    try:
        return await func()
    except tuple(error_mapping.keys()) as e:
        await session.rollback()

        status, message = error_mapping[type(e)]
        if callable(message):
            message = message(e)

        if isinstance(e, HiveNotFoundError):
            logger.warning(
                "Inspection creation failed - hive not found", hive_id=e.hive_id
            )
        elif isinstance(e, InvalidScheduleError):
            logger.warning(
                "Inspection creation failed - invalid schedule", error=e.message
            )
        elif isinstance(e, DatabaseConflictError):
            logger.warning(
                "Inspection creation failed - database constraint violation",
                error_type=type(e.original_error).__name__,
                original_error=str(e.original_error),
            )

        return create_error_response(message, status)
    except Exception as e:
        await session.rollback()
        logger.exception(
            "Unexpected error during inspection creation",
            error_type=type(e).__name__,
        )
        return create_error_response("Internal server error", 500)


async def create_inspection(request: web.Request) -> web.Response:
    """
    Create a new inspection.

    Args:
        request: The HTTP request object containing the JSON data

    Returns:
        A web.Response object with the appropriate status code and error message
    """
    try:
        validation_result = await _parse_and_validate(request)
        if isinstance(validation_result, web.Response):
            return validation_result
        creation_input = validation_result
        async with request.app[db_key]() as session:

            async def domain_operation() -> Inspection:
                inspection_service_factory = request.app[inspection_service_factory_key]
                inspection_service = inspection_service_factory.create_service(session)
                inspection = await inspection_service.create_inspection(creation_input)
                await session.commit()
                return inspection

            result = await _handle_domain_errors(session, domain_operation)
            if isinstance(result, web.Response):
                return result

            logger.info(
                "Inspection creation API success",
                inspection_id=result.id,
                hive_id=result.hive_id,
                scheduled_for=result.scheduled_for.isoformat(),
            )
            return create_success_response(
                {
                    "id": result.id,
                    "hive_id": result.hive_id,
                    "scheduled_for": result.scheduled_for.isoformat(),
                    "notes": result.notes,
                    "created_at": result.created_at.isoformat(),
                },
                status=201,
            )
    except Exception:
        logger.exception("Unexpected error in inspection creation API")
        return create_error_response("Internal server error", 500)
