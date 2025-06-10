from collections.abc import AsyncGenerator

import aiohttp_jinja2
import jinja2
from aiohttp import web

from cityhive.app.middlewares import setup_middlewares
from cityhive.app.routes import setup_routes, setup_static_routes
from cityhive.domain.health.service import HealthServiceFactory
from cityhive.domain.hive.service import HiveServiceFactory
from cityhive.domain.inspection.service import InspectionServiceFactory
from cityhive.domain.user.service import UserServiceFactory
from cityhive.infrastructure.config import Config, get_config
from cityhive.infrastructure.db import pg_context
from cityhive.infrastructure.logging import get_logger, setup_logging
from cityhive.infrastructure.typedefs import (
    config_key,
    db_key,
    health_service_factory_key,
    hive_service_factory_key,
    inspection_service_factory_key,
    user_service_factory_key,
)


def setup_templates(app: web.Application) -> None:
    """Configure Jinja2 templates for the application."""
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader("cityhive", "templates"),
    )


def init_user_service(app: web.Application) -> None:
    """
    Initialize user service with proper dependency injection.

    Creates and registers a UserServiceFactory that can create UserService instances
    with proper session management for each request.
    """
    session_factory = app[db_key]
    user_service_factory = UserServiceFactory(session_factory)
    app[user_service_factory_key] = user_service_factory


def init_hive_service(app: web.Application) -> None:
    """
    Initialize hive service with proper dependency injection.

    Creates and registers a HiveServiceFactory that can create HiveService instances
    with proper session management for each request.
    """
    session_factory = app[db_key]
    hive_service_factory = HiveServiceFactory(session_factory)
    app[hive_service_factory_key] = hive_service_factory


def init_inspection_service(app: web.Application) -> None:
    """
    Initialize inspection service with proper dependency injection.

    Creates and registers an InspectionServiceFactory that can create InspectionService
    instances with proper session management for each request.
    """
    session_factory = app[db_key]
    inspection_service_factory = InspectionServiceFactory(session_factory)
    app[inspection_service_factory_key] = inspection_service_factory


def init_health_service(app: web.Application) -> None:
    """
    Initialize health service with proper dependency injection.

    Creates and registers a HealthServiceFactory that can create HealthService instances
    for health check operations.
    """
    config = app[config_key]
    health_service_factory = HealthServiceFactory(
        service_name="cityhive",
        version=getattr(config, "version", None),
    )
    app[health_service_factory_key] = health_service_factory


async def init_services_context(app: web.Application) -> AsyncGenerator[None, None]:
    """
    Startup context for initializing services after database is ready.

    This is where all service wiring and dependency injection happens.
    Keeps infrastructure concerns out of domain modules.

    This function also ensures services are initialized only after the
    database cleanup context has set up the session factory.
    """
    init_user_service(app)
    init_hive_service(app)
    init_inspection_service(app)
    init_health_service(app)

    yield


async def create_app(config: Config | None = None) -> web.Application:
    """
    Application factory for creating the aiohttp web application.

    Args:
        config: Optional configuration object. If None, loads from environment.

    Returns:
        Configured aiohttp Application instance.
    """
    if config is None:
        config = get_config()

    app = web.Application()
    app[config_key] = config

    # Setup order matters: middleware first, then routes, then cleanup contexts
    setup_middlewares(app)
    setup_routes(app)
    setup_static_routes(app)
    setup_templates(app)

    # Database connection cleanup context
    app.cleanup_ctx.append(pg_context)

    # Services initialization context (runs after database is ready)
    app.cleanup_ctx.append(init_services_context)

    return app


def main() -> None:
    """Main entry point for the application."""
    setup_logging(force_json=True)

    logger = get_logger(__name__)
    logger.info("Starting CityHive application")

    config = get_config()
    logger.info(
        "Configuration loaded", app_host=config.app_host, app_port=config.app_port
    )

    web.run_app(create_app(config), host=config.app_host, port=config.app_port)
