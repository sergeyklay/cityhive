import os
from unittest.mock import patch

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
