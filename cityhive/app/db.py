from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cityhive.app.typedefs import db_key
from cityhive.infrastructure.config import get_config


async def pg_context(app: web.Application):
    """
    Create a database connection pool for the application.
    """
    config = get_config()
    engine = create_async_engine(
        str(config.database_uri),
        pool_size=config.db_pool_size,
        max_overflow=config.db_pool_overflow,
    )

    app[db_key] = async_sessionmaker(engine)

    yield

    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()
