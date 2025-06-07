"""
CityHive web application package.

This package contains the aiohttp web application components including
views, middleware, routing, and application factory.
"""

from cityhive.app.app import create_app, main

__all__ = ["create_app", "main"]
