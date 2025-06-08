"""
API routes for JSON responses.

These routes handle the REST API endpoints of the application.
All API routes should return JSON responses and follow REST conventions.
"""

from aiohttp import web

from cityhive.app.views.api import create_user

# API routes (JSON responses)
api_routes = web.RouteTableDef()


@api_routes.post("/api/users", name="api_users_create")
async def users_create_route(request: web.Request) -> web.Response:
    """User registration API endpoint."""
    return await create_user(request)
