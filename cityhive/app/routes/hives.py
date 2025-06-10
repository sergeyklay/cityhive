"""
Hive API routes for JSON responses.

These routes handle hive-related REST API endpoints of the application.
All hive routes return JSON responses and follow REST conventions.
"""

from aiohttp import web

from cityhive.app.views.hives import create_hive, list_hives

# Hive API routes (JSON responses)
hive_routes = web.RouteTableDef()


@hive_routes.post("/api/hives", name="api_hives_create")
async def hives_create_route(request: web.Request) -> web.Response:
    """Hive creation API endpoint."""
    return await create_hive(request)


@hive_routes.get("/api/hives", name="api_hives_list")
async def hives_list_route(request: web.Request) -> web.Response:
    """Hive list API endpoint."""
    return await list_hives(request)
