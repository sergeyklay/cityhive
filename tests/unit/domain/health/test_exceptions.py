"""Unit tests for cityhive.domain.health.exceptions module."""

import pytest

from cityhive.domain.health.exceptions import (
    DatabaseHealthCheckError,
    HealthCheckError,
    HealthCheckTimeoutError,
)


def test_health_check_error_inherits_from_exception():
    error = HealthCheckError("test message")

    assert isinstance(error, Exception)


def test_database_health_check_error_inherits_from_health_check_error():
    error = DatabaseHealthCheckError("Database is down")

    assert isinstance(error, HealthCheckError)
    assert isinstance(error, Exception)


def test_health_check_timeout_error_inherits_from_health_check_error():
    error = HealthCheckTimeoutError("database", 5.0)

    assert isinstance(error, HealthCheckError)
    assert isinstance(error, Exception)


@pytest.mark.parametrize(
    "message,original_error",
    [
        ("Database connection failed", None),
        ("Connection timeout", ValueError("Invalid connection string")),
        ("", None),
        ("Network error", ConnectionError("Host unreachable")),
    ],
)
def test_database_health_check_error_stores_attributes_correctly(
    message, original_error
):
    error = DatabaseHealthCheckError(message, original_error)

    assert str(error) == message
    assert error.message == message
    assert error.original_error == original_error


@pytest.mark.parametrize(
    "component,timeout_seconds,expected_message",
    [
        ("database", 5.0, "database health check timed out after 5.0s"),
        ("redis", 3.5, "redis health check timed out after 3.5s"),
        ("", 0.0, " health check timed out after 0.0s"),
        ("external-api", 10.0, "external-api health check timed out after 10.0s"),
    ],
)
def test_health_check_timeout_error_formats_message_correctly(
    component, timeout_seconds, expected_message
):
    error = HealthCheckTimeoutError(component, timeout_seconds)

    assert str(error) == expected_message
    assert error.component == component
    assert error.timeout_seconds == timeout_seconds
