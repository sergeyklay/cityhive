import os
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from pydantic_settings import SettingsConfigDict

from cityhive.infrastructure.config import Config
from cityhive.infrastructure.typedefs import db_key


class MockAsyncContextManager:
    """Reusable async context manager for mocking database sessions."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    return AsyncMock()


@pytest.fixture
def session_maker(mock_session):
    """Create a session maker function that returns a context manager."""

    def _session_maker():
        return MockAsyncContextManager(mock_session)

    return _session_maker


@pytest.fixture
def base_app():
    """Basic aiohttp application without any configuration."""
    return web.Application()


@pytest.fixture
def app_with_db(base_app, session_maker):
    """Application with database configured for unit testing."""
    base_app[db_key] = session_maker
    return base_app


@pytest.fixture
async def client(aiohttp_client, base_app):
    """Test client for validation-only tests without database."""
    return await aiohttp_client(base_app)


@pytest.fixture
async def client_with_db(aiohttp_client, app_with_db):
    """Test client with database configured for integration tests."""
    return await aiohttp_client(app_with_db)


@pytest.fixture
async def full_app_client(aiohttp_client):
    """Test client with full application setup for end-to-end tests."""
    from cityhive.app.app import create_app

    app = await create_app()
    return await aiohttp_client(app)


@pytest.fixture(autouse=True)
def isolate_env():
    """Ensure complete test isolation from .env files and system environment."""
    # Preserve DATABASE_URI for tests that need it (integration tests)
    test_env = {}
    if "DATABASE_URI" in os.environ:
        # For local testing, convert Docker internal hostname to localhost
        database_uri = os.environ["DATABASE_URI"]
        if "cityhive-db" in database_uri:
            database_uri = database_uri.replace("cityhive-db", "localhost")
        test_env["DATABASE_URI"] = database_uri
    else:
        # Provide a test default for unit tests
        test_env["DATABASE_URI"] = (
            "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive"
        )

    with (
        patch.dict(os.environ, test_env, clear=True),
        patch.multiple(
            Config,
            model_config=SettingsConfigDict(env_file=None, env_ignore_empty=True),
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def suppress_integration_logging(request, caplog):
    """
    Automatically suppress verbose logging for integration tests.

    This fixture automatically activates for tests marked with @pytest.mark.integration
    and suppresses INFO level logs while keeping WARNING and ERROR visible.
    """
    if request.node.get_closest_marker("integration"):
        caplog.set_level("WARNING")

        import logging

        logging.getLogger("cityhive.app.middlewares").setLevel(logging.WARNING)
        logging.getLogger("cityhive.domain.services.health").setLevel(logging.WARNING)
        logging.getLogger("cityhive.infrastructure.database").setLevel(logging.WARNING)
