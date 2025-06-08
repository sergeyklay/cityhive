"""
Hive API routes for JSON responses.

These routes handle hive-related REST API endpoints of the application.
All hive routes return JSON responses and follow REST conventions.
"""

from aiohttp import web

from cityhive.app.views.hives import create_hive

# Hive API routes (JSON responses)
hive_routes = web.RouteTableDef()


@hive_routes.post("/api/hives", name="api_hives_create")
async def hives_create_route(request: web.Request) -> web.Response:
    """Hive creation API endpoint."""
    return await create_hive(request)
