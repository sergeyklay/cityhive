"""Unit test configuration and fixtures."""

import logging

import pytest


@pytest.fixture(autouse=True)
def suppress_unit_test_logging(caplog):
    """
    Suppress logging noise in unit tests.

    Tests that need to verify logging behavior should use mocker.patch() directly.
    """
    caplog.set_level(logging.WARNING)
