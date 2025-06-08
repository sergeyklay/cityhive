"""
Tests for validation helpers.

These tests cover email validation, field validation, and sanitization functions.
"""

import pytest

from cityhive.app.helpers.validation import (
    ValidationResult,
    get_normalized_email,
    sanitize_email_field,
    sanitize_string_field,
    validate_email,
    validate_required_field,
)


@pytest.fixture
def valid_email():
    """Valid email for testing."""
    return "test@example.com"


@pytest.fixture
def invalid_email():
    """Invalid email for testing."""
    return "invalid-email"


@pytest.fixture
def sample_field_name():
    """Sample field name for testing validation."""
    return "Name"


@pytest.mark.parametrize(
    "email,expected_valid",
    [
        ("user@example.com", True),
        ("test.email+tag@domain.co.uk", True),
        ("user123@test-domain.org", True),
        ("user@domain.com", True),
        ("", False),
        ("invalid-email", False),
        ("@domain.com", False),
        ("user@", False),
        ("user@domain", True),
        ("user.domain.com", False),
        ("user@domain.", False),
    ],
)
def test_validate_email_with_various_email_formats_returns_expected_validity(
    email: str, expected_valid: bool
):
    result = validate_email(email)

    assert result.is_valid == expected_valid
    if not expected_valid and email:
        assert result.error_message == "Invalid email format"
    elif not email:
        assert result.error_message == "Email is required"


def test_validate_email_with_valid_email_returns_validation_result_instance(
    valid_email,
):
    result = validate_email(valid_email)

    assert isinstance(result, ValidationResult)


@pytest.mark.parametrize(
    "email,expected_normalized",
    [
        ("User@Example.COM", "User@example.com"),
        ("test@domain.org", "test@domain.org"),
        ("Test.Email+Tag@Domain.CO.UK", "Test.Email+Tag@domain.co.uk"),
        ("invalid-email", None),
        ("", None),
        ("@domain.com", None),
    ],
)
def test_get_normalized_email_with_various_inputs_returns_expected_normalization(
    email: str, expected_normalized: str | None
):
    result = get_normalized_email(email)

    assert result == expected_normalized


def test_get_normalized_email_with_valid_email_returns_string_type(valid_email):
    result = get_normalized_email(valid_email)

    assert isinstance(result, str) or result is None


@pytest.mark.parametrize(
    "value,field_name,expected_valid,expected_error",
    [
        ("John", "Name", True, None),
        ("Valid Value", "Field", True, None),
        ("", "Name", False, "Name is required"),
        ("   ", "Email", False, "Email is required"),
        (None, "Field", False, "Field is required"),
    ],
)
def test_validate_required_field_with_various_values_returns_expected_validation(
    value: str | None,
    field_name: str,
    expected_valid: bool,
    expected_error: str | None,
):
    result = validate_required_field(value, field_name)

    assert result.is_valid == expected_valid
    assert result.error_message == expected_error


def test_validate_required_field_with_valid_value_returns_validation_result_instance(
    sample_field_name,
):
    result = validate_required_field("value", sample_field_name)

    assert isinstance(result, ValidationResult)


@pytest.mark.parametrize(
    "input_value,expected_output",
    [
        ("hello", "hello"),
        ("  hello  ", "hello"),
        ("", ""),
        ("   ", ""),
        (None, ""),
        ("  spaced  words  ", "spaced  words"),
    ],
)
def test_sanitize_string_field_with_various_inputs_returns_trimmed_string(
    input_value: str | None, expected_output: str
):
    result = sanitize_string_field(input_value)

    assert result == expected_output


def test_sanitize_string_field_with_any_input_returns_string_type():
    """sanitize_string_field should always return string type."""
    result = sanitize_string_field("test")

    assert isinstance(result, str)


@pytest.mark.parametrize(
    "input_value,expected_output",
    [
        ("user@example.com", "user@example.com"),
        ("  User@Example.COM  ", "user@example.com"),
        ("TEST@DOMAIN.ORG", "test@domain.org"),
        ("", ""),
        ("   ", ""),
        (None, ""),
        ("  Mixed.Case@Test.COM  ", "mixed.case@test.com"),
    ],
)
def test_sanitize_email_field_with_various_inputs_returns_normalized_lowercase_email(
    input_value: str | None, expected_output: str
):
    result = sanitize_email_field(input_value)

    assert result == expected_output


def test_sanitize_email_field_with_any_input_returns_string_type():
    result = sanitize_email_field("Test@Example.com")

    assert isinstance(result, str)
