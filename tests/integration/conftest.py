"""
Integration test configuration and fixtures.

This module provides configuration specific to integration tests,
following pytest and aiohttp best practices for logging control
and test isolation.
"""

import logging

import pytest


@pytest.fixture(autouse=True, scope="function")
def configure_integration_test_logging(caplog):
    """
    Configure logging for integration tests to reduce noise.

    Best practices implemented:
    - Suppress INFO level logs by default for cleaner test output
    - Keep WARNING and ERROR logs visible for debugging
    - Allow override via pytest command-line options
    - Maintain structured logging when enabled

    Usage:
        # Silent tests (default):
        pytest tests/integration/

        # Enable verbose logging for debugging:
        pytest tests/integration/ --log-cli-level=INFO -s

        # Enable debug level logging:
        pytest tests/integration/ --log-cli-level=DEBUG -s
    """
    caplog.set_level(logging.WARNING)

    loggers_to_suppress = [
        "cityhive",
        "aiohttp.access",
        "asyncio",
        "urllib3",
    ]

    original_levels = {}

    for logger_name in loggers_to_suppress:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.WARNING)

    yield

    for logger_name, original_level in original_levels.items():
        logging.getLogger(logger_name).setLevel(original_level)


@pytest.fixture
def enable_debug_logging(caplog):
    """
    Fixture to explicitly enable debug logging for specific tests.

    Use this fixture when you need detailed logging for debugging
    a specific integration test.

    Example:
        def test_complex_integration(enable_debug_logging, full_app_client):
            # This test will show all log messages including DEBUG
            ...
    """
    caplog.set_level(logging.DEBUG)

    debug_loggers = [
        "cityhive",
        "aiohttp",
        "asyncio",
        "sqlalchemy.engine",
    ]

    for logger_name in debug_loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)
