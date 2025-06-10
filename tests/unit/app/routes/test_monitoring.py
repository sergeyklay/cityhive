"""Unit tests for monitoring routes."""

from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import make_mocked_request

from cityhive.app.routes.monitoring import liveness_route, readiness_route


async def test_liveness_route_delegates_to_liveness_check_view():
    """Test that liveness_route calls the liveness_check view function."""
    request = make_mocked_request("GET", "/health/live")

    with patch("cityhive.app.routes.monitoring.liveness_check") as mock_liveness_check:
        mock_liveness_check.return_value = AsyncMock()

        await liveness_route(request)

        mock_liveness_check.assert_called_once_with(request)


async def test_liveness_route_returns_view_response():
    """Test that liveness_route returns the response from liveness_check view."""
    request = make_mocked_request("GET", "/health/live")
    expected_response = AsyncMock()

    with patch("cityhive.app.routes.monitoring.liveness_check") as mock_liveness_check:
        mock_liveness_check.return_value = expected_response

        result = await liveness_route(request)

        assert result is expected_response


async def test_readiness_route_delegates_to_readiness_check_view():
    """Test that readiness_route calls the readiness_check view function."""
    request = make_mocked_request("GET", "/health/ready")

    with patch(
        "cityhive.app.routes.monitoring.readiness_check"
    ) as mock_readiness_check:
        mock_readiness_check.return_value = AsyncMock()

        await readiness_route(request)

        mock_readiness_check.assert_called_once_with(request)


async def test_readiness_route_returns_view_response():
    """Test that readiness_route returns the response from readiness_check view."""
    request = make_mocked_request("GET", "/health/ready")
    expected_response = AsyncMock()

    with patch(
        "cityhive.app.routes.monitoring.readiness_check"
    ) as mock_readiness_check:
        mock_readiness_check.return_value = expected_response

        result = await readiness_route(request)

        assert result is expected_response
