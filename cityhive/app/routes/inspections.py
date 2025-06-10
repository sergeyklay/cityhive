"""
Inspection API routes for JSON responses.

These routes handle inspection-related REST API endpoints of the application.
All inspection routes return JSON responses and follow REST conventions.
"""

from aiohttp import web

from cityhive.app.views.inspections import create_inspection

# Inspection API routes (JSON responses)
inspection_routes = web.RouteTableDef()


@inspection_routes.post("/api/inspections", name="api_inspections_create")
async def inspections_create_route(request: web.Request) -> web.Response:
    """Inspection creation API endpoint."""
    return await create_inspection(request)
