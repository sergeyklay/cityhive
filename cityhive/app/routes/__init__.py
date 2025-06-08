"""
Routes package for CityHive application.

This package organizes routes into logical groups for better maintainability
and future extensibility.
"""

from cityhive.app.routes.main import setup_routes, setup_static_routes, setup_subapps

__all__ = ["setup_routes", "setup_static_routes", "setup_subapps"]
