"""Unit tests for InspectionCreationInput validation."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from cityhive.domain.inspection.service import InspectionCreationInput


def test_valid_inspection_creation_input_with_notes():
    """Test valid input with all fields."""
    tomorrow = date.today() + timedelta(days=1)
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=tomorrow,
        notes="Check the condition of the wax and add a new frame",
    )

    assert input_data.hive_id == 42
    assert input_data.scheduled_for == tomorrow
    assert input_data.notes == "Check the condition of the wax and add a new frame"


def test_valid_inspection_creation_input_without_notes():
    """Test valid input without notes."""
    tomorrow = date.today() + timedelta(days=1)
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=tomorrow,
        notes=None,
    )

    assert input_data.hive_id == 42
    assert input_data.scheduled_for == tomorrow
    assert input_data.notes is None


def test_inspection_creation_input_with_empty_string_notes_converts_to_none():
    """Test that empty string notes are converted to None."""
    tomorrow = date.today() + timedelta(days=1)
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=tomorrow,
        notes="",
    )

    assert input_data.notes is None


def test_inspection_creation_input_with_whitespace_notes_preserves_content():
    """Test that whitespace is stripped but content is preserved."""
    tomorrow = date.today() + timedelta(days=1)
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=tomorrow,
        notes="  Check the wax  ",
    )

    assert input_data.notes == "Check the wax"


def test_inspection_creation_input_hive_id_must_be_positive():
    """Test that hive_id must be greater than 0."""
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        InspectionCreationInput(
            hive_id=0,
            scheduled_for=tomorrow,
            notes=None,
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "greater_than"
    assert errors[0]["loc"] == ("hive_id",)


def test_inspection_creation_input_hive_id_cannot_be_negative():
    """Test that hive_id cannot be negative."""
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        InspectionCreationInput(
            hive_id=-1,
            scheduled_for=tomorrow,
            notes=None,
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "greater_than"


def test_inspection_creation_input_scheduled_for_cannot_be_in_past():
    """Test that scheduled_for cannot be in the past."""
    yesterday = date.today() - timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        InspectionCreationInput(
            hive_id=42,
            scheduled_for=yesterday,
            notes=None,
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert "past" in str(errors[0]["msg"])


def test_inspection_creation_input_scheduled_for_today_is_valid():
    """Test that scheduling for today is valid."""
    today = date.today()
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=today,
        notes=None,
    )

    assert input_data.scheduled_for == today


def test_inspection_creation_input_scheduled_for_future_is_valid():
    """Test that scheduling for the future is valid."""
    future_date = date.today() + timedelta(days=30)
    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=future_date,
        notes=None,
    )

    assert input_data.scheduled_for == future_date


def test_inspection_creation_input_notes_max_length():
    """Test that notes have a maximum length limit."""
    tomorrow = date.today() + timedelta(days=1)
    long_notes = "x" * 1001

    with pytest.raises(ValidationError) as exc_info:
        InspectionCreationInput(
            hive_id=42,
            scheduled_for=tomorrow,
            notes=long_notes,
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "string_too_long"


def test_inspection_creation_input_notes_at_max_length_is_valid():
    """Test that notes at exactly max length are valid."""
    tomorrow = date.today() + timedelta(days=1)
    notes_at_limit = "x" * 1000

    input_data = InspectionCreationInput(
        hive_id=42,
        scheduled_for=tomorrow,
        notes=notes_at_limit,
    )

    assert input_data.notes == notes_at_limit
    assert input_data.notes is not None and len(input_data.notes) == 1000


@pytest.mark.parametrize(
    "invalid_hive_id",
    [
        "not_a_number",
        None,
        3.14,
        [],
        {},
    ],
)
def test_inspection_creation_input_invalid_hive_id_types(invalid_hive_id):
    """Test that invalid hive_id types raise ValidationError."""
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError):
        InspectionCreationInput(
            hive_id=invalid_hive_id,
            scheduled_for=tomorrow,
            notes=None,
        )


def test_inspection_creation_input_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        InspectionCreationInput(
            hive_id=-1,
            scheduled_for=date.today() - timedelta(days=1),
            notes=None,
        )

    errors = exc_info.value.errors()
    assert len(errors) >= 2
    has_hive_id_error = any("hive_id" in error.get("loc", []) for error in errors)
    has_scheduled_for_error = any(
        "scheduled_for" in error.get("loc", []) for error in errors
    )
    assert has_hive_id_error
    assert has_scheduled_for_error
