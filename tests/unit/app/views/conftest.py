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


def make_api_request(method: str, path: str, app: web.Application):
    """Create a mocked request for unit testing API views."""
    return make_mocked_request(
        method=method,
        path=path,
        headers={"Content-Type": "application/json"},
        app=app,
    )
