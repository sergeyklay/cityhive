"""Unit tests for cityhive.domain.user.exceptions module."""

import pytest

from cityhive.domain.user.exceptions import (
    DuplicateUserError,
    UserError,
    UserNotFoundError,
)


def test_user_error_inherits_from_exception():
    error = UserError("test message")

    assert isinstance(error, Exception)


def test_duplicate_user_error_inherits_from_user_error():
    error = DuplicateUserError("test@example.com")

    assert isinstance(error, UserError)
    assert isinstance(error, Exception)


def test_user_not_found_error_inherits_from_user_error():
    error = UserNotFoundError("test-id")

    assert isinstance(error, UserError)
    assert isinstance(error, Exception)


@pytest.mark.parametrize(
    "email,expected_message",
    [
        ("user@example.com", "User with email 'user@example.com' already exists"),
        ("test@test.com", "User with email 'test@test.com' already exists"),
        ("", "User with email '' already exists"),
    ],
)
def test_duplicate_user_error_formats_message_correctly(email, expected_message):
    error = DuplicateUserError(email)

    assert str(error) == expected_message
    assert error.email == email


@pytest.mark.parametrize(
    "identifier,expected_message",
    [
        ("123", "User not found: 123"),
        ("user@example.com", "User not found: user@example.com"),
        ("", "User not found: "),
    ],
)
def test_user_not_found_error_formats_message_correctly(identifier, expected_message):
    error = UserNotFoundError(identifier)

    assert str(error) == expected_message
    assert error.identifier == identifier
