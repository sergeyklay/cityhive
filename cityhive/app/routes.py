from aiohttp import web

from cityhive.app.views import index
from cityhive.infrastructure.config import PROJECT_DIR


def setup_routes(app: web.Application):
    app.router.add_get("/", index, name="index")


def setup_static_routes(app: web.Application):
    app.router.add_static("/static/", path=PROJECT_DIR / "static", name="static")
