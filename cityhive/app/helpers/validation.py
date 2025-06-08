"""
Validation helpers for web request processing.

This module contains reusable validation functions for processing
HTTP request data in the aiohttp web application layer.
"""

from typing import NamedTuple

from emval import EmailValidator


class ValidationResult(NamedTuple):
    """Result of a validation operation."""

    is_valid: bool
    error_message: str | None = None


# Create a configured email validator that doesn't check domain deliverability
# This allows for faster validation without MX record lookups
_email_validator = EmailValidator(
    allow_smtputf8=True,
    allow_empty_local=False,
    allow_quoted_local=False,
    allow_domain_literal=False,
    deliverable_address=False,
)


def validate_email(email: str) -> ValidationResult:
    """
    Validate email format using emval (Rust-based RFC 5322/6531 compliant validator).

    Uses emval library which is 100-1000x faster than traditional validators
    and properly implements RFC 5322 and RFC 6531 standards.

    Args:
        email: Email address string to validate

    Returns:
        ValidationResult with validity status and optional error message

    Examples:
        >>> validate_email("user@example.com")
        ValidationResult(is_valid=True, error_message=None)

        >>> validate_email("invalid-email")
        ValidationResult(is_valid=False, error_message="Invalid email format")
    """
    if not email:
        return ValidationResult(False, "Email is required")

    try:
        # Use configured emval validator for fast, RFC-compliant email validation
        _email_validator.validate_email(email)
        return ValidationResult(True)
    except SyntaxError:
        # emval raises SyntaxError for invalid email format
        return ValidationResult(False, "Invalid email format")
    except Exception:
        # Handle any unexpected errors gracefully
        return ValidationResult(False, "Invalid email format")


def validate_required_field(value: str | None, field_name: str) -> ValidationResult:
    """
    Validate that a required field is present and not empty.

    Args:
        value: Field value to validate (may be None)
        field_name: Name of the field for error messages

    Returns:
        ValidationResult with validity status and optional error message

    Examples:
        >>> validate_required_field("John", "Name")
        ValidationResult(is_valid=True, error_message=None)

        >>> validate_required_field("", "Name")
        ValidationResult(is_valid=False, error_message="Name is required")
    """
    if not value or not value.strip():
        return ValidationResult(False, f"{field_name} is required")

    return ValidationResult(True)


def sanitize_string_field(value: str | None) -> str:
    """
    Sanitize string input by stripping whitespace and handling None values.

    Args:
        value: Input string value (may be None)

    Returns:
        Sanitized string (empty string if None)

    Examples:
        >>> sanitize_string_field("  hello  ")
        'hello'

        >>> sanitize_string_field(None)
        ''
    """
    if value is None:
        return ""
    return value.strip()


def sanitize_email_field(value: str | None) -> str:
    """
    Sanitize email input by stripping whitespace and converting to lowercase.

    Args:
        value: Email string value (may be None)

    Returns:
        Sanitized email string (empty string if None)

    Examples:
        >>> sanitize_email_field("  User@Example.COM  ")
        'user@example.com'

        >>> sanitize_email_field(None)
        ''
    """
    sanitized = sanitize_string_field(value)
    return sanitized.lower()


def get_normalized_email(email: str) -> str | None:
    """
    Get normalized email address using emval.

    Args:
        email: Email address to normalize

    Returns:
        Normalized email address or None if invalid

    Examples:
        >>> get_normalized_email("User@Example.COM")
        'user@example.com'

        >>> get_normalized_email("invalid-email")
        None
    """
    try:
        validated_email = _email_validator.validate_email(email)
        return validated_email.normalized
    except (SyntaxError, Exception):
        return None


def validate_latitude(latitude: float | None) -> ValidationResult:
    """
    Validate latitude coordinate.

    Args:
        latitude: Latitude value to validate

    Returns:
        ValidationResult with validity status and optional error message

    Examples:
        >>> validate_latitude(45.5)
        ValidationResult(is_valid=True, error_message=None)

        >>> validate_latitude(95.0)
        ValidationResult(is_valid=False, error_message="...")
    """
    if latitude is None:
        return ValidationResult(True)  # Optional field

    try:
        lat_float = float(latitude)
        if -90.0 <= lat_float <= 90.0:
            return ValidationResult(True)
        return ValidationResult(False, "Latitude must be between -90 and 90 degrees")
    except (ValueError, TypeError):
        return ValidationResult(False, "Latitude must be a valid number")


def validate_longitude(longitude: float | None) -> ValidationResult:
    """
    Validate longitude coordinate.

    Args:
        longitude: Longitude value to validate

    Returns:
        ValidationResult with validity status and optional error message

    Examples:
        >>> validate_longitude(-73.5)
        ValidationResult(is_valid=True, error_message=None)

        >>> validate_longitude(185.0)
        ValidationResult(is_valid=False, error_message="...")
    """
    if longitude is None:
        return ValidationResult(True)  # Optional field

    try:
        lon_float = float(longitude)
        if -180.0 <= lon_float <= 180.0:
            return ValidationResult(True)
        return ValidationResult(False, "Longitude must be between -180 and 180 degrees")
    except (ValueError, TypeError):
        return ValidationResult(False, "Longitude must be a valid number")


def validate_coordinates(
    latitude: float | None, longitude: float | None
) -> ValidationResult:
    """
    Validate coordinate pair consistency.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        ValidationResult with validity status and optional error message

    Examples:
        >>> validate_coordinates(45.5, -73.5)
        ValidationResult(is_valid=True, error_message=None)

        >>> validate_coordinates(45.5, None)
        ValidationResult(is_valid=False, error_message="...")
    """
    # Both must be provided together or both must be None
    if (latitude is None) != (longitude is None):
        return ValidationResult(
            False, "Both latitude and longitude must be provided together"
        )

    # If both are None, that's valid (no location)
    if latitude is None and longitude is None:
        return ValidationResult(True)

    # Validate individual coordinates
    lat_result = validate_latitude(latitude)
    if not lat_result.is_valid:
        return lat_result

    lon_result = validate_longitude(longitude)
    if not lon_result.is_valid:
        return lon_result

    return ValidationResult(True)


def sanitize_numeric_field(value: str | float | int | None) -> float | None:
    """
    Sanitize numeric input field.

    Args:
        value: Numeric value to sanitize

    Returns:
        Sanitized float value or None if invalid/empty

    Examples:
        >>> sanitize_numeric_field("45.5")
        45.5

        >>> sanitize_numeric_field("")
        None

        >>> sanitize_numeric_field("invalid")
        None
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    return None
