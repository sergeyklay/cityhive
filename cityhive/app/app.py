import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web

from cityhive.app.db import pg_context
from cityhive.app.middlewares import setup_middlewares
from cityhive.app.routes import setup_routes, setup_static_routes
from cityhive.app.typedefs import config_key
from cityhive.infrastructure.config import Config, get_config


def setup_templates(app: web.Application):
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader("cityhive", "templates"),
    )


async def create_app(config: Config) -> web.Application:
    app = web.Application()
    app[config_key] = config

    setup_routes(app)
    setup_static_routes(app)
    setup_middlewares(app)
    app.cleanup_ctx.append(pg_context)
    setup_templates(app)

    return app


def main():
    logging.basicConfig(level=logging.DEBUG)

    config = get_config()
    app = create_app(config)

    web.run_app(app, host=config.app_host, port=config.app_port)
