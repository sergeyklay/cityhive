# Coding Standards

CityHive follows modern Python development practices with a focus on clean, maintainable code.

## General Python Standards

- **Python Version**: Use Python 3.12 features and syntax
- **Line Length**: 88 characters maximum (ruff/black default)
- **Indentation**: 4 spaces, never tabs
- **Naming Conventions**:
  - Classes: `CamelCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private attributes: `_single_underscore`

## Meaningful Names

Use descriptive names that clearly communicate intent:

```python
# ✅ DO: Clear, descriptive names
async def create_beehive_inspection(
    session: AsyncSession,
    beehive_id: int,
    inspector_notes: str,
    health_score: float,
) -> InspectionModel:
    """Create a new beehive inspection record."""

# ❌ DON'T: Cryptic abbreviations
async def cr_bh_insp(s, bid, n, hs):
    """Create inspection."""
```

## Type Hints Usage

Use modern type hints following PEP 604 and PEP 585:

```python
# ✅ DO: Modern union syntax and built-in generics
from collections.abc import Sequence

def process_beehives(
    hives: list[BeehiveModel],
    filters: dict[str, str | int] | None = None,
) -> Sequence[ProcessedHive]:
    """Process beehives with optional filters."""

# ❌ DON'T: Legacy typing imports
from typing import List, Dict, Optional, Union

def process_beehives(
    hives: List[BeehiveModel],
    filters: Optional[Dict[str, Union[str, int]]] = None,
) -> List[ProcessedHive]:
```

## Docstrings

Use Google-style docstrings for all public APIs:

```python
async def schedule_inspection(
    session: AsyncSession,
    beehive_id: int,
    inspection_date: datetime,
    inspector_id: int,
) -> InspectionSchedule:
    """Schedule a beehive inspection.

    Args:
        session: Database session for the operation
        beehive_id: ID of the beehive to inspect
        inspection_date: When the inspection should occur
        inspector_id: ID of the assigned inspector

    Returns:
        The created inspection schedule

    Raises:
        BeehiveNotFoundError: If the beehive doesn't exist
        InspectorUnavailableError: If inspector is not available
        ValidationError: If the inspection date is invalid
    """
```

## Comments

Avoid obvious comments. Target audience is senior Python developers:

```python
# ✅ DO: Explain complex business logic or non-obvious decisions
# Use Haversine formula for accurate distance calculation with spatial coordinates
distance = calculate_haversine_distance(hive_location, inspector_location)

# Apply temperature correction factor for winter inspections
if inspection_date.month in (12, 1, 2):
    health_score *= WINTER_ADJUSTMENT_FACTOR

# ❌ DON'T: State the obvious
beehive_count += 1  # Increment beehive count
for hive in hives:  # Loop through hives
    print(hive.name)  # Print hive name
```

## Exception Handling

Always use explicit exception chaining for better debugging:

```python
# ✅ DO: Preserve original exception context
async def fetch_beehive_data(hive_id: int) -> BeehiveData:
    try:
        response = await http_client.get(f"/api/hives/{hive_id}")
        return BeehiveData.model_validate(response.json())
    except httpx.HTTPError as e:
        raise BeehiveAPIError(f"Failed to fetch hive {hive_id}") from e
    except ValidationError as e:
        raise BeehiveDataError(f"Invalid data for hive {hive_id}") from e

# ❌ DON'T: Lose original exception context
async def fetch_beehive_data(hive_id: int) -> BeehiveData:
    try:
        response = await http_client.get(f"/api/hives/{hive_id}")
        return BeehiveData.model_validate(response.json())
    except Exception:
        raise BeehiveAPIError("Something went wrong")
```

## Async Patterns

Follow proper async/await patterns throughout:

```python
# ✅ DO: Proper async context managers and resource cleanup
async def process_sensor_data(sensor_id: int) -> ProcessingResult:
    async with get_database_session() as session:
        sensor = await session.get(SensorModel, sensor_id)
        if not sensor:
            raise SensorNotFoundError(f"Sensor {sensor_id} not found")

        async with httpx.AsyncClient() as client:
            raw_data = await client.get(sensor.endpoint_url)
            processed_data = await process_raw_sensor_data(raw_data.json())

        await session.merge(processed_data)
        await session.commit()
        return ProcessingResult(success=True, sensor_id=sensor_id)

# ❌ DON'T: Mix sync and async or forget resource cleanup
def process_sensor_data(sensor_id: int):
    session = get_database_session()  # Missing async context
    client = httpx.Client()  # Sync client in async context
    # ... processing without proper cleanup
```

## Resource Management

Use context managers for all resource management:

```python
# ✅ DO: Proper resource management
async def backup_beehive_data(hive_id: int) -> None:
    async with get_database_session() as session:
        hive_data = await session.execute(
            select(BeehiveModel).where(BeehiveModel.id == hive_id)
        )

        with open(f"backup_hive_{hive_id}.json", "w") as backup_file:
            json.dump(hive_data.scalars().first().to_dict(), backup_file)

# ❌ DON'T: Manual resource management
async def backup_beehive_data(hive_id: int) -> None:
    session = get_database_session()
    backup_file = open(f"backup_hive_{hive_id}.json", "w")
    # ... forget to close resources
```

## Logging Guidelines

Use structlog for structured, machine-readable logging:

```python
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)

# ✅ DO: Structured logging with key-value pairs
logger.info(
    "Processing beehive inspection",
    beehive_id=hive_id,
    inspector_id=inspector_id,
    inspection_type=inspection_type,
)

logger.error(
    "Failed to process sensor data",
    beehive_id=hive_id,
    error_type="timeout",
    retry_count=3,
)

# ✅ DO: Context binding for related operations
inspection_logger = logger.bind(
    beehive_id=hive_id,
    inspector_id=inspector_id,
    inspection_date=inspection_date.isoformat(),
)

inspection_logger.info("Inspection started")
inspection_logger.info("Health score calculated", score=0.89)
inspection_logger.info("Inspection completed", status="success")

# ❌ DON'T: String formatting or f-strings in logging
logger.info(f"Processing beehive {hive_id} inspection")  # Bypasses structured logging
logger.error("Failed to process sensor data for hive %s", hive_id)  # Old format
```

## Import Organization

Organize imports in clear groups:

```python
# Standard library imports
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Third-party imports
import httpx
from aiohttp import web
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

# First-party imports
from cityhive.domain.models.beehive import BeehiveModel
from cityhive.domain.services.inspection import InspectionService
from cityhive.infrastructure.database.session import get_session
from cityhive.infrastructure.logging import get_logger

# Initialize structured logger
logger = get_logger(__name__)
```
