"""
API views for JSON responses.

These views handle REST API endpoints and return JSON responses.
All API views should follow REST conventions and proper HTTP status codes.
"""

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)
from cityhive.app.helpers.validation import (
    get_normalized_email,
    sanitize_email_field,
    sanitize_string_field,
    validate_email,
    validate_required_field,
)
from cityhive.domain.services.user import (
    UserRegistrationData,
    UserRegistrationErrorType,
    UserService,
)
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


def _validate_user_data(
    data: dict,
) -> tuple[UserRegistrationData | None, web.Response | None]:
    """
    Validate and parse user registration data.

    Returns:
        Tuple of (UserRegistrationData, None) on success
        or (None, error_response) on failure
    """
    # Sanitize input fields
    name = sanitize_string_field(data.get("name"))
    email = sanitize_email_field(data.get("email"))

    # Validate required fields
    name_validation = validate_required_field(name, "Name")
    if not name_validation.is_valid:
        return None, create_error_response(
            name_validation.error_message or "Name validation failed", 400
        )

    email_validation = validate_required_field(email, "Email")
    if not email_validation.is_valid:
        return None, create_error_response(
            email_validation.error_message or "Email validation failed", 400
        )

    # Validate email format
    email_format_validation = validate_email(email)
    if not email_format_validation.is_valid:
        return None, create_error_response(
            email_format_validation.error_message or "Email format invalid", 400
        )

    # Get normalized email for storage consistency
    normalized_email = get_normalized_email(email)
    if normalized_email is None:
        return None, create_error_response("Invalid email format", 400)

    return UserRegistrationData(name=name, email=normalized_email), None


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
    - 400: Invalid request data
    - 409: User already exists
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

        # Validate and parse user data
        registration_data, validation_error = _validate_user_data(data)
        if validation_error:
            return validation_error

        # Ensure registration_data is not None (defensive programming)
        if registration_data is None:
            return create_error_response("Failed to process user data", 500)

        # Register user through domain service
        async with request.app[db_key]() as session:
            session: AsyncSession
            user_service = UserService()
            result = await user_service.register_user(session, registration_data)

            if result.success and result.user:
                logger.info(
                    "User registration API success",
                    user_id=result.user.id,
                    email=result.user.email,
                )

                return create_success_response(
                    {
                        "user": {
                            "id": result.user.id,
                            "name": result.user.name,
                            "email": result.user.email,
                            "api_key": str(result.user.api_key),
                            "registered_at": result.user.registered_at.isoformat(),
                        },
                    },
                    status=201,
                )

            # Determine appropriate HTTP status code based on structured error type
            status_code = 400  # Default to client error
            if result.error_type == UserRegistrationErrorType.USER_EXISTS:
                status_code = 409
            elif result.error_type in (
                UserRegistrationErrorType.DATABASE_ERROR,
                UserRegistrationErrorType.INTEGRITY_VIOLATION,
                UserRegistrationErrorType.UNKNOWN_ERROR,
            ):
                status_code = 500

            logger.warning(
                "User registration failed",
                email=registration_data.email,
                error_type=result.error_type.value if result.error_type else None,
                error=result.error_message,
            )

            return create_error_response(
                result.error_message or "Registration failed", status_code
            )

    except Exception:
        logger.exception("Unexpected error in user registration API")
        return create_error_response("Internal server error", 500)
