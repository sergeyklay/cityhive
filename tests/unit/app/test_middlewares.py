"""Unit tests for cityhive.app.middlewares module."""

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


async def test_handle_404_returns_correct_status_and_template(mocker):
    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Not Found", status=404)
    request = make_mocked_request("GET", "/nonexistent")

    response = await handle_404(request)

    assert response.status == 404
    mock_render.assert_called_once_with(
        "404.html", request, {"path": "/nonexistent"}, status=404
    )


async def test_handle_404_logs_warning_with_path(mocker):
    mock_logger = mocker.patch("cityhive.app.middlewares.logger")
    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Not Found", status=404)
    request = make_mocked_request("GET", "/missing-page")

    await handle_404(request)

    mock_logger.warning.assert_called_once_with(
        "404 error", path="/missing-page", method="GET"
    )


async def test_handle_500_returns_correct_status_and_template(mocker):
    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Server Error", status=500)
    request = make_mocked_request("POST", "/api/endpoint")

    response = await handle_500(request)

    assert response.status == 500
    mock_render.assert_called_once_with(
        "500.html", request, {"path": "/api/endpoint"}, status=500
    )


async def test_handle_500_logs_error_with_path(mocker):
    mock_logger = mocker.patch("cityhive.app.middlewares.logger")
    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Server Error", status=500)
    request = make_mocked_request("GET", "/error-endpoint")

    await handle_500(request)

    mock_logger.error.assert_called_once_with(
        "500 error", path="/error-endpoint", method="GET"
    )


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


async def test_create_error_middleware_handles_unexpected_exception(mocker):
    mock_logger = mocker.patch("cityhive.app.middlewares.logger")

    async def mock_handler(request):
        raise ValueError("Unexpected error")

    async def custom_500_handler(request):
        return web.Response(text="Custom 500", status=500)

    error_middleware = create_error_middleware({500: custom_500_handler})
    request = make_mocked_request("GET", "/error")

    response = await error_middleware(request, mock_handler)

    assert response.status == 500
    assert isinstance(response, web.Response)
    assert response.body == b"Custom 500"
    mock_logger.exception.assert_called_once_with(
        "Unhandled exception in request handler",
        method="GET",
        path="/error",
        error="Unexpected error",
        error_type="ValueError",
    )


async def test_create_error_middleware_uses_default_500_handler_when_no_override(
    mocker,
):
    mock_handle_500 = mocker.patch("cityhive.app.middlewares.handle_500")
    mock_handle_500.return_value = web.Response(text="Default 500", status=500)

    async def mock_handler(request):
        raise RuntimeError("Something went wrong")

    error_middleware = create_error_middleware({})
    request = make_mocked_request("POST", "/api/data")

    response = await error_middleware(request, mock_handler)

    assert response.status == 500
    mock_handle_500.assert_called_once_with(request)


async def test_logging_middleware_logs_successful_request(mocker):
    mock_get_logger = mocker.patch("cityhive.app.middlewares.get_logger")
    mocker.patch("cityhive.app.middlewares.clear_request_context")
    mocker.patch("cityhive.app.middlewares.bind_request_context")

    mock_logger = mocker.MagicMock()
    mock_bound_logger = mocker.MagicMock()
    mock_logger.bind.return_value = mock_bound_logger
    mock_get_logger.return_value = mock_logger

    async def mock_handler(request):
        return web.Response(text="OK", status=200)

    request = make_mocked_request("GET", "/test", headers={"Host": "localhost"})

    response = await logging_middleware(request, mock_handler)

    assert response.status == 200
    assert mock_bound_logger.info.call_count == 2

    start_call = mock_bound_logger.info.call_args_list[0]
    assert start_call[0][0] == "Request started"
    assert start_call[1]["method"] == "GET"
    assert start_call[1]["path"] == "/test"

    complete_call = mock_bound_logger.info.call_args_list[1]
    assert complete_call[0][0] == "Request completed"
    assert complete_call[1]["method"] == "GET"
    assert complete_call[1]["path"] == "/test"
    assert complete_call[1]["status"] == 200
    assert "duration_seconds" in complete_call[1]


