import logging

import aiohttp_jinja2
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.infrastructure.typedefs import db_key

logger = logging.getLogger(__name__)


@aiohttp_jinja2.template("index.html")
async def index(request: web.Request) -> dict[str, str]:
    """
    Home page view.

    Renders the main index page with basic application information.
    """
    try:
        # Get database session for potential future use
        async with request.app[db_key]() as session:
            # Type hint for session
            session: AsyncSession
            # Example: could fetch some data here
            # For now, just return empty context
            # Using session to avoid linting warning
            _ = session
            return {"title": "CityHive", "message": "Welcome to CityHive!"}
    except Exception:
        logger.exception("Error in index view")
        # Return basic context even if database fails
        return {
            "title": "CityHive",
            "message": "Welcome to CityHive!",
            "error": "Some features may be temporarily unavailable",
        }


async def health_check(request: web.Request) -> web.Response:
    """
    Health check endpoint for monitoring and load balancers.

    Returns a simple JSON response indicating service status.
    """
    try:
        # Test database connectivity
        async with request.app[db_key]() as session:
            session: AsyncSession
            # Simple query to test database
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))

        return web.json_response({"status": "healthy", "service": "cityhive"})
    except Exception:
        logger.exception("Health check failed")
        return web.json_response(
            {
                "status": "unhealthy",
                "service": "cityhive",
                "error": "Database connection failed",
            },
            status=503,
        )
