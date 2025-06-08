"""
Shared fixtures for API view tests.

Following testing guidelines: "Domain-specific fixtures in test files"
for pure unit testing of view functions without networking.
"""

from aiohttp import web
from aiohttp.test_utils import make_mocked_request


def make_api_request(method: str, path: str, app: web.Application):
    """Create a mocked request for unit testing API views."""
    return make_mocked_request(
        method=method,
        path=path,
        headers={"Content-Type": "application/json"},
        app=app,
    )
