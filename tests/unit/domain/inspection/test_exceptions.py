"""Unit tests for cityhive.domain.inspection.exceptions module."""

import pytest

from cityhive.domain.inspection.exceptions import (
    HiveNotFoundError,
    InspectionError,
    InvalidScheduleError,
)


def test_inspection_error_inherits_from_exception():
    error = InspectionError("test message")

    assert isinstance(error, Exception)


def test_invalid_schedule_error_inherits_from_inspection_error():
    error = InvalidScheduleError("Invalid schedule date")

    assert isinstance(error, InspectionError)
    assert isinstance(error, Exception)


def test_hive_not_found_error_inherits_from_inspection_error():
    error = HiveNotFoundError(123)

    assert isinstance(error, InspectionError)
    assert isinstance(error, Exception)


@pytest.mark.parametrize(
    "message",
    [
        "Scheduled date cannot be in the past",
        "Inspection cannot be scheduled more than 1 year in advance",
        "",
        "Invalid schedule provided",
    ],
)
def test_invalid_schedule_error_stores_message_correctly(message):
    error = InvalidScheduleError(message)

    assert str(error) == message
    assert error.message == message


@pytest.mark.parametrize(
    "hive_id,expected_message",
    [
        (123, "Hive with ID 123 not found"),
        (0, "Hive with ID 0 not found"),
        (-1, "Hive with ID -1 not found"),
        (999999, "Hive with ID 999999 not found"),
    ],
)
def test_hive_not_found_error_formats_message_correctly(hive_id, expected_message):
    error = HiveNotFoundError(hive_id)

    assert str(error) == expected_message
    assert error.hive_id == hive_id
