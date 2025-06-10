"""
Tests for validation helpers.

These tests cover email validation, field validation, and sanitization functions.
"""

import pytest

from cityhive.app.helpers.validation import (
    ValidationResult,
    get_normalized_email,
    sanitize_email_field,
    sanitize_numeric_field,
    sanitize_string_field,
    validate_coordinates,
    validate_email,
    validate_latitude,
    validate_longitude,
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


# Latitude validation tests


@pytest.mark.parametrize(
    "latitude,expected_valid,expected_error",
    [
        (45.5, True, None),
        (0.0, True, None),
        (90.0, True, None),
        (-90.0, True, None),
        (None, True, None),
        (91.0, False, "Latitude must be between -90 and 90 degrees"),
        (-91.0, False, "Latitude must be between -90 and 90 degrees"),
        (180.0, False, "Latitude must be between -90 and 90 degrees"),
    ],
)
def test_validate_latitude_with_various_values_returns_expected_validation(
    latitude: float | None, expected_valid: bool, expected_error: str | None
):
    result = validate_latitude(latitude)

    assert result.is_valid == expected_valid
    assert result.error_message == expected_error


@pytest.mark.parametrize(
    "invalid_latitude",
    [
        "invalid_string",
        "not_a_number",
        "abc123",
        "45.5.5",
        "45,5",
        "",
        "   ",
        [],
        {},
        set(),
        object(),
        complex(1, 2),
    ],
)
def test_validate_latitude_with_invalid_types_returns_type_error(invalid_latitude):
    """Test that invalid types trigger the except (ValueError, TypeError) block."""
    result = validate_latitude(invalid_latitude)

    assert result.is_valid is False
    assert result.error_message == "Latitude must be a valid number"


def test_validate_latitude_returns_validation_result_instance():
    result = validate_latitude(45.5)

    assert isinstance(result, ValidationResult)


@pytest.mark.parametrize(
    "longitude,expected_valid,expected_error",
    [
        (-73.5, True, None),
        (0.0, True, None),
        (180.0, True, None),
        (-180.0, True, None),
        (None, True, None),
        (181.0, False, "Longitude must be between -180 and 180 degrees"),
        (-181.0, False, "Longitude must be between -180 and 180 degrees"),
        (360.0, False, "Longitude must be between -180 and 180 degrees"),
    ],
)
def test_validate_longitude_with_various_values_returns_expected_validation(
    longitude: float | None, expected_valid: bool, expected_error: str | None
):
    result = validate_longitude(longitude)

    assert result.is_valid == expected_valid
    assert result.error_message == expected_error


@pytest.mark.parametrize(
    "invalid_longitude",
    [
        "invalid_string",
        "not_a_number",
        "xyz789",
        "-73.5.2",
        "-73,5",
        "",
        "   ",
        [],
        {},
        set(),
        object(),
        complex(1, 2),
        (),
    ],
)
def test_validate_longitude_with_invalid_types_returns_type_error(invalid_longitude):
    """Test that invalid types trigger the except (ValueError, TypeError) block."""
    result = validate_longitude(invalid_longitude)

    assert result.is_valid is False
    assert result.error_message == "Longitude must be a valid number"


def test_validate_longitude_returns_validation_result_instance():
    result = validate_longitude(-73.5)

    assert isinstance(result, ValidationResult)


@pytest.mark.parametrize(
    "latitude,longitude,expected_valid,expected_error",
    [
        (45.5, -73.5, True, None),
        (None, None, True, None),
        (45.5, None, False, "Both latitude and longitude must be provided together"),
        (None, -73.5, False, "Both latitude and longitude must be provided together"),
        (91.0, -73.5, False, "Latitude must be between -90 and 90 degrees"),
        (45.5, 181.0, False, "Longitude must be between -180 and 180 degrees"),
    ],
)
def test_validate_coordinates_with_various_values_returns_expected_validation(
    latitude: float | None,
    longitude: float | None,
    expected_valid: bool,
    expected_error: str | None,
):
    result = validate_coordinates(latitude, longitude)

    assert result.is_valid == expected_valid
    assert result.error_message == expected_error


def test_validate_coordinates_with_invalid_latitude_type_returns_error():
    """Test that invalid latitude types are caught by coordinate validation."""
    result = validate_coordinates("invalid", -73.5)  # type: ignore

    assert result.is_valid is False
    assert result.error_message == "Latitude must be a valid number"


def test_validate_coordinates_with_invalid_longitude_type_returns_error():
    """Test that invalid longitude types are caught by coordinate validation."""
    result = validate_coordinates(45.5, "invalid")  # type: ignore

    assert result.is_valid is False
    assert result.error_message == "Longitude must be a valid number"


def test_validate_coordinates_returns_validation_result_instance():
    result = validate_coordinates(45.5, -73.5)

    assert isinstance(result, ValidationResult)


def test_sanitize_numeric_field_returns_none_for_none_input():
    result = sanitize_numeric_field(None)

    assert result is None


def test_sanitize_numeric_field_returns_none_for_empty_string():
    result = sanitize_numeric_field("")

    assert result is None


def test_sanitize_numeric_field_returns_none_for_whitespace_string():
    result = sanitize_numeric_field("   ")

    assert result is None


@pytest.mark.parametrize(
    "input_value,expected_output",
    [
        (42, 42.0),
        (42.5, 42.5),
        (-10, -10.0),
        (0, 0.0),
        (3.14159, 3.14159),
    ],
)
def test_sanitize_numeric_field_converts_numeric_types_to_float(
    input_value, expected_output
):
    result = sanitize_numeric_field(input_value)

    assert result == expected_output
    assert isinstance(result, float)


@pytest.mark.parametrize(
    "input_string,expected_output",
    [
        ("42", 42.0),
        ("42.5", 42.5),
        ("-10", -10.0),
        ("0", 0.0),
        ("3.14159", 3.14159),
        ("  45.5  ", 45.5),
        ("-73.123", -73.123),
    ],
)
def test_sanitize_numeric_field_converts_valid_numeric_strings_to_float(
    input_string, expected_output
):
    result = sanitize_numeric_field(input_string)

    assert result == expected_output
    assert isinstance(result, float)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "invalid",
        "abc123",
        "12.34.56",
        "not_a_number",
        "42x",
        "x42",
        "42 43",
        "12,34",
    ],
)
def test_sanitize_numeric_field_returns_none_for_invalid_strings(invalid_input):
    result = sanitize_numeric_field(invalid_input)

    assert result is None


@pytest.mark.parametrize(
    "special_input",
    [
        "NaN",
        "inf",
        "infinity",
        "-inf",
        "-infinity",
    ],
)
def test_sanitize_numeric_field_converts_special_float_strings(special_input):
    result = sanitize_numeric_field(special_input)

    assert isinstance(result, float)


def test_sanitize_numeric_field_handles_unsupported_types():
    result = sanitize_numeric_field(object())  # type: ignore[arg-type]

    assert result is None
