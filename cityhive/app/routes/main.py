"""
Main routes configuration for CityHive application.

This module contains the main route setup functions and groups routes
logically for better organization and future API support.
"""

from aiohttp import web

from cityhive.app.routes.hives import hive_routes
from cityhive.app.routes.inspections import inspection_routes
from cityhive.app.routes.monitoring import monitoring_routes
from cityhive.app.routes.users import user_routes
from cityhive.app.routes.web import web_routes
from cityhive.infrastructure.config import PROJECT_DIR


def setup_routes(app: web.Application) -> None:
    """Configure all application routes."""
    # Add web routes
    app.add_routes(web_routes)

    # Add monitoring routes
    app.add_routes(monitoring_routes)

    # Add entity-specific API routes
    app.add_routes(user_routes)
    app.add_routes(hive_routes)
    app.add_routes(inspection_routes)


def setup_static_routes(app: web.Application) -> None:
    """Configure static file serving."""
    app.router.add_static(
        "/static/",
        path=PROJECT_DIR / "static",
        name="static",
        # Add cache control for production
        # append_version=True  # Could be enabled for cache busting
    )


def create_api_subapp() -> web.Application:
    """
    Create API sub-application for future use.

    This allows better separation of concerns and different middleware
    for API vs web routes.
    """
    api_app = web.Application()

    # API-specific routes can be added here
    # api_app.add_routes(api_routes)

    # Future: API-specific middleware can be added here
    # api_app.middlewares.append(api_auth_middleware)
    # api_app.middlewares.append(cors_middleware)

    return api_app


def setup_subapps(app: web.Application) -> None:
    """
    Setup sub-applications for better route organization.

    This is optional and can be enabled when API routes are needed.
    """
    # Uncomment when API sub-app is needed:
    # api_app = create_api_subapp()
    # app.add_subapp('/api/', api_app)
    pass
