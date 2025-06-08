"""
Views package for CityHive application.

This package contains all view handlers organized by functionality.
Views handle the business logic for each route.
"""

from cityhive.app.views.monitoring import health_check
from cityhive.app.views.web import index

__all__ = ["index", "health_check"]
