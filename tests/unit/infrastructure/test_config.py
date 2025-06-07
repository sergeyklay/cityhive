"""Unit tests for configuration management module.

This module tests all configuration classes, validation logic, and helper functions
using pytest with parametrization for comprehensive coverage.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import PostgresDsn, ValidationError

from cityhive.infrastructure.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    get_config,
    get_current_config,
)


def test_base_config_default_values():
    """Test that base config has correct default values."""
    config = Config()

    assert config.testing is False
    assert config.debug is False
    assert str(config.database_uri).startswith("postgresql+asyncpg://")
    assert config.db_pool_size == 5
    assert config.db_pool_overflow == 10
    assert config.app_host == "0.0.0.0"
    assert config.app_port == 8080


def test_base_config_properties():
    """Test base config environment detection properties."""
    config = Config()

    assert config.is_development is False
    assert config.is_production is False
    assert config.is_testing is False


@pytest.mark.parametrize(
    "database_uri,expected_scheme",
    [
        ("postgresql://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgres://user:pass@host:5432/db", "postgresql+asyncpg"),
        ("postgresql+asyncpg://user:pass@host:5432/db", "postgresql+asyncpg"),
    ],
)
def test_base_config_database_uri_validation(database_uri: str, expected_scheme: str):
    """Test database URI validation converts to asyncpg driver."""
    config = Config(database_uri=database_uri)  # type: ignore[arg-type]

    assert config.database_uri.scheme == expected_scheme


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("db_pool_size", 0),
        ("db_pool_size", 51),
        ("db_pool_overflow", -1),
        ("db_pool_overflow", 101),
        ("app_port", 0),
        ("app_port", 65536),
    ],
)
def test_base_config_field_validation_constraints(field_name: str, invalid_value: int):
    """Test field validation constraints raise appropriate errors."""
    with pytest.raises(ValidationError) as exc_info:
        Config(
            database_uri="postgresql://test:test@test:5432/test",  # type: ignore[arg-type]
            **{field_name: invalid_value},  # type: ignore[arg-type]
        )

    assert field_name in str(exc_info.value)


def test_development_config_defaults():
    """Test development config has correct default values."""
    config = DevelopmentConfig()

    assert config.debug is True
    assert config.testing is False
    assert config.is_development is True
    assert config.is_production is False
    assert config.is_testing is False


def test_development_config_database_uri():
    """Test development config database URI default."""
    config = DevelopmentConfig()

    expected_uri = "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive"
    assert str(config.database_uri) == expected_uri


def test_development_config_overrides():
    """Test development config field overrides work correctly."""
    config = DevelopmentConfig(
        app_host="0.0.0.0",
        app_port=9000,
        db_pool_size=10,
    )

    assert config.app_host == "0.0.0.0"
    assert config.app_port == 9000
    assert config.db_pool_size == 10


def test_production_config_defaults():
    """Test production config has correct default values."""
    with patch.dict(
        os.environ, {"DATABASE_URI": "postgresql://prod:pass@prod:5432/prod"}
    ):
        config = ProductionConfig()

        assert config.debug is False
        assert config.testing is False
        assert config.is_development is False
        assert config.is_production is True
        assert config.is_testing is False
        assert config.app_host == "0.0.0.0"
        assert config.app_port == 8080
        assert config.db_pool_size == 5
        assert config.db_pool_overflow == 10


def test_production_config_requires_database_uri_env():
    """Test production config requires DATABASE_URI environment variable."""
    with pytest.raises(ValidationError, match="Field required"):
        ProductionConfig()


def test_production_config_with_env_database_uri():
    """Test production config uses DATABASE_URI from environment."""
    test_uri = "postgresql://prod:secret@prod-host:5432/prod_db"

    with patch.dict(os.environ, {"DATABASE_URI": test_uri}):
        config = ProductionConfig()

        assert (
            str(config.database_uri)
            == "postgresql+asyncpg://prod:secret@prod-host:5432/prod_db"
        )


def test_production_config_with_explicit_database_uri():
    """Test production config can accept explicit database_uri parameter."""
    test_uri = "postgresql://explicit:pass@explicit:5432/explicit_db"

    config = ProductionConfig(database_uri=test_uri)  # type: ignore[arg-type]

    assert (
        str(config.database_uri)
        == "postgresql+asyncpg://explicit:pass@explicit:5432/explicit_db"
    )


def test_testing_config_defaults():
    """Test testing config has correct default values."""
    config = TestingConfig()

    assert config.debug is False
    assert config.testing is True
    assert config.is_development is False
    assert config.is_production is False
    assert config.is_testing is True
    assert config.app_port == 8080
    assert config.db_pool_size == 5
    assert config.db_pool_overflow == 10


def test_testing_config_database_uri():
    """Test testing config database URI uses test database."""
    config = TestingConfig()

    expected_uri = "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive_test"
    assert str(config.database_uri) == expected_uri


def test_testing_config_overrides():
    """Test testing config field overrides work correctly."""
    config = TestingConfig(
        app_host="localhost",
        app_port=9999,
        db_pool_size=1,
    )

    assert config.app_host == "localhost"
    assert config.app_port == 9999
    assert config.db_pool_size == 1


@pytest.mark.parametrize(
    "env_value,expected_config_type",
    [
        ("development", DevelopmentConfig),
        ("production", ProductionConfig),
        ("testing", TestingConfig),
        ("DEVELOPMENT", DevelopmentConfig),
        ("Production", ProductionConfig),
        ("TESTING", TestingConfig),
    ],
)
def test_get_current_config_environment_detection(
    env_value: str, expected_config_type: type[Config]
):
    """Test get_current_config returns correct config based on APP_ENV."""
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    with patch.dict(os.environ, {"APP_ENV": env_value}):
        if expected_config_type == ProductionConfig:
            with patch.dict(
                os.environ,
                {"DATABASE_URI": "postgresql://test:test@test:5432/test"},
            ):
                config = get_current_config(config_map)
        else:
            config = get_current_config(config_map)

        assert isinstance(config, expected_config_type)


def test_get_current_config_invalid_environment():
    """Test get_current_config raises error for invalid environment."""
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    with patch.dict(os.environ, {"APP_ENV": "invalid_env"}):
        with pytest.raises(ValueError, match="Invalid environment 'invalid_env'"):
            get_current_config(config_map)


def test_get_current_config_empty_environment_defaults_to_development():
    """Test get_current_config defaults to 'default' when APP_ENV is empty."""
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
        "default": DevelopmentConfig,
    }

    config = get_current_config(config_map)
    assert isinstance(config, DevelopmentConfig)


def test_get_config_cached():
    """Test get_config returns cached instance on subsequent calls."""
    with patch.dict(os.environ, {"APP_ENV": "development"}):
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
        assert isinstance(config1, DevelopmentConfig)


def test_config_reads_from_environment():
    """Test config reads values from environment variables."""
    env_vars = {
        "DATABASE_URI": "postgresql://env:pass@env:5432/env_db",
        "APP_HOST": "env-host",
        "APP_PORT": "9876",
        "DB_POOL_SIZE": "15",
        "DB_POOL_OVERFLOW": "25",
    }

    with patch.dict(os.environ, env_vars):
        config = DevelopmentConfig()

        assert (
            str(config.database_uri) == "postgresql+asyncpg://env:pass@env:5432/env_db"
        )
        assert config.app_host == "env-host"
        assert config.app_port == 9876
        assert config.db_pool_size == 15
        assert config.db_pool_overflow == 25


def test_config_validation_with_invalid_env_values():
    """Test config validation fails with invalid environment values."""
    with patch.dict(os.environ, {"APP_PORT": "invalid_port"}):
        with pytest.raises(ValidationError):
            DevelopmentConfig()


def test_config_boolean_env_vars():
    """Test config handles boolean environment variables correctly."""
    with patch.dict(os.environ, {"DEBUG": "false", "TESTING": "true"}):
        config = Config()

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
