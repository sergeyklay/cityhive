import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web

from cityhive.app.db import pg_context
from cityhive.app.middlewares import setup_middlewares
from cityhive.app.routes import setup_routes, setup_static_routes
from cityhive.app.typedefs import config_key
from cityhive.infrastructure.config import Config, get_config


def setup_templates(app: web.Application) -> None:
    """Configure Jinja2 templates for the application."""
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader("cityhive", "templates"),
    )


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

    return app


def main() -> None:
    """Main entry point for the application."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = get_config()

    web.run_app(create_app(config), host=config.app_host, port=config.app_port)
