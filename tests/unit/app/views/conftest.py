"""
Shared fixtures for API view tests.

Following testing guidelines: "Cross-module reuse" and "Fundamental patterns"
for pure unit testing of view functions without networking.
"""

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from cityhive.infrastructure.typedefs import db_key


@pytest.fixture
def base_app():
    """Basic aiohttp application for unit testing."""
    return web.Application()


@pytest.fixture
def app_with_db(base_app, session_maker):
    """Application with database configured for unit testing."""
    base_app[db_key] = session_maker
    return base_app


def make_api_request(method: str, path: str, app: web.Application, json_data=None):
    """Create a mocked request for unit testing API views."""
    headers = {"Content-Type": "application/json"} if json_data else {}

    # For make_mocked_request, we'll simulate JSON data by adding it to the request
    # The actual JSON parsing will be handled by the view function
    kwargs = {
        "method": method,
        "path": path,
        "headers": headers,
        "app": app,
    }

    if json_data:
        # We'll patch the request.json() method in tests to return our data
        pass

    return make_mocked_request(**kwargs)
