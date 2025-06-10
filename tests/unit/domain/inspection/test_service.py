"""
Unit tests for InspectionService.

Tests demonstrate improved testability with dependency injection and mocking.
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from cityhive.domain.inspection.exceptions import (
    HiveNotFoundError,
    InvalidScheduleError,
)
from cityhive.domain.inspection.repository import InspectionRepository
from cityhive.domain.inspection.service import (
    InspectionCreationInput,
    InspectionService,
)
from cityhive.domain.models import Hive, Inspection


@pytest.fixture
def mock_inspection_repository():
    """Mock inspection repository for testing."""
    return AsyncMock(spec=InspectionRepository)


@pytest.fixture
def inspection_service(mock_inspection_repository):
    """Inspection service with mocked dependencies."""
    return InspectionService(mock_inspection_repository)


@pytest.fixture
def valid_creation_input():
    """Valid inspection creation input."""
    return InspectionCreationInput(
        hive_id=1,
        scheduled_for=date(2025, 6, 15),
        notes="Check the condition of the wax and add a new frame",
    )


@pytest.fixture
def minimal_creation_input():
    """Minimal inspection creation input."""
    return InspectionCreationInput(
        hive_id=1,
        scheduled_for=date(2025, 6, 15),
        notes=None,
    )


@pytest.fixture
def sample_hive():
    """Sample hive model."""
    hive = Hive(user_id=1, name="Test Hive", frame_type="Langstroth")
    hive.id = 1
    return hive


@pytest.fixture
def sample_inspection():
    """Sample inspection model."""
    inspection = Inspection(
        hive_id=1,
        scheduled_for=date(2025, 6, 15),
        notes="Check the condition of the wax and add a new frame",
    )
    inspection.id = 1
    inspection.created_at = datetime(2025, 6, 10, 14, 20, tzinfo=timezone.utc)
    return inspection


async def test_create_inspection_success_with_notes(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    valid_creation_input: InspectionCreationInput,
    sample_hive: Hive,
    sample_inspection: Inspection,
):
    """Test successful inspection creation with notes."""
    mock_inspection_repository.get_hive_by_id.return_value = sample_hive
    mock_inspection_repository.save.return_value = sample_inspection

    result = await inspection_service.create_inspection(valid_creation_input)

    assert isinstance(result, Inspection)
    assert result.id == sample_inspection.id
    assert result.hive_id == sample_inspection.hive_id
    assert result.scheduled_for == sample_inspection.scheduled_for

    mock_inspection_repository.get_hive_by_id.assert_called_once_with(1)
    mock_inspection_repository.save.assert_called_once()


async def test_create_inspection_success_without_notes(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    minimal_creation_input: InspectionCreationInput,
    sample_hive: Hive,
    sample_inspection: Inspection,
):
    """Test successful inspection creation without notes."""
    mock_inspection_repository.get_hive_by_id.return_value = sample_hive
    mock_inspection_repository.save.return_value = sample_inspection

    result = await inspection_service.create_inspection(minimal_creation_input)

    assert isinstance(result, Inspection)
    assert result.id == sample_inspection.id

    mock_inspection_repository.get_hive_by_id.assert_called_once_with(1)
    mock_inspection_repository.save.assert_called_once()


async def test_create_inspection_hive_not_found(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    valid_creation_input: InspectionCreationInput,
):
    """Test inspection creation fails when hive doesn't exist."""
    mock_inspection_repository.get_hive_by_id.return_value = None

    with pytest.raises(HiveNotFoundError) as exc_info:
        await inspection_service.create_inspection(valid_creation_input)

    assert exc_info.value.hive_id == 1

    mock_inspection_repository.get_hive_by_id.assert_called_once_with(1)
    mock_inspection_repository.save.assert_not_called()


async def test_create_inspection_scheduled_too_far_in_future(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    sample_hive: Hive,
):
    """Test inspection creation fails when scheduled too far in the future."""
    far_future_date = date.today() + timedelta(days=366)  # >1 year ahead
    creation_input = InspectionCreationInput(
        hive_id=1,
        scheduled_for=far_future_date,
        notes=None,
    )
    mock_inspection_repository.get_hive_by_id.return_value = sample_hive

    with pytest.raises(InvalidScheduleError) as exc_info:
        await inspection_service.create_inspection(creation_input)

    assert "1 year in advance" in str(exc_info.value)
    mock_inspection_repository.save.assert_not_called()


async def test_create_inspection_database_integrity_error(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    valid_creation_input: InspectionCreationInput,
    sample_hive: Hive,
):
    """Test inspection creation fails with database integrity constraint violation."""
    mock_inspection_repository.get_hive_by_id.return_value = sample_hive
    mock_inspection_repository.save.side_effect = IntegrityError(
        "duplicate key violation", "params", Exception("orig error")
    )

    with pytest.raises(InvalidScheduleError) as exc_info:
        await inspection_service.create_inspection(valid_creation_input)

    assert "data conflict" in str(exc_info.value)
    mock_inspection_repository.save.assert_called_once()


async def test_get_inspection_by_id_found(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    sample_inspection: Inspection,
):
    """Test successful inspection lookup by ID."""
    mock_inspection_repository.get_by_id.return_value = sample_inspection

    result = await inspection_service.get_inspection_by_id(1)

    assert isinstance(result, Inspection)
    assert result.id == sample_inspection.id
    assert result.hive_id == sample_inspection.hive_id

    mock_inspection_repository.get_by_id.assert_called_once_with(1)


async def test_get_inspection_by_id_not_found(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
):
    """Test inspection lookup when inspection doesn't exist."""
    mock_inspection_repository.get_by_id.return_value = None

    result = await inspection_service.get_inspection_by_id(999)

    assert result is None
    mock_inspection_repository.get_by_id.assert_called_once_with(999)


async def test_get_inspections_by_hive_id_with_inspections(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
    sample_inspection: Inspection,
):
    """Test getting inspections for a hive that has inspections."""
    inspections = [sample_inspection]
    mock_inspection_repository.get_by_hive_id.return_value = inspections

    result = await inspection_service.get_inspections_by_hive_id(1)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == sample_inspection

    mock_inspection_repository.get_by_hive_id.assert_called_once_with(1)


async def test_get_inspections_by_hive_id_no_inspections(
    inspection_service: InspectionService,
    mock_inspection_repository: AsyncMock,
):
    """Test getting inspections for a hive that has no inspections."""
    mock_inspection_repository.get_by_hive_id.return_value = []

    result = await inspection_service.get_inspections_by_hive_id(1)

    assert isinstance(result, list)
    assert len(result) == 0

    mock_inspection_repository.get_by_hive_id.assert_called_once_with(1)
