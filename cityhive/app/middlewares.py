import logging
from collections.abc import Awaitable, Callable

import aiohttp_jinja2
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware

logger = logging.getLogger(__name__)


async def handle_404(request: web.Request) -> web.Response:
    """Handle 404 Not Found errors with a custom template."""
    logger.warning("404 error for path: %s", request.path)
    return aiohttp_jinja2.render_template(
        "404.html", request, {"path": request.path}, status=404
    )


async def handle_500(request: web.Request) -> web.Response:
    """Handle 500 Internal Server Error with a custom template."""
    logger.error("500 error for path: %s", request.path)
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
                "Unhandled exception in request handler for %s %s",
                request.method,
                request.path,
                extra={"error": str(e), "path": request.path, "method": request.method},
            )
            handler_500 = overrides.get(500, handle_500)
            return await handler_500(request)

    return error_middleware


@web.middleware
async def logging_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    """Log request/response information."""
    import time

    start_time = time.time()

    logger.info(
        "Request started: %s %s",
        request.method,
        request.path,
        extra={
            "method": request.method,
            "path": request.path,
            "remote": request.remote,
        },
    )

    try:
        response = await handler(request)
        duration = time.time() - start_time

        logger.info(
            "Request completed: %s %s -> %d (%.3fs)",
            request.method,
            request.path,
            response.status,
            duration,
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status,
                "duration": duration,
            },
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Request failed: %s %s (%.3fs)",
            request.method,
            request.path,
            duration,
            extra={
                "method": request.method,
                "path": request.path,
                "duration": duration,
                "error": str(e),
            },
        )
        raise


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
