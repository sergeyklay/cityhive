"""
Type definitions and application keys for the aiohttp application.

This module defines the type-safe keys used to store and retrieve
application-wide data in the aiohttp Application instance.
"""

from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from cityhive.domain.health.service import HealthServiceFactory
from cityhive.domain.hive.service import HiveServiceFactory
from cityhive.domain.user.service import UserServiceFactory
from cityhive.infrastructure.config import Config

# Application keys for type-safe data storage
# These keys ensure type safety when storing/retrieving data from app dict

config_key = web.AppKey("config", Config)
"""Application configuration key for storing Config instance."""

db_key = web.AppKey("database", async_sessionmaker)
"""Database session maker key for storing SQLAlchemy async session factory."""

user_service_factory_key = web.AppKey("user_service_factory", UserServiceFactory)
"""User service factory key for storing UserServiceFactory instance."""

hive_service_factory_key = web.AppKey("hive_service_factory", HiveServiceFactory)
"""Hive service factory key for storing HiveServiceFactory instance."""

health_service_factory_key = web.AppKey("health_service_factory", HealthServiceFactory)
"""Health service factory key for storing HealthServiceFactory instance."""
