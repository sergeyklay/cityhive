"""Unit tests for cityhive.domain.hive.exceptions module."""

import pytest

from cityhive.domain.hive.exceptions import (
    HiveError,
    InvalidLocationError,
    UserNotFoundError,
)


def test_hive_error_inherits_from_exception():
    error = HiveError("test message")

    assert isinstance(error, Exception)


def test_invalid_location_error_inherits_from_hive_error():
    error = InvalidLocationError("Invalid coordinates")

    assert isinstance(error, HiveError)
    assert isinstance(error, Exception)


def test_user_not_found_error_inherits_from_hive_error():
    error = UserNotFoundError(123)

    assert isinstance(error, HiveError)
    assert isinstance(error, Exception)


@pytest.mark.parametrize(
    "message",
    [
        "Invalid coordinates provided",
        "Location out of bounds",
        "",
        "Latitude must be between -90 and 90",
    ],
)
def test_invalid_location_error_stores_message_correctly(message):
    error = InvalidLocationError(message)

    assert str(error) == message
    assert error.message == message


@pytest.mark.parametrize(
    "user_id,expected_message",
    [
        (123, "User with ID 123 not found"),
        (0, "User with ID 0 not found"),
        (-1, "User with ID -1 not found"),
        (999999, "User with ID 999999 not found"),
    ],
)
def test_user_not_found_error_formats_message_correctly(user_id, expected_message):
    error = UserNotFoundError(user_id)

    assert str(error) == expected_message
    assert error.user_id == user_id
