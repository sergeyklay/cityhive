"""Unit tests for configuration management module.

This module tests the configuration class and validation logic using pytest.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import PostgresDsn, ValidationError

from cityhive.infrastructure.config import Config, get_config


def test_config_default_values():
    """Test that config has correct default values."""
    test_uri = "postgresql://test:test@localhost:5432/test"
    config = Config(database_uri=test_uri)  # type: ignore[arg-type]

    assert config.testing is False
    assert config.debug is False
    assert str(config.database_uri).startswith("postgresql+asyncpg://")
    assert config.db_pool_size == 5
    assert config.db_max_overflow == 10
    assert config.app_host == "0.0.0.0"
    assert config.app_port == 8080


@pytest.mark.parametrize(
    "database_uri,expected_scheme",
    [
        ("postgresql://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgres://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgresql+asyncpg://user:pass@host:5432/db", "postgresql+asyncpg"),
    ],
)
def test_config_database_uri_validation(database_uri: str, expected_scheme: str):
    """Test database URI validation converts to asyncpg driver."""
    config = Config(database_uri=database_uri)  # type: ignore[arg-type]

    assert config.database_uri.scheme == expected_scheme


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("db_pool_size", 0),
        ("db_pool_size", 51),
        ("db_max_overflow", -1),
        ("db_max_overflow", 101),
        ("app_port", 0),
        ("app_port", 65536),
    ],
)
def test_config_field_validation_constraints(field_name: str, invalid_value: int):
    """Test field validation constraints raise appropriate errors."""
    with pytest.raises(ValidationError) as exc_info:
        Config(
            database_uri="postgresql://test:test@test:5432/test",  # type: ignore[arg-type]
            **{field_name: invalid_value},  # type: ignore[arg-type]
        )

    assert field_name in str(exc_info.value)


def test_config_overrides():
    """Test config field overrides work correctly."""
    test_uri = "postgresql://test:test@localhost:5432/test"
    config = Config(
        database_uri=test_uri,  # type: ignore[arg-type]
        app_host="localhost",
        app_port=9000,
        db_pool_size=10,
        debug=True,
        testing=True,
    )

    assert config.app_host == "localhost"
    assert config.app_port == 9000
    assert config.db_pool_size == 10
    assert config.debug is True
    assert config.testing is True


def test_get_config_cached():
    """Test get_config returns cached instance on subsequent calls."""
    with patch.dict(
        os.environ, {"DATABASE_URI": "postgresql://test:test@localhost:5432/test"}
    ):
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
        assert isinstance(config1, Config)


def test_config_reads_from_environment():
    """Test config reads values from environment variables."""
    env_vars = {
        "DATABASE_URI": "postgresql://env:pass@env:5432/env_db",
        "APP_HOST": "env-host",
        "APP_PORT": "9876",
        "DB_POOL_SIZE": "15",
        "DB_MAX_OVERFLOW": "25",
        "DEBUG": "true",
        "TESTING": "false",
    }

    with patch.dict(os.environ, env_vars):
        config = Config()  # type: ignore[call-arg]

        assert (
            str(config.database_uri) == "postgresql+asyncpg://env:pass@env:5432/env_db"
        )
        assert config.app_host == "env-host"
        assert config.app_port == 9876
        assert config.db_pool_size == 15
        assert config.db_max_overflow == 25
        assert config.debug is True
        assert config.testing is False


def test_config_validation_with_invalid_env_values():
    """Test config validation fails with invalid environment values."""
    env_vars = {
        "DATABASE_URI": "postgresql://test:test@localhost:5432/test",
        "APP_PORT": "invalid_port",
    }
    with patch.dict(os.environ, env_vars):
        with pytest.raises(ValidationError):
            Config()  # type: ignore[call-arg]


def test_config_boolean_env_vars():
    """Test config handles boolean environment variables correctly."""
    env_vars = {
        "DATABASE_URI": "postgresql://test:test@localhost:5432/test",
        "DEBUG": "false",
        "TESTING": "true",
    }
    with patch.dict(os.environ, env_vars):
        config = Config()  # type: ignore[call-arg]

        assert config.debug is False
        assert config.testing is True


@pytest.mark.parametrize(
    "input_uri,expected_scheme",
    [
        ("postgresql://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgres://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgresql+asyncpg://user:pass@host:5432/db", "postgresql+asyncpg"),
    ],
)
def test_validate_database_uri_transforms_scheme(input_uri: str, expected_scheme: str):
    """Test database URI validator transforms schemes correctly."""
    config = Config(database_uri=input_uri)  # type: ignore[arg-type]

    assert config.database_uri.scheme == expected_scheme
    assert "user:pass@host:5432/db" in str(config.database_uri)


def test_validate_database_uri_preserves_asyncpg():
    """Test database URI validator preserves existing asyncpg scheme."""
    original_uri = PostgresDsn("postgresql+asyncpg://user:pass@host:5432/db")
    config = Config(database_uri=original_uri)

    assert str(config.database_uri) == str(original_uri)


def test_config_requires_database_uri():
    """Test config requires database_uri parameter or environment variable."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError, match="Field required"):
            Config()  # type: ignore[call-arg]


def test_config_from_environment_variable():
    """Test config can be created from DATABASE_URI environment variable."""
    test_uri = "postgresql://env:pass@localhost:5432/envdb"
    with patch.dict(os.environ, {"DATABASE_URI": test_uri}):
        config = Config()  # type: ignore[call-arg]
        assert (
            str(config.database_uri)
            == "postgresql+asyncpg://env:pass@localhost:5432/envdb"
        )
