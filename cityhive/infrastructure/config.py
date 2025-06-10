"""Configuration management for CityHive application.

This module provides environment-aware configuration using pydantic-settings.
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).parent.parent
BASE_DIR = PROJECT_DIR.parent


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    debug: bool = False

    database_uri: PostgresDsn = Field(
        ...,
        description="PostgreSQL database connection URI (required)",
    )

    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of permanent connections in the pool",
    )

    db_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum number of overflow connections allowed",
    )

    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Seconds to wait before timing out on pool get",
    )

    db_pool_recycle: int = Field(
        default=1800,
        ge=60,
        le=3600,
        description="Seconds to recycle connections after",
    )

    db_pool_pre_ping: bool = Field(
        default=True,
        description="Check connection health before using",
    )

    db_echo: bool = Field(
        default=False,
        description="Enable SQL logging in debug mode",
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

    log_force_json: bool = Field(
        default=True,
        description="Force JSON logging",
    )

    log_level: int = Field(
        default=logging.INFO,
        ge=logging.NOTSET,
        le=logging.CRITICAL,
        description="Log level",
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


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached application configuration.

    This function uses LRU cache to ensure configuration is loaded only once
    and reused across the application.

    Configuration is loaded from environment variables. The DATABASE_URI
    environment variable is required.

    Returns:
        Configured Config instance.

    Examples:
        >>> import os
        >>> os.environ["DATABASE_URI"] = "postgresql://user:pass@host:5432/db"
        >>> config = get_config()
        >>> db_uri = config.database_uri
        >>> host = config.app_host

        # Subsequent calls return the same cached instance
        >>> config2 = get_config()
        >>> assert config is config2

    Raises:
        ValidationError: If DATABASE_URI environment variable is not set.
    """
    return Config()  # type: ignore[call-arg]
