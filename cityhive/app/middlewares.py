from typing import Awaitable, Callable

import aiohttp_jinja2
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware


async def handle_404(request: web.Request) -> web.Response:
    return aiohttp_jinja2.render_template("404.html", request, {}, status=404)


async def handle_500(request: web.Request) -> web.Response:
    return aiohttp_jinja2.render_template("500.html", request, {}, status=500)


def create_error_middleware(
    overrides: dict[int, Callable[[web.Request], Awaitable[web.Response]]],
) -> Middleware:
    @web.middleware
    async def error_middleware(
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        try:
            return await handler(request)
        except web.HTTPException as ex:
            override = overrides.get(ex.status, None)
            if override:
                return await override(request)
            raise
        except Exception:
            request.protocol.logger.exception("Error handling request")
            return await overrides.get(500, handle_500)(request)

    return error_middleware


def setup_middlewares(app: web.Application):
    error_middleware = create_error_middleware({404: handle_404, 500: handle_500})

    app.middlewares.append(error_middleware)
