"""
Monitoring views for system health and metrics.

These views handle health checks and monitoring endpoints using the centralized
health check service from the domain layer.
"""

from typing import Any

from aiohttp import web

from cityhive.domain.services.health import HealthCheckService
from cityhive.infrastructure.logging import get_logger
from cityhive.infrastructure.typedefs import db_key

logger = get_logger(__name__)


async def liveness_check(request: web.Request) -> web.Response:
    """
    Liveness probe endpoint.

    Fast check to verify the application is running and responsive.
    Used by orchestration systems to know when to restart the container.
    """
    health_service = HealthCheckService()
    health = await health_service.check_liveness()

    response_data: dict[str, Any] = {
        "status": health.status.value,
        "service": health.service,
        "timestamp": health.timestamp.isoformat(),
    }

    if health.version:
        response_data["version"] = health.version

    logger.info("Liveness check completed", status=health.status.value)

    return web.json_response(
        response_data,
        status=200 if health.is_healthy else 503,
    )


async def readiness_check(request: web.Request) -> web.Response:
    """
    Readiness probe endpoint.

    Comprehensive check including all dependencies (database, etc.).
    Used by load balancers to know when the service can accept traffic.
    """
    health_service = HealthCheckService()
    health = await health_service.check_readiness(request.app[db_key])

    response_data: dict[str, Any] = {
        "status": health.status.value,
        "service": health.service,
        "timestamp": health.timestamp.isoformat(),
    }

    if health.version:
        response_data["version"] = health.version

    if health.components:
        components_data = []
        for component in health.components:
            component_dict = {
                "name": component.name,
                "status": component.status.value,
                "message": component.message,
                "response_time_ms": component.response_time_ms,
            }

            # Add metadata safely without overwriting core fields
            if component.metadata:
                component_dict["metadata"] = component.metadata

            components_data.append(component_dict)

        response_data["components"] = components_data

    logger.info(
        "Readiness check completed",
        status=health.status.value,
        component_count=len(health.components) if health.components else 0,
    )

    return web.json_response(
        response_data,
        status=200 if health.is_healthy else 503,
    )
