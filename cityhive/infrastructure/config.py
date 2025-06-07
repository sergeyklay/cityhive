"""Configuration management for CityHive application.

This module provides environment-aware configuration using pydantic-settings
with class inheritance for different environments (development, production, testing).
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).parent.parent
BASE_DIR = PROJECT_DIR.parent


class Config(BaseSettings):
    """Base configuration class for all environments."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    testing: bool = False
    debug: bool = False

    database_uri: PostgresDsn = Field(
        default_factory=lambda: PostgresDsn(
            "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive"
        ),
        description="PostgreSQL database connection URI",
    )

    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of permanent connections in the pool",
    )

    db_pool_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum number of overflow connections allowed",
    )

    app_host: str = Field(
        default="0.0.0.0",
        description="Host address to bind the HTTP server",
    )

    app_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Port number for the HTTP server",
    )

    @field_validator("database_uri", mode="before")
    @classmethod
    def validate_database_uri(cls, v: str | PostgresDsn) -> PostgresDsn:
        """Ensure database URI uses asyncpg driver for async support."""
        if isinstance(v, str):
            if not v.startswith(("postgresql+asyncpg://", "postgres+asyncpg://")):
                if v.startswith("postgresql://"):
                    v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
                elif v.startswith("postgres://"):
                    v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            return PostgresDsn(v)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return isinstance(self, DevelopmentConfig)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return isinstance(self, ProductionConfig)

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return isinstance(self, TestingConfig)


class DevelopmentConfig(Config):
    """Development environment configuration."""

    debug: bool = True

    database_uri: PostgresDsn = Field(
        default_factory=lambda: PostgresDsn(
            "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive"
        ),
        description="Development database connection URI",
    )


class ProductionConfig(Config):
    """Production environment configuration."""

    debug: bool = False

    database_uri: PostgresDsn = Field(  # type: ignore[assignment]
        ...,
        description="Production database connection URI (set via DATABASE_URI env var)",
    )


class TestingConfig(Config):
    """Testing environment configuration."""

    debug: bool = False
    testing: bool = True

    database_uri: PostgresDsn = Field(
        default_factory=lambda: PostgresDsn(
            "postgresql+asyncpg://cityhive:cityhive@localhost:5432/cityhive_test"
        ),
        description="Testing database connection URI",
    )


def get_current_config(config_map: dict[str, type[Config]]) -> Config:
    """Get the current configuration instance based on environment.

    Args:
        config_map: Dictionary mapping environment names to config classes

    Returns:
        An instantiated Config object for the current environment

    Raises:
        ValueError: If the environment configuration is invalid
    """
    env = os.getenv("APP_ENV", "default").lower()
    config_class = config_map.get(env)

    if not config_class:
        available = ", ".join(config_map.keys())
        raise ValueError(f"Invalid environment '{env}'. Available: {available}")

    return config_class()


config_registry = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,  # Fallback
}


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached application configuration.

    This function uses LRU cache to ensure configuration is loaded only once
    and reused across the application.

    Returns:
        Configured Config instance for the current environment.

    Examples:
        >>> config = get_config()
        >>> db_uri = config.database_uri
        >>> host = config.app_host

        # Subsequent calls return the same cached instance
        >>> config2 = get_config()
        >>> assert config is config2
    """
    return get_current_config(config_registry)
