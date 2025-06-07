"""Configuration management for CityHive application.

This module provides environment-aware configuration using pydantic-settings
with class inheritance for different environments (development, production, testing).
"""

import os
from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Base configuration class for all environments."""

    model_config = SettingsConfigDict(
        env_file=".env",
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
        default="127.0.0.1",
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
                v = v.replace("postgresql://", "postgresql+asyncpg://")
                v = v.replace("postgres://", "postgresql+asyncpg://")
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

    db_pool_size: int = Field(default=5)
    db_pool_overflow: int = Field(default=10)

    app_host: str = Field(default="127.0.0.1")
    app_port: int = Field(default=8080)


class ProductionConfig(Config):
    """Production environment configuration."""

    debug: bool = False

    database_uri: PostgresDsn | None = Field(
        default=None,
        description="Production database connection URI (set via DATABASE_URI env var)",
    )

    db_pool_size: int = Field(default=20)
    db_pool_overflow: int = Field(default=30)

    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8080)

    def __init__(self, **kwargs):
        """Initialize production config with required environment variables."""
        if not kwargs.get("database_uri") and not os.getenv("DATABASE_URI"):
            raise ValueError(
                "DATABASE_URI environment variable is required for production"
            )

        if not kwargs.get("database_uri"):
            kwargs["database_uri"] = os.getenv("DATABASE_URI")

        super().__init__(**kwargs)


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

    db_pool_size: int = Field(default=2)
    db_pool_overflow: int = Field(default=5)

    app_host: str = Field(default="127.0.0.1")
    app_port: int = Field(default=8081)


def get_current_config(config_map: dict[str, type[Config]]) -> Config:
    """Get the current configuration instance based on environment.

    Args:
        config_map: Dictionary mapping environment names to config classes

    Returns:
        An instantiated Config object for the current environment

    Raises:
        ValueError: If the environment configuration is invalid
    """
    env = os.getenv("APP_ENV", "development").lower()
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


def get_config_for_environment(env: str) -> Config:
    """Get configuration for a specific environment.

    This function is useful for testing or when you need to override
    the environment setting programmatically.

    Args:
        env: Target environment name.

    Returns:
        Config instance configured for the specified environment.

    Examples:
        >>> test_config = get_config_for_environment("testing")
        >>> assert test_config.is_testing
        >>> assert not test_config.debug
    """
    config_class = config_registry.get(env.lower())
    if not config_class:
        available = ", ".join(config_registry.keys())
        raise ValueError(f"Invalid environment '{env}'. Available: {available}")

    return config_class()


def get_development_config() -> DevelopmentConfig:
    """Get development environment configuration."""
    return DevelopmentConfig()


def get_production_config() -> ProductionConfig:
    """Get production environment configuration."""
    return ProductionConfig()


def get_testing_config() -> TestingConfig:
    """Get testing environment configuration."""
    return TestingConfig()