async def test_logging_middleware_logs_failed_request(mocker):
    mock_get_logger = mocker.patch("cityhive.app.middlewares.get_logger")
    mocker.patch("cityhive.app.middlewares.clear_request_context")
    mocker.patch("cityhive.app.middlewares.bind_request_context")

    mock_logger = mocker.MagicMock()
    mock_bound_logger = mocker.MagicMock()
    mock_logger.bind.return_value = mock_bound_logger
    mock_get_logger.return_value = mock_logger

    async def mock_handler(request):
        raise ValueError("Handler error")

    request = make_mocked_request("POST", "/api/users")

    with pytest.raises(ValueError, match="Handler error"):
        await logging_middleware(request, mock_handler)

    assert mock_bound_logger.info.call_count == 1
    assert mock_bound_logger.error.call_count == 1

    start_call = mock_bound_logger.info.call_args_list[0]
    assert start_call[0][0] == "Request started"

    error_call = mock_bound_logger.error.call_args_list[0]
    assert error_call[0][0] == "Request failed"
    assert error_call[1]["method"] == "POST"
    assert error_call[1]["path"] == "/api/users"
    assert error_call[1]["error"] == "Handler error"
    assert error_call[1]["error_type"] == "ValueError"


async def test_logging_middleware_measures_request_duration(mocker):
    mock_get_logger = mocker.patch("cityhive.app.middlewares.get_logger")
    mocker.patch("cityhive.app.middlewares.clear_request_context")
    mocker.patch("cityhive.app.middlewares.bind_request_context")

    mock_logger = mocker.MagicMock()
    mock_bound_logger = mocker.MagicMock()
    mock_logger.bind.return_value = mock_bound_logger
    mock_get_logger.return_value = mock_logger

    async def slow_handler(request):
        return web.Response(text="Slow response", status=200)

    request = make_mocked_request("GET", "/slow")

    await logging_middleware(request, slow_handler)

    complete_call = mock_bound_logger.info.call_args_list[1]
    assert "duration_seconds" in complete_call[1]
    assert isinstance(complete_call[1]["duration_seconds"], float)
    assert complete_call[1]["duration_seconds"] >= 0


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
    assert app.middlewares[0] is logging_middleware
    assert callable(app.middlewares[1])


def test_setup_middlewares_configures_error_middleware_correctly(mocker):
    mock_create = mocker.patch("cityhive.app.middlewares.create_error_middleware")
    mock_middleware = mocker.AsyncMock()
    mock_create.return_value = mock_middleware
    app = web.Application()

    setup_middlewares(app)

    mock_create.assert_called_once_with({404: handle_404, 500: handle_500})
    assert app.middlewares[1] is mock_middleware


@pytest.mark.integration
async def test_middleware_integration_with_aiohttp_client(aiohttp_client):
    async def hello_handler(request):
        return web.Response(text="Hello, World!")

    app = web.Application()
    app.router.add_get("/", hello_handler)
    setup_middlewares(app)

    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == 200
        text = await resp.text()
        assert text == "Hello, World!"


@pytest.mark.integration
async def test_middleware_integration_exception_handling(aiohttp_client, mocker):
    mock_logger = mocker.patch("cityhive.app.middlewares.logger")
    mock_render = mocker.patch(
        "cityhive.app.middlewares.aiohttp_jinja2.render_template"
    )
    mock_render.return_value = web.Response(text="Server Error", status=500)

    async def error_handler(request):
        raise ValueError("Test exception")

    app = web.Application()
    app.router.add_get("/error", error_handler)
    setup_middlewares(app)

    client = await aiohttp_client(app)

    async with client.get("/error") as response:
        assert response.status == 500

    mock_logger.exception.assert_called_once_with(
        "Unhandled exception in request handler",
        method="GET",
        path="/error",
        error="Test exception",
        error_type="ValueError",
    )


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
    method: str, path: str, expected_method: str, expected_path: str, mocker
):
    mock_get_logger = mocker.patch("cityhive.app.middlewares.get_logger")
    mocker.patch("cityhive.app.middlewares.clear_request_context")
    mocker.patch("cityhive.app.middlewares.bind_request_context")

    mock_logger = mocker.MagicMock()
    mock_bound_logger = mocker.MagicMock()
    mock_logger.bind.return_value = mock_bound_logger
    mock_get_logger.return_value = mock_logger

    async def mock_handler(request):
        return web.Response(text="OK", status=200)

    request = make_mocked_request(method, path)

    await logging_middleware(request, mock_handler)

    start_call = mock_bound_logger.info.call_args_list[0]
    assert start_call[0][0] == "Request started"
    assert start_call[1]["method"] == expected_method
    assert start_call[1]["path"] == expected_path

    complete_call = mock_bound_logger.info.call_args_list[1]
    assert complete_call[0][0] == "Request completed"
    assert complete_call[1]["method"] == expected_method
    assert complete_call[1]["path"] == expected_path


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
