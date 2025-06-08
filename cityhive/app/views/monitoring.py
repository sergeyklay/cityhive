"""
Monitoring views for system health and metrics.

These views handle health checks and monitoring endpoints.
"""

from aiohttp import web
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


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
