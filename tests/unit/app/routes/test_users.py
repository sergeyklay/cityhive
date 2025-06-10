"""Unit tests for user routes."""

from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import make_mocked_request

from cityhive.app.routes.users import users_create_route


async def test_users_create_route_delegates_to_create_user_view():
    """Test that users_create_route calls the create_user view function."""
    request = make_mocked_request("POST", "/api/users")

    with patch("cityhive.app.routes.users.create_user") as mock_create_user:
        mock_create_user.return_value = AsyncMock()

        await users_create_route(request)

        mock_create_user.assert_called_once_with(request)


async def test_users_create_route_returns_view_response():
    """Test that users_create_route returns the response from create_user view."""
    request = make_mocked_request("POST", "/api/users")
    expected_response = AsyncMock()

    with patch("cityhive.app.routes.users.create_user") as mock_create_user:
        mock_create_user.return_value = expected_response

        result = await users_create_route(request)

        assert result is expected_response
