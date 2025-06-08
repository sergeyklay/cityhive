"""
Web views for HTML responses.

These views handle the main web interface pages and return HTML responses.
"""

import aiohttp_jinja2
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


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
