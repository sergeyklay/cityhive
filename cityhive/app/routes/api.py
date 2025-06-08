"""
API routes for JSON responses.

These routes handle the REST API endpoints of the application.
All API routes should return JSON responses and follow REST conventions.
"""

from aiohttp import web

# Future API views will be imported here
# from cityhive.app.views.api import list_users, create_user, get_user

# API routes (JSON responses)
api_routes = web.RouteTableDef()

# Future API routes will be added here following REST conventions
# Example structure:

# @api_routes.get("/api/v1/users", name="api_users_list")
# async def users_list_route(request: web.Request) -> web.Response:
#     """List users API endpoint."""
#     return await list_users(request)

# @api_routes.post("/api/v1/users", name="api_users_create")
# async def users_create_route(request: web.Request) -> web.Response:
#     """Create user API endpoint."""
#     return await create_user(request)

# @api_routes.get("/api/v1/users/{user_id}", name="api_users_get")
# async def users_get_route(request: web.Request) -> web.Response:
#     """Get user API endpoint."""
#     return await get_user(request)
