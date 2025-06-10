"""Unit tests for hive routes."""

from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import make_mocked_request

from cityhive.app.routes.hives import hives_create_route, hives_list_route


async def test_hives_create_route_delegates_to_create_hive_view():
    """Test that hives_create_route calls the create_hive view function."""
    request = make_mocked_request("POST", "/api/hives")

    with patch("cityhive.app.routes.hives.create_hive") as mock_create_hive:
        mock_create_hive.return_value = AsyncMock()

        await hives_create_route(request)

        mock_create_hive.assert_called_once_with(request)


async def test_hives_create_route_returns_view_response():
    """Test that hives_create_route returns the response from create_hive view."""
    request = make_mocked_request("POST", "/api/hives")
    expected_response = AsyncMock()

    with patch("cityhive.app.routes.hives.create_hive") as mock_create_hive:
        mock_create_hive.return_value = expected_response

        result = await hives_create_route(request)

        assert result is expected_response


async def test_hives_list_route_delegates_to_list_hives_view():
    """Test that hives_list_route calls the list_hives view function."""
    request = make_mocked_request("GET", "/api/hives")

    with patch("cityhive.app.routes.hives.list_hives") as mock_list_hives:
        mock_list_hives.return_value = AsyncMock()

        await hives_list_route(request)

        mock_list_hives.assert_called_once_with(request)


async def test_hives_list_route_returns_view_response():
    """Test that hives_list_route returns the response from list_hives view."""
    request = make_mocked_request("GET", "/api/hives")
    expected_response = AsyncMock()

    with patch("cityhive.app.routes.hives.list_hives") as mock_list_hives:
        mock_list_hives.return_value = expected_response

        result = await hives_list_route(request)

        assert result is expected_response
