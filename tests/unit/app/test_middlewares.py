"""
Unit tests for cityhive.app.middlewares module.

Tests middleware functionality including error handling, logging,
and request/response processing following aiohttp patterns.
"""

import logging
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from cityhive.app.middlewares import (
    create_error_middleware,
    handle_404,
    handle_500,
    logging_middleware,
    setup_middlewares,
)


async def test_handle_404_returns_correct_status_and_template():
    request = make_mocked_request("GET", "/nonexistent")

    with patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    ) as mock_render:
        mock_render.return_value = web.Response(text="Not Found", status=404)

        response = await handle_404(request)

        assert response.status == 404
        mock_render.assert_called_once_with(
            "404.html", request, {"path": "/nonexistent"}, status=404
        )


async def test_handle_404_logs_warning_with_path(caplog):
    request = make_mocked_request("GET", "/missing-page")

    with patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    ) as mock_render:
        mock_render.return_value = web.Response(text="Not Found", status=404)

        with caplog.at_level(logging.WARNING):
            await handle_404(request)

        assert "404 error for path: /missing-page" in caplog.text
        assert caplog.records[0].levelname == "WARNING"


async def test_handle_500_returns_correct_status_and_template():
    request = make_mocked_request("POST", "/api/endpoint")

    with patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    ) as mock_render:
        mock_render.return_value = web.Response(text="Server Error", status=500)

        response = await handle_500(request)

        assert response.status == 500
        mock_render.assert_called_once_with(
            "500.html", request, {"path": "/api/endpoint"}, status=500
        )


async def test_handle_500_logs_error_with_path(caplog):
    request = make_mocked_request("GET", "/error-endpoint")

    with patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    ) as mock_render:
        mock_render.return_value = web.Response(text="Server Error", status=500)

        with caplog.at_level(logging.ERROR):
            await handle_500(request)

        assert "500 error for path: /error-endpoint" in caplog.text
        assert caplog.records[0].levelname == "ERROR"


async def test_create_error_middleware_handles_successful_request():
    async def mock_handler(request):
        return web.Response(text="Success", status=200)

    error_middleware = create_error_middleware({})
    request = make_mocked_request("GET", "/")

    response = await error_middleware(request, mock_handler)

    assert response.status == 200
    assert isinstance(response, web.Response)
    assert response.body == b"Success"


async def test_create_error_middleware_handles_http_exception_with_override():
    async def mock_handler(request):
        raise web.HTTPNotFound()

    async def custom_404_handler(request):
        return web.Response(text="Custom 404", status=404)

    error_middleware = create_error_middleware({404: custom_404_handler})
    request = make_mocked_request("GET", "/missing")

    response = await error_middleware(request, mock_handler)

    assert response.status == 404
    assert isinstance(response, web.Response)
    assert response.body == b"Custom 404"


async def test_create_error_middleware_reraises_http_exception_without_override():
    async def mock_handler(request):
        raise web.HTTPForbidden()

    error_middleware = create_error_middleware({404: handle_404})
    request = make_mocked_request("GET", "/forbidden")

    with pytest.raises(web.HTTPForbidden):
        await error_middleware(request, mock_handler)


async def test_create_error_middleware_handles_unexpected_exception(caplog):
    async def mock_handler(request):
        raise ValueError("Unexpected error")

    async def custom_500_handler(request):
        return web.Response(text="Custom 500", status=500)

    error_middleware = create_error_middleware({500: custom_500_handler})
    request = make_mocked_request("GET", "/error")

    with caplog.at_level(logging.ERROR):
        response = await error_middleware(request, mock_handler)

    assert response.status == 500
    assert isinstance(response, web.Response)
    assert response.body == b"Custom 500"
    assert "Unhandled exception in request handler for GET /error" in caplog.text


async def test_create_error_middleware_uses_default_500_handler_when_no_override():
    async def mock_handler(request):
        raise RuntimeError("Something went wrong")

    error_middleware = create_error_middleware({})
    request = make_mocked_request("POST", "/api/data")

    with patch("cityhive.app.middlewares.handle_500") as mock_handle_500:
        mock_handle_500.return_value = web.Response(text="Default 500", status=500)

        response = await error_middleware(request, mock_handler)

        assert response.status == 500
        mock_handle_500.assert_called_once_with(request)


async def test_logging_middleware_logs_successful_request(caplog):
    async def mock_handler(request):
        return web.Response(text="OK", status=200)

    request = make_mocked_request("GET", "/test", headers={"Host": "localhost"})

    with caplog.at_level(logging.INFO):
        response = await logging_middleware(request, mock_handler)

    assert response.status == 200
    assert len(caplog.records) == 2

    start_record = caplog.records[0]
    assert "Request started: GET /test" in start_record.message
    assert start_record.method == "GET"
    assert start_record.path == "/test"

    complete_record = caplog.records[1]
    assert "Request completed: GET /test -> 200" in complete_record.message
    assert complete_record.status == 200
    assert "duration" in complete_record.__dict__


