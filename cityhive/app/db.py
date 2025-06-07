import logging
from collections.abc import AsyncGenerator

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from cityhive.app.typedefs import db_key
from cityhive.infrastructure.config import get_config

logger = logging.getLogger(__name__)


async def pg_context(app: web.Application) -> AsyncGenerator[None, None]:
    """
    Create and manage database connection pool for the application lifecycle.

    This cleanup context ensures proper initialization and cleanup of the
    database engine and session factory.
    """
    config = get_config()

    logger.info("Initializing database connection pool")
    engine: AsyncEngine = create_async_engine(
        str(config.database_uri),
        pool_size=config.db_pool_size,
        max_overflow=config.db_pool_overflow,
        echo=config.debug,  # Enable SQL logging in debug mode
    )

    app[db_key] = async_sessionmaker(engine, expire_on_commit=False)

    try:
        yield
    finally:
        logger.info("Disposing database connection pool")
        await engine.dispose()
