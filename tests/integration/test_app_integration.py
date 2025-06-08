"""
Integration tests for the full aiohttp application.

These tests demonstrate best practices for aiohttp integration testing:
- Using async context managers for proper resource cleanup
- Testing full HTTP request/response cycles
- Using hierarchical fixtures appropriately
- Following aiohttp patterns from official documentation
- Suppressing verbose logging output for cleaner test results
"""

import pytest
from aiohttp import web


@pytest.mark.integration
async def test_liveness_endpoint_with_full_app(full_app_client):
    """Test liveness endpoint using full application setup."""
    async with full_app_client.get("/health/live") as response:
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cityhive"
        assert "timestamp" in data


@pytest.mark.integration
async def test_readiness_endpoint_with_full_app(full_app_client):
    """Test readiness endpoint using full application setup."""
    async with full_app_client.get("/health/ready") as response:
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cityhive"
        assert "timestamp" in data
        assert "components" in data


@pytest.mark.integration
async def test_middleware_pipeline_integration(aiohttp_client):
    """Test that middleware pipeline works correctly with real HTTP requests."""

    async def test_handler(request):
        return web.json_response({"message": "success"})

    app = web.Application()
    app.router.add_get("/test", test_handler)

    from cityhive.app.middlewares import setup_middlewares

    setup_middlewares(app)

    client = await aiohttp_client(app)

    async with client.get("/test") as response:
        assert response.status == 200
        data = await response.json()
        assert data["message"] == "success"


@pytest.mark.integration
async def test_404_handling_integration(aiohttp_client, mocker):
    """Test 404 error handling through the complete middleware stack."""

    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Not Found", status=404)

    app = web.Application()
    from cityhive.app.middlewares import setup_middlewares

    setup_middlewares(app)

    client = await aiohttp_client(app)

    async with client.get("/nonexistent") as response:
        assert response.status == 404
        text = await response.text()
        assert "Not Found" in text


@pytest.mark.integration
async def test_json_response_with_proper_headers(aiohttp_client):
    """Test JSON responses have proper content-type headers."""

    async def json_handler(request):
        return web.json_response({"data": "test"})

    app = web.Application()
    app.router.add_get("/api/test", json_handler)

    client = await aiohttp_client(app)

    async with client.get("/api/test") as response:
        assert response.status == 200
        assert response.content_type == "application/json"
        data = await response.json()
        assert data["data"] == "test"


@pytest.mark.integration
async def test_client_with_custom_headers(aiohttp_client):
    """Test client can send custom headers correctly."""

    async def header_echo_handler(request):
        auth_header = request.headers.get("Authorization")
        return web.json_response({"authorization": auth_header})

    app = web.Application()
    app.router.add_get("/echo-headers", header_echo_handler)

    client = await aiohttp_client(app)

    headers = {"Authorization": "Bearer test-token"}
    async with client.get("/echo-headers", headers=headers) as response:
        assert response.status == 200
        data = await response.json()
        assert data["authorization"] == "Bearer test-token"


@pytest.mark.integration
async def test_post_request_with_json_payload(aiohttp_client):
    """Test POST requests with JSON payloads work correctly."""

    async def echo_handler(request):
        data = await request.json()
        return web.json_response({"received": data})

    app = web.Application()
    app.router.add_post("/api/echo", echo_handler)

    client = await aiohttp_client(app)

    payload = {"name": "test", "value": 123}
    async with client.post("/api/echo", json=payload) as response:
        assert response.status == 200
        data = await response.json()
        assert data["received"] == payload


@pytest.mark.integration
async def test_database_integration_with_full_app(full_app_client):
    """Test that requires actual database connection."""
    async with full_app_client.get("/health/ready") as response:
        assert response.status == 200
        data = await response.json()
        assert "components" in data
        assert data["status"] == "healthy"

        db_component = next(
            (c for c in data["components"] if c["name"] == "database"), None
        )
        assert db_component is not None
        assert db_component["status"] == "healthy"
        assert "response_time_ms" in db_component
