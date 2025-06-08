"""
Request processing helpers for aiohttp handlers.

This module contains utilities for processing HTTP requests,
extracting data, and handling common request patterns.
"""

import json
from typing import Any

from aiohttp import web

from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)


async def parse_json_request(
    request: web.Request,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Parse JSON request body with proper error handling.

    Args:
        request: aiohttp web request object

    Returns:
        Tuple of (parsed_data, error_message)
        - If successful: (data_dict, None)
        - If failed: (None, error_message)

    Examples:
        >>> data, error = await parse_json_request(request)
        >>> if error:
        ...     return web.json_response({"error": error}, status=400)
    """
    try:
        data = await request.json()
        return data, None
    except json.JSONDecodeError:
        logger.warning(
            "Invalid JSON in request",
            method=request.method,
            path=request.path,
        )
        return None, "Invalid JSON format"
    except Exception as e:
        logger.error(
            "Unexpected error parsing JSON request",
            method=request.method,
            path=request.path,
            error_type=type(e).__name__,
        )
        return None, "Unable to parse request data"


def create_error_response(error_message: str, status: int = 400) -> web.Response:
    """
    Create standardized JSON error response.

    Args:
        error_message: Human-readable error message
        status: HTTP status code (default: 400)

    Returns:
        aiohttp JSON response with error details

    Examples:
        >>> return create_error_response("Invalid email format", 400)
        >>> return create_error_response("User not found", 404)
    """
    response_data: dict[str, Any] = {"error": error_message, "success": False}

    return web.json_response(response_data, status=status)


def create_success_response(data: dict[str, Any], status: int = 200) -> web.Response:
    """
    Create standardized JSON success response.

    Args:
        data: Response data dictionary
        status: HTTP status code (default: 200)

    Returns:
        aiohttp JSON response with success data

    Examples:
        >>> return create_success_response({"user": user_data}, 201)
    """
    response_data = {"success": True}
    response_data.update(data)

    return web.json_response(response_data, status=status)
