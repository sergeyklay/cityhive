import aiohttp_jinja2
from aiohttp import web

from cityhive.app.typedefs import db_key


@aiohttp_jinja2.template("index.html")
async def index(request: web.Request) -> dict:
    async with request.app[db_key]() as _:
        return {}
