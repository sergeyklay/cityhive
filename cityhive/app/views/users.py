"""
API views for JSON responses.

These views handle REST API endpoints and return JSON responses.
All API views should follow REST conventions and proper HTTP status codes.
"""

from aiohttp import web
from pydantic import ValidationError

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.domain.user import DuplicateUserError, UserRegistrationInput
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key, user_service_factory_key

logger = get_logger(__name__)


async def create_user(request: web.Request) -> web.Response:
    """
    Register a new user.

    Expected JSON payload:
    {
        "name": "User Name",
        "email": "user@example.com"
    }

    Returns:
    - 201: User created successfully with API key
    - 400: Invalid request data or validation errors
    - 409: User already exists
    - 500: Internal server error
    """
    try:
        data, parse_error = await parse_json_request(request)
        if parse_error:
            return create_error_response(parse_error, 400)

        if data is None:
            return create_error_response("Invalid JSON data", 400)

        try:
            registration_input = UserRegistrationInput(**data)
        except ValidationError as e:
            logger.warning(
                "User registration validation failed",
                errors=e.errors(),
                data=data,
            )
            return create_error_response("Invalid input data", 400)

        async with request.app[db_key]() as session:
            try:
                user_service_factory = request.app[user_service_factory_key]
                user_service = user_service_factory.create_service(session)
                user = await user_service.register_user(registration_input)

                await session.commit()

                logger.info(
                    "User registration API success",
                    user_id=user.id,
                    email=user.email,
                )

                return create_success_response(
                    {
                        "user": {
                            "id": user.id,
                            "name": user.name,
                            "email": user.email,
                            "api_key": str(user.api_key),
                            "registered_at": user.registered_at.isoformat(),
                        },
                    },
                    status=201,
                )

            except DuplicateUserError as e:
                await session.rollback()
                logger.warning(
                    "User registration failed - duplicate user",
                    email=e.email,
                )
                return create_error_response("User with this email already exists", 409)

            except Exception as e:
                await session.rollback()
                logger.exception(
                    "Unexpected error during user registration",
                    email=registration_input.email,
                    error_type=type(e).__name__,
                )
                return create_error_response("Internal server error", 500)

    except Exception:
        logger.exception("Unexpected error in user registration API")
        return create_error_response("Internal server error", 500)
