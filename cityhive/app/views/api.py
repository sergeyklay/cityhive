"""
API views for JSON responses.

These views handle REST API endpoints and return JSON responses.
All API views should follow REST conventions and proper HTTP status codes.
"""

import json

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.services.user import (
    UserRegistrationData,
    UserRegistrationErrorType,
    UserService,
)
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

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
    - 400: Invalid request data
    - 409: User already exists
    - 500: Internal server error
    """
    try:
        # Parse and validate JSON request data
        try:
            data = await request.json()
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in user registration request")
            return web.json_response({"error": "Invalid JSON format"}, status=400)

        # Validate required fields
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()

        if not name:
            return web.json_response({"error": "Name is required"}, status=400)

        if not email:
            return web.json_response({"error": "Email is required"}, status=400)

        # Basic email validation
        email_parts = email.split("@")
        if (
            len(email_parts) != 2
            or not email_parts[0]
            or not email_parts[1]
            or "." not in email_parts[1]
        ):
            return web.json_response({"error": "Invalid email format"}, status=400)

        # Create registration data
        registration_data = UserRegistrationData(name=name, email=email)

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

                return web.json_response(
                    {
                        "success": True,
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
                email=email,
                error_type=result.error_type.value if result.error_type else None,
                error=result.error_message,
            )

            return web.json_response(
                {"success": False, "error": result.error_message}, status=status_code
            )

    except Exception:
        logger.exception("Unexpected error in user registration API")
        return web.json_response({"error": "Internal server error"}, status=500)
