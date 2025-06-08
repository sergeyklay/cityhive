"""
Web application routes for HTML responses.

These routes handle the main web interface of the application.
"""

from aiohttp import web

from cityhive.app.views.web import index

# Web application routes (HTML responses)
web_routes = web.RouteTableDef()


@web_routes.get("/", name="index")
async def index_route(request: web.Request) -> web.StreamResponse:
    """Home page route."""
    return await index(request)


# Future web routes can be added here
# @web_routes.get("/about", name="about")
# async def about_route(request: web.Request) -> web.StreamResponse:
#     """About page route."""
#     return await about_view(request)