async def test_logging_middleware_logs_failed_request(caplog):
    async def mock_handler(request):
        raise ValueError("Handler error")

    request = make_mocked_request("POST", "/api/users")

    with (
        caplog.at_level(logging.INFO),
        pytest.raises(ValueError, match="Handler error"),
    ):
        await logging_middleware(request, mock_handler)

    assert len(caplog.records) == 2

    start_record = caplog.records[0]
    assert "Request started: POST /api/users" in start_record.message

    fail_record = caplog.records[1]
    assert "Request failed: POST /api/users" in fail_record.message
    assert fail_record.levelname == "ERROR"
    assert "Handler error" in fail_record.error


async def test_logging_middleware_measures_request_duration(caplog):
    async def slow_handler(request):
        return web.Response(text="Slow response", status=200)

    request = make_mocked_request("GET", "/slow")

    with caplog.at_level(logging.INFO):
        await logging_middleware(request, slow_handler)

    complete_record = caplog.records[1]
    assert hasattr(complete_record, "duration")
    assert isinstance(complete_record.duration, float)
    assert complete_record.duration >= 0


async def test_logging_middleware_passes_through_response_unchanged():
    expected_response = web.Response(
        text="Original response", status=201, headers={"X-Custom": "header"}
    )

    async def mock_handler(request):
        return expected_response

    request = make_mocked_request("PUT", "/resource")

    actual_response = await logging_middleware(request, mock_handler)

    assert actual_response is expected_response
    assert actual_response.status == 201
    assert isinstance(actual_response, web.Response)
    assert actual_response.body == b"Original response"
    assert actual_response.headers.get("X-Custom") == "header"


def test_setup_middlewares_adds_correct_middlewares_in_order():
    app = web.Application()
    assert len(app.middlewares) == 0

    setup_middlewares(app)

    assert len(app.middlewares) == 2

    middlewares = list(app.middlewares)
    assert middlewares[0] is logging_middleware
    assert callable(middlewares[1])


def test_setup_middlewares_configures_error_middleware_correctly():
    app = web.Application()

    with patch("cityhive.app.middlewares.create_error_middleware") as mock_create:
        mock_middleware = AsyncMock()
        mock_create.return_value = mock_middleware

        setup_middlewares(app)

        mock_create.assert_called_once_with({404: handle_404, 500: handle_500})
        assert mock_middleware in app.middlewares


@pytest.mark.integration
async def test_middleware_integration_with_aiohttp_client(aiohttp_client):
    async def hello_handler(request):
        return web.Response(text="Hello, World!")

    app = web.Application()
    app.router.add_get("/", hello_handler)
    setup_middlewares(app)

    client = await aiohttp_client(app)

    resp = await client.get("/")

    assert resp.status == 200
    text = await resp.text()
    assert text == "Hello, World!"


@pytest.mark.integration
async def test_middleware_integration_exception_handling(aiohttp_client, caplog):
    async def error_handler(request):
        raise ValueError("Test exception")

    app = web.Application()
    app.router.add_get("/error", error_handler)
    setup_middlewares(app)

    client = await aiohttp_client(app)

    with caplog.at_level(logging.ERROR):
        resp = await client.get("/error")

    assert resp.status == 500
    assert "Unhandled exception in request handler for GET /error" in caplog.text


@pytest.mark.parametrize(
    "method,path,expected_method,expected_path",
    [
        ("GET", "/", "GET", "/"),
        ("POST", "/api/users", "POST", "/api/users"),
        ("PUT", "/api/users/123", "PUT", "/api/users/123"),
        ("DELETE", "/api/resources/456", "DELETE", "/api/resources/456"),
    ],
)
async def test_logging_middleware_handles_different_methods_and_paths(
    method: str, path: str, expected_method: str, expected_path: str, caplog
):
    async def mock_handler(request):
        return web.Response(text="Response", status=200)

    request = make_mocked_request(method, path)

    with caplog.at_level(logging.INFO):
        await logging_middleware(request, mock_handler)

    start_record = caplog.records[0]
    complete_record = caplog.records[1]

    assert f"Request started: {expected_method} {expected_path}" in start_record.message
    assert (
        f"Request completed: {expected_method} {expected_path} -> 200"
        in complete_record.message
    )


@pytest.mark.parametrize(
    "exception_class,status_code,should_use_override",
    [
        (web.HTTPNotFound, 404, True),
        (web.HTTPInternalServerError, 500, True),
        (web.HTTPForbidden, 403, False),
        (web.HTTPUnauthorized, 401, False),
    ],
)
async def test_error_middleware_handles_different_http_exceptions(
    exception_class, status_code: int, should_use_override: bool
):
    async def mock_handler(request):
        raise exception_class()

    async def custom_handler(request):
        return web.Response(text=f"Custom {status_code}", status=status_code)

    error_middleware = create_error_middleware(
        {404: custom_handler, 500: custom_handler}
    )
    request = make_mocked_request("GET", "/test")

    if should_use_override:
        response = await error_middleware(request, mock_handler)
        assert response.status == status_code
        assert isinstance(response, web.Response)
        assert response.body == f"Custom {status_code}".encode()
    else:
        with pytest.raises(exception_class):
            await error_middleware(request, mock_handler)
