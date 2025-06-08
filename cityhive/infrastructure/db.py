from collections.abc import AsyncGenerator

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from cityhive.infrastructure.config import get_config
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


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
        max_overflow=config.db_max_overflow,
        pool_timeout=config.db_pool_timeout,
        pool_recycle=config.db_pool_recycle,
        pool_pre_ping=config.db_pool_pre_ping,
        echo=config.db_echo,
    )

    app[db_key] = async_sessionmaker(engine, expire_on_commit=False)

    try:
        yield
    finally:
        logger.info("Disposing database connection pool")
        await engine.dispose()
