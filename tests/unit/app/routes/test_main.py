"""Unit tests for main routes setup."""

from unittest.mock import Mock, patch

from aiohttp import web

from cityhive.app.routes.main import (
    create_api_subapp,
    setup_routes,
    setup_static_routes,
    setup_subapps,
)


def test_setup_routes_adds_all_route_tables():
    """Test that setup_routes adds all expected route tables to the application."""
    app = Mock(spec=web.Application)

    with (
        patch("cityhive.app.routes.main.web_routes") as mock_web_routes,
        patch("cityhive.app.routes.main.monitoring_routes") as mock_monitoring_routes,
        patch("cityhive.app.routes.main.user_routes") as mock_user_routes,
        patch("cityhive.app.routes.main.hive_routes") as mock_hive_routes,
    ):
        setup_routes(app)

        expected_calls = [
            mock_web_routes,
            mock_monitoring_routes,
            mock_user_routes,
            mock_hive_routes,
        ]

        assert app.add_routes.call_count == 4
        for expected_call in expected_calls:
            app.add_routes.assert_any_call(expected_call)


def test_setup_static_routes_configures_static_serving():
    """Test that setup_static_routes configures static file serving."""
    app = Mock(spec=web.Application)

    with patch("cityhive.app.routes.main.PROJECT_DIR") as mock_project_dir:
        setup_static_routes(app)

        app.router.add_static.assert_called_once_with(
            "/static/",
            path=mock_project_dir / "static",
            name="static",
        )


def test_create_api_subapp_returns_web_application():
    """Test that create_api_subapp returns a web.Application instance."""
    result = create_api_subapp()

    assert isinstance(result, web.Application)


def test_setup_subapps_does_nothing():
    """Test that setup_subapps currently does nothing (placeholder)."""
    app = Mock(spec=web.Application)

    setup_subapps(app)

    assert not app.method_calls
