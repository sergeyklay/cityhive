"""
User API routes for JSON responses.

These routes handle user-related REST API endpoints of the application.
All user routes return JSON responses and follow REST conventions.
"""

from aiohttp import web

from cityhive.app.views.users import create_user

# User API routes (JSON responses)
user_routes = web.RouteTableDef()


@user_routes.post("/api/users", name="api_users_create")
async def users_create_route(request: web.Request) -> web.Response:
    """User registration API endpoint."""
    return await create_user(request)
