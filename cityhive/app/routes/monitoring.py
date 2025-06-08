"""
Monitoring and health check routes.

These routes provide system monitoring and health status endpoints.
"""

from aiohttp import web

from cityhive.app.views.monitoring import health_check

# Health and monitoring routes
monitoring_routes = web.RouteTableDef()


@monitoring_routes.get("/health", name="health")
async def health_route(request: web.Request) -> web.Response:
    """Health check endpoint for monitoring."""
    return await health_check(request)


# Future monitoring routes can be added here
# @monitoring_routes.get("/metrics", name="metrics")
# async def metrics_route(request: web.Request) -> web.Response:
#     """Metrics endpoint for monitoring."""
