"""
Monitoring and health check routes.

These routes provide system monitoring and health status endpoints following
Kubernetes health check patterns (liveness and readiness probes).
"""

from aiohttp import web

from cityhive.app.views.monitoring import liveness_check, readiness_check

# Health and monitoring routes
monitoring_routes = web.RouteTableDef()


@monitoring_routes.get("/health/live", name="liveness")
async def liveness_route(request: web.Request) -> web.Response:
    """
    Liveness probe endpoint.

    Fast check to verify the application is running.
    Used by Kubernetes to determine when to restart containers.
    """
    return await liveness_check(request)


@monitoring_routes.get("/health/ready", name="readiness")
async def readiness_route(request: web.Request) -> web.Response:
    """
    Readiness probe endpoint.

    Comprehensive check including dependencies.
    Used by Kubernetes and load balancers to route traffic.
    """
    return await readiness_check(request)


# Future monitoring routes can be added here
# @monitoring_routes.get("/metrics", name="metrics")
# async def metrics_route(request: web.Request) -> web.Response:
#     """Metrics endpoint for monitoring."""
