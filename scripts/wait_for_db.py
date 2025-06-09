#!/usr/bin/env python3
"""
Database connectivity check utility.

Simple database connectivity checker that waits for PostgreSQL availability.
This replaces the database wait logic scattered in various shell scripts.
"""

import asyncio
import os
import sys
from urllib.parse import urlparse

import asyncpg

from cityhive.infrastructure.logging import get_logger, setup_logging

setup_logging(force_json=True)

logger = get_logger(__name__)


async def check_database_connection(database_url: str) -> bool:
    """
    Check if database is available using a simple connection test.

    Args:
        database_url: Database connection URL

    Returns:
        True if database is available, False otherwise
    """
    try:
        # Convert SQLAlchemy URL to asyncpg format if needed
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace(
                "postgresql+asyncpg://", "postgresql://"
            )

        # Test connection
        conn = await asyncpg.connect(database_url)
        await conn.execute("SELECT 1")
        await conn.close()
        return True

    except Exception:
        return False


async def wait_for_database(
    database_url: str, max_attempts: int = 30, delay_seconds: int = 2
) -> bool:
    """
    Wait for database to become available.

    Args:
        database_url: Database connection URL
        max_attempts: Maximum number of connection attempts
        delay_seconds: Delay between attempts in seconds

    Returns:
        True if database is available, False if all attempts failed
    """
    # Parse database URL for logging
    parsed_url = urlparse(database_url)
    db_info = f"{parsed_url.hostname}:{parsed_url.port}/{parsed_url.path.lstrip('/')}"

    logger.info(
        "Starting database connectivity check",
        database=db_info,
        max_attempts=max_attempts,
        delay_seconds=delay_seconds,
    )

    for attempt in range(1, max_attempts + 1):
        start_time = asyncio.get_running_loop().time()

        if await check_database_connection(database_url):
            response_time = (asyncio.get_running_loop().time() - start_time) * 1000
            logger.info(
                "Database connectivity check successful",
                attempt=attempt,
                response_time_ms=round(response_time, 2),
            )
            return True

        logger.warning(
            "Database connectivity check failed",
            attempt=attempt,
            max_attempts=max_attempts,
        )

        if attempt < max_attempts:
            logger.info(
                "Waiting before next attempt",
                delay_seconds=delay_seconds,
                next_attempt=attempt + 1,
            )
            await asyncio.sleep(delay_seconds)

    logger.error(
        "Database connectivity check failed after all attempts",
        max_attempts=max_attempts,
        database=db_info,
    )
    return False


async def main():
    """Main entry point for database wait utility."""
    database_url = os.getenv("DATABASE_URI")
    if not database_url:
        logger.error("DATABASE_URI environment variable not set")
        sys.exit(1)

    # Parse command line arguments
    max_attempts = int(os.getenv("DB_WAIT_MAX_ATTEMPTS", "30"))
    delay_seconds = int(os.getenv("DB_WAIT_DELAY_SECONDS", "2"))

    success = await wait_for_database(database_url, max_attempts, delay_seconds)

    if success:
        logger.info("Database is ready")
        sys.exit(0)
    else:
        logger.error("Database connectivity check failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
