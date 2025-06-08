import os
from unittest.mock import AsyncMock, patch

import pytest
from pydantic_settings import SettingsConfigDict

from cityhive.infrastructure.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
)


@pytest.fixture(autouse=True)
def isolate_env_and_dotenv():
    """Ensure complete test isolation from .env files and system environment."""
    with (
        patch.dict(os.environ, {}, clear=True),
        patch.multiple(
            Config,
            model_config=SettingsConfigDict(env_file=None, env_ignore_empty=True),
        ),
        patch.multiple(
            DevelopmentConfig,
            model_config=SettingsConfigDict(env_file=None, env_ignore_empty=True),
        ),
        patch.multiple(
            ProductionConfig,
            model_config=SettingsConfigDict(env_file=None, env_ignore_empty=True),
        ),
        patch.multiple(
            TestingConfig,
            model_config=SettingsConfigDict(env_file=None, env_ignore_empty=True),
        ),
    ):
        yield


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
