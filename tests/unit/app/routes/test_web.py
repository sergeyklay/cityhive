"""Unit tests for web routes."""

from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import make_mocked_request

from cityhive.app.routes.web import index_route


async def test_index_route_delegates_to_index_view():
    """Test that index_route calls the index view function."""
    request = make_mocked_request("GET", "/")

    with patch("cityhive.app.routes.web.index") as mock_index:
        mock_index.return_value = AsyncMock()

        await index_route(request)

        mock_index.assert_called_once_with(request)


async def test_index_route_returns_view_response():
    """Test that index_route returns the response from index view."""
    request = make_mocked_request("GET", "/")
    expected_response = AsyncMock()

    with patch("cityhive.app.routes.web.index") as mock_index:
        mock_index.return_value = expected_response

        result = await index_route(request)

        assert result is expected_response
