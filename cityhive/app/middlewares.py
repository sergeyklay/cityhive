from collections.abc import Awaitable, Callable

import aiohttp_jinja2
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware

from cityhive.infrastructure.logging import (
    bind_request_context,
    clear_request_context,
    get_logger,
)

logger = get_logger(__name__)


async def handle_404(request: web.Request) -> web.Response:
    """Handle 404 Not Found errors with a custom template."""
    logger.warning("404 error", path=request.path, method=request.method)
    return aiohttp_jinja2.render_template(
        "404.html", request, {"path": request.path}, status=404
    )


async def handle_500(request: web.Request) -> web.Response:
    """Handle 500 Internal Server Error with a custom template."""
    logger.error("500 error", path=request.path, method=request.method)
    return aiohttp_jinja2.render_template(
        "500.html", request, {"path": request.path}, status=500
    )


def create_error_middleware(
    overrides: dict[int, Callable[[web.Request], Awaitable[web.Response]]],
) -> Middleware:
    """
    Create error handling middleware with custom handlers for specific status codes.

    Args:
        overrides: Mapping of status codes to custom error handlers

    Returns:
        Configured middleware function
    """

    @web.middleware
    async def error_middleware(
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        try:
            return await handler(request)
        except web.HTTPException as ex:
            # Handle HTTP exceptions with custom handlers if available
            override = overrides.get(ex.status)
            if override:
                return await override(request)
            raise
        except Exception as e:
            # Log unexpected errors and return 500
            logger.exception(
                "Unhandled exception in request handler",
                method=request.method,
                path=request.path,
                error=str(e),
                error_type=type(e).__name__,
            )
            handler_500 = overrides.get(500, handle_500)
            return await handler_500(request)

    return error_middleware


@web.middleware
async def logging_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    """Log request/response information with structured logging."""
    import time
    import uuid

    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Clear any existing context and bind request-specific information
    clear_request_context()
    bind_request_context(
        request_id=request_id,
        method=request.method,
        path=request.path,
        remote=request.remote,
        user_agent=request.headers.get("User-Agent", "unknown"),
    )

    # Create a request-scoped logger
    request_logger = get_logger(__name__).bind(request_id=request_id)

    request_logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote=request.remote,
    )

    try:
        response = await handler(request)
        duration = time.time() - start_time

        request_logger.info(
            "Request completed",
            method=request.method,
            path=request.path,
            status=response.status,
            duration_seconds=round(duration, 3),
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        request_logger.error(
            "Request failed",
            method=request.method,
            path=request.path,
            duration_seconds=round(duration, 3),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
    finally:
        # Clean up request context
        clear_request_context()


def setup_middlewares(app: web.Application) -> None:
    """Configure all middlewares for the application."""
    error_middleware = create_error_middleware({404: handle_404, 500: handle_500})

    # Order matters: logging first, then error handling
    app.middlewares.extend(
        [
            logging_middleware,
            error_middleware,
        ]
    )
