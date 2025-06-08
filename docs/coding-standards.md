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

## Testing Standards

Follow pytest best practices with emphasis on maintainable, reusable test code:

### Test Structure

- **Pure functional style**: Use plain functions, avoid class-based tests
- **Clear naming**: Tests should describe what is being tested and expected outcome
- **DRY principle**: Extract common setup into reusable fixtures

```python
# ✅ DO: Descriptive test name and clean structure
async def test_beehive_inspection_with_valid_data_creates_record(
    client_with_db, inspection_data, mock_inspector
):
    async with client_with_db.post("/api/inspections", json=inspection_data) as response:
        assert response.status == 201
        data = await response.json()
        assert data["beehive_id"] == inspection_data["beehive_id"]

# ❌ DON'T: Vague names and repetitive setup
async def test_inspection(aiohttp_client):
    app = web.Application()  # Repetitive setup
    app[db_key] = session_maker  # Should be in fixture
    client = await aiohttp_client(app)
    # Test logic...
```

### Test Performance and Resource Management

**Choose appropriate testing strategy for performance and reliability:**

- **Unit Tests**: Direct function calls for validation and business logic
  - Use `make_mocked_request` from `aiohttp.test_utils`
  - No HTTP infrastructure, no resource leaks
  - Execution: ~0.25 seconds for 42 tests
  - Perfect for validation logic, error handling, data transformation

- **Integration Tests**: Full HTTP cycle for critical user journeys
  - Use `aiohttp_client` sparingly for end-to-end validation
  - Test middleware, routing, and complete request pipeline
  - Slower execution but validates real user experience

```python
# ✅ DO: Fast unit testing for validation logic
async def test_email_validation_rejects_invalid_format():
    data = {"name": "John", "email": "invalid-email"}
    request = make_mocked_request("POST", "/api/users")
    request.json = AsyncMock(return_value=data)

    response = await create_user(request)
    assert response.status == 400

# ✅ DO: Integration testing for critical paths only
async def test_complete_user_registration_workflow(aiohttp_client, app_with_db):
    client = await aiohttp_client(app_with_db)
    response = await client.post("/api/users", json=valid_user_data)
    assert response.status == 201

# ❌ DON'T: Use integration tests for simple validation
async def test_validation_logic(aiohttp_client):  # Unnecessary overhead
    app = web.Application()
    client = await aiohttp_client(app)  # Creates test server
    # This is unit testing disguised as integration testing
```

### Resource Leak Prevention

**Prevent "Too many open files" and DNS resolver warnings:**

- **Avoid networking in unit tests**: Eliminates resource leaks and DNS warnings
- **Use direct function calls**: Test view functions without HTTP infrastructure
- **Mock external dependencies**: Prevent real network calls in tests

```python
# ✅ DO: Resource-safe unit testing
from aiohttp.test_utils import make_mocked_request
from unittest.mock import AsyncMock

async def test_user_creation_without_networking():
    # No HTTP server, no networking, no resource leaks
    request = make_mocked_request("POST", "/api/users", app=app_with_db)
    request.json = AsyncMock(return_value=user_data)

    response = await create_user(request)
    assert response.status == 201

# ❌ DON'T: Create HTTP infrastructure for unit tests
async def test_user_creation_with_overhead(aiohttp_client):
    app = web.Application()  # Unnecessary overhead
    client = await aiohttp_client(app)  # Can cause resource leaks
    response = await client.post("/api/users", json=user_data)
```

### Fixture Organization

Follow "Local when possible, shared when necessary" principle:

**Move to `tests/conftest.py`:**
- Cross-module utilities (AsyncMock context managers)
- Core infrastructure patterns (database session mocks)
- Stable, reusable helpers

**Keep in test files:**
- Domain-specific test data
- Feature-specific fixtures that change frequently
- Complex setup scenarios

```python
# ✅ DO: Shared infrastructure in conftest.py
@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    return AsyncMock()

@pytest.fixture
def session_maker(mock_session):
    """Create a session maker function that returns a context manager."""
    def _session_maker():
        return MockAsyncContextManager(mock_session)
    return _session_maker

# ✅ DO: Domain-specific fixtures in test files
@pytest.fixture
def inspection_data():
    return {
        "beehive_id": 1,
        "inspector_notes": "Colony appears healthy",
        "health_score": 0.89
    }
```

### Composable Fixtures

Build hierarchical fixtures that compose cleanly:

```python
# ✅ DO: Composable fixture hierarchy
@pytest.fixture
def base_app():
    """Basic aiohttp application with routes."""
    app = web.Application()
    app.router.add_post("/api/inspections", create_inspection)
    return app

@pytest.fixture
def app_with_db(base_app, session_maker):
    """Application with database configured."""
    base_app[db_key] = session_maker
    return base_app

@pytest.fixture
async def client_with_db(aiohttp_client, app_with_db):
    """Test client with database configured."""
    return await aiohttp_client(app_with_db)
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

---

**See also:**
- [Development Guide](docs/development.md) for setup and workflow instructions
