"""
Unit tests for InspectionRepository.

Tests the repository logic with mocked database operations.
"""

from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cityhive.domain.inspection.repository import InspectionRepository
from cityhive.domain.models import Hive, Inspection


@pytest.fixture
def mock_session():
    """Mock async database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def inspection_repository(mock_session):
    """Inspection repository with mocked session."""
    return InspectionRepository(mock_session)


@pytest.fixture
def sample_inspection_data():
    """Sample inspection data for testing."""
    return {
        "hive_id": 1,
        "scheduled_for": date(2025, 6, 15),
        "notes": "Check the condition of the wax and add a new frame",
    }


@pytest.fixture
def sample_inspection(sample_inspection_data):
    """Sample inspection model."""
    inspection = Inspection(**sample_inspection_data)
    inspection.id = 1
    return inspection


@pytest.fixture
def sample_hive():
    """Sample hive model."""
    hive = Hive(user_id=1, name="Test Hive", frame_type="Langstroth")
    hive.id = 1
    return hive


async def test_save_inspection_with_valid_data_returns_inspection_with_id(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
    sample_inspection_data: dict,
):
    """Test successfully saving an inspection."""
    inspection = Inspection(**sample_inspection_data)

    mock_session.add.return_value = None
    mock_session.flush.return_value = None

    def set_inspection_id():
        inspection.id = 1

    mock_session.flush.side_effect = set_inspection_id

    result = await inspection_repository.save(inspection)

    assert result is inspection
    assert result.id == 1
    mock_session.add.assert_called_once_with(inspection)
    mock_session.flush.assert_called_once()


async def test_save_inspection_with_integrity_error_raises_exception(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
    sample_inspection_data: dict,
):
    """Test that saving an inspection with integrity constraint raises error."""
    inspection = Inspection(**sample_inspection_data)

    integrity_error = IntegrityError(
        "integrity constraint", None, Exception("constraint violation")
    )
    mock_session.flush.side_effect = integrity_error

    with pytest.raises(IntegrityError):
        await inspection_repository.save(inspection)

    mock_session.add.assert_called_once_with(inspection)
    mock_session.flush.assert_called_once()


async def test_get_hive_by_id_with_existing_hive_returns_hive(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
    sample_hive: Hive,
):
    """Test getting hive by ID when hive exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_hive
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_hive_by_id(1)

    assert result is sample_hive
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_hive_by_id_with_nonexistent_hive_returns_none(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
):
    """Test getting hive by ID when hive doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_hive_by_id(999)

    assert result is None
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_id_with_existing_inspection_returns_inspection(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
    sample_inspection: Inspection,
):
    """Test getting inspection by ID when inspection exists."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_inspection
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_by_id(1)

    assert result is sample_inspection
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_id_with_nonexistent_inspection_returns_none(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
):
    """Test getting inspection by ID when inspection doesn't exist."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_by_id(999)

    assert result is None
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


async def test_get_by_hive_id_returns_list_of_inspections(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
    sample_inspection: Inspection,
):
    """Test getting inspections by hive ID."""
    inspections = [sample_inspection]
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = inspections
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_by_hive_id(1)

    assert result == inspections
    assert isinstance(result, list)
    mock_session.execute.assert_called_once()
    mock_result.scalars.assert_called_once()
    mock_scalars.all.assert_called_once()


async def test_get_by_hive_id_with_no_inspections_returns_empty_list(
    inspection_repository: InspectionRepository,
    mock_session: AsyncMock,
):
    """Test getting inspections by hive ID when hive has no inspections."""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await inspection_repository.get_by_hive_id(1)

    assert result == []
    assert isinstance(result, list)
    mock_session.execute.assert_called_once()
    mock_result.scalars.assert_called_once()
    mock_scalars.all.assert_called_once()
