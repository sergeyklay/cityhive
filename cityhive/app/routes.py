from aiohttp import web

from cityhive.app.views import health_check, index
from cityhive.infrastructure.config import PROJECT_DIR


def setup_routes(app: web.Application) -> None:
    """Configure all application routes."""
    # Main application routes
    app.router.add_get("/", index, name="index")

    # Health check endpoint for monitoring
    app.router.add_get("/health", health_check, name="health")


def setup_static_routes(app: web.Application) -> None:
    """Configure static file serving."""
    app.router.add_static(
        "/static/",
        path=PROJECT_DIR / "static",
        name="static",
        # Add cache control for production
        # append_version=True  # Could be enabled for cache busting
    )
