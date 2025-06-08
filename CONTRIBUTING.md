# Contributing to CityHive

Welcome to CityHive! This project serves as an experimental playground for modern Python web development patterns, tools, and practices. Whether you're here to explore, learn, experiment, or contribute, this guide will help you navigate the codebase effectively.

## Table of Contents

- [Project Philosophy](#project-philosophy)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Development Environment Setup](#development-environment-setup)
  - [Working with the Project](#working-with-the-project)
- [Development Workflow](#development-workflow)
  - [Creating a New Feature](#creating-a-new-feature)
  - [Bug Fixes](#bug-fixes)
  - [Code Style and Standards](#code-style-and-standards)
    - [General Python Standards](#general-python-standards)
    - [Meaningful Names](#meaningful-names)
    - [Type Hints Usage](#type-hints-usage)
    - [Docstrings](#docstrings)
    - [Comments](#comments)
    - [Exception Handling](#exception-handling)
    - [Async Patterns](#async-patterns)
    - [Resource Management](#resource-management)
    - [Logging Guidelines](#logging-guidelines)
    - [Import Organization](#import-organization)
  - [Testing Guidelines](#testing-guidelines)
  - [Documentation Standards](#documentation-standards)
- [Architecture Guidelines](#architecture-guidelines)
  - [Clean Architecture Principles](#clean-architecture-principles)
  - [aiohttp Patterns](#aiohttp-patterns)
  - [Database Patterns](#database-patterns)
- [Experimental Areas](#experimental-areas)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Dependency Management](#dependency-management)
- [AI Integration](#ai-integration)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Additional Resources](#additional-resources)

## Project Philosophy

CityHive is intentionally experimental and educational, serving as a comprehensive technology playground. Our goals are to:

- **Explore**: Test cutting-edge Python tools, frameworks, and architectural patterns
- **Learn**: Provide a realistic codebase for studying modern web development practices
- **Share**: Demonstrate best practices and emerging patterns in the Python ecosystem
- **Experiment**: Try innovative approaches without production constraints
- **Demonstrate**: Showcase clean architecture and domain-driven design in Python

## Project Structure

CityHive follows clean architecture principles with strict layer separation:

```
project-directory/
├── cityhive/                    # Main application package
│   ├── app/                     # Web Layer
│   │   ├── routes/              # Route definitions organized by functionality
│   │   │   ├── web.py           # Web interface routes (HTML)
│   │   │   ├── api.py           # REST API routes (JSON)
│   │   │   ├── monitoring.py    # Health and monitoring routes
│   │   │   └── main.py          # Route setup and configuration
│   │   ├── views/               # View handlers organized by functionality
│   │   │   ├── web.py           # Web interface views
│   │   │   ├── api.py           # API endpoint views
│   │   │   └── monitoring.py    # Health check views
│   │   ├── middlewares.py       # Request/response middleware
│   │   └── app.py               # Application factory
│   ├── domain/                  # Domain Layer
│   │   ├── models.py            # Domain entities and value objects
│   │   ├── services/            # Business logic and use cases
│   │   └── interfaces/          # Abstract interfaces and protocols
│   ├── infrastructure/          # Infrastructure Layer
│   │   ├── db.py                # Database management and repositories
│   │   ├── config.py            # Configuration management
│   │   └── logging.py           # Structured logging infrastructure
│   ├── static/                  # Static assets (CSS, JS, images)
│   └── templates/               # Jinja2 HTML templates
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests (fast, isolated)
│   └── integration/             # Integration tests (realistic scenarios)
├── migration/                   # Alembic database migrations
└── scripts/                     # Utility and maintenance scripts
```

**Layer Dependencies** (following clean architecture):
- **Web Layer** → Domain Layer
- **Infrastructure Layer** → Domain Layer
- **Domain Layer** → External dependencies (isolated)

## Getting Started

### Prerequisites

- **Python 3.12+**: Latest Python with modern async capabilities
- **PostgreSQL 13+**: With PostGIS extension for spatial data
- **Docker & Docker Compose**: For containerized development
- **Git**: Version control system
- **uv**: Ultra-fast Python package manager

### Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sergeyklay/cityhive.git
   cd cityhive
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install all dependencies**:
   ```bash
   uv sync --all-groups
   ```

4. **Set up environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Start app (with Docker)**:
   ```bash
   docker compose up --build
   ```

### Working with the Project

**Development Commands**:

```bash
# Format code (mandatory before commits)
make format

# Check code quality
make lint format-check

# Run tests with coverage
make test

# Generate coverage reports
make ccov

# Run database migrations
make migrate

# Start application locally (this needs database container to be up)
uv run python -m cityhive.app
```

**Docker Operations**:

```bash
# Start all services
docker compose up --build

# Start specific service
docker compose up postgres

# View logs
docker compose logs -f cityhive_app

# Execute commands in container
docker compose exec cityhive_app bash
```

## Development Workflow

### Creating a New Feature

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/descriptive-feature-name
   ```

2. **Follow clean architecture**:
   - Add domain logic in `domain/` layer
   - Create web handlers in `app/` layer
   - Implement data access in `infrastructure/` layer

3. **Write comprehensive tests**:
   ```bash
   # Add unit tests
   tests/unit/domain/test_your_feature.py

   # Add integration tests
   tests/integration/test_your_feature.py
   ```

4. **Verify quality**:
   ```bash
   make format lint test
   ```

### Bug Fixes

1. **Create a bug fix branch**:
   ```bash
   git checkout -b fix/descriptive-bug-name
   ```

2. **Write regression tests first**:
   - Add tests that would have caught the bug
   - Verify tests fail without the fix

3. **Implement minimal fix**:
   - Keep changes focused on the specific issue
   - Avoid refactoring unrelated code

### Code Style and Standards

#### General Python Standards

- **Python Version**: Use Python 3.12 features and syntax
- **Line Length**: 88 characters maximum (ruff/black default)
- **Indentation**: 4 spaces, never tabs
- **Naming Conventions**:
  - Classes: `CamelCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private attributes: `_single_underscore`

#### Meaningful Names

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

#### Type Hints Usage

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

#### Docstrings

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

#### Comments

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

#### Exception Handling

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

#### Async Patterns

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

#### Resource Management

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

#### Logging Guidelines

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

# ✅ DO: Exception logging with structured context
try:
    process_sensor_data(sensor_id)
except SensorError as e:
    logger.exception(
        "Sensor processing failed",
        sensor_id=sensor_id,
        error_type=type(e).__name__,
        error_code=getattr(e, 'code', None),
    )

# ❌ DON'T: String formatting or f-strings in logging
logger.info(f"Processing beehive {hive_id} inspection")  # Bypasses structured logging
logger.error("Failed to process sensor data for hive %s", hive_id)  # Old format
```

#### Import Organization

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

### Testing Guidelines

Write comprehensive tests following modern pytest practices:

#### Test Structure and Style

```python
# ✅ DO: Clear, focused test with descriptive name
@pytest.mark.parametrize(
    "temperature,humidity,expected_health_score",
    [
        (25.0, 60.0, 0.95),  # Optimal conditions
        (35.0, 80.0, 0.65),  # High temperature and humidity
        (10.0, 30.0, 0.45),  # Cold and dry conditions
    ],
)
async def test_calculate_beehive_health_score_handles_various_conditions(
    temperature: float,
    humidity: float,
    expected_health_score: float,
):
    # Arrange
    sensor_data = SensorData(temperature=temperature, humidity=humidity)

    # Act
    health_score = calculate_beehive_health_score(sensor_data)

    # Assert
    assert abs(health_score - expected_health_score) < 0.01

# ❌ DON'T: Generic test names or complex test logic
def test_health_calculation():
    # Multiple assertions testing different scenarios
    assert calculate_beehive_health_score(...) == 0.95
    assert calculate_beehive_health_score(...) == 0.65
    # ... more assertions
```

#### Async Testing

```python
# ✅ DO: Proper async test with realistic mocking
@pytest.mark.asyncio
async def test_create_inspection_saves_to_database(
    mock_session: AsyncMock,
    sample_beehive: BeehiveModel,
):
    # Arrange
    inspection_data = InspectionCreateModel(
        beehive_id=sample_beehive.id,
        notes="Healthy colony with active queen",
        health_score=0.89,
    )

    # Act
    result = await create_inspection(mock_session, inspection_data)

    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    assert result.beehive_id == sample_beehive.id
    assert result.health_score == 0.89
```

#### Test Organization

- **Unit Tests**: Fast, isolated tests for individual functions
- **Integration Tests**: Test interactions between components
- **Mark slow tests**: Use `@pytest.mark.slow` for database-dependent tests

```bash
# Run all tests
make test

# Run only fast tests
uv run pytest -m "not slow"

# Run specific test file
uv run pytest tests/unit/domain/test_beehive_service.py

# Run with coverage
make test ccov
```

### Documentation Standards

- **Code Documentation**: Google-style docstrings for all public APIs
- **API Documentation**: Auto-generated from type hints and docstrings
- **Architecture Documentation**: High-level design decisions and patterns
- **README Updates**: Keep installation and usage instructions current

## Architecture Guidelines

### Clean Architecture Principles

#### Layer Responsibilities

**Web Layer (`app/`)**:
- **Routes (`app/routes/`)**: HTTP route definitions organized by functionality
- **Views (`app/views/`)**: Request handlers and business logic orchestration
- **Middleware (`app/middlewares.py`)**: Request/response processing
- Template rendering and input validation

```python
# app/routes/web.py
@web_routes.get("/beehives/create", name="beehive_create")
async def create_beehive_route(request: web.Request) -> web.StreamResponse:
    """Handle beehive creation requests."""
    try:
        # Extract and validate input
        data = await request.json()
        create_data = BeehiveCreateModel.model_validate(data)

        # Delegate to view handler
        return await create_beehive_view(request, create_data)
    except ValidationError as e:
        return web.json_response({"errors": e.errors()}, status=400)
```

**Domain Layer (`domain/`)**:
- Business logic and rules
- Domain entities and value objects
- Use cases and services
- Abstract interfaces

```python
# domain/services/beehive.py
class BeehiveService:
    """Service for beehive business operations."""

    def __init__(self, repository: BeehiveRepository):
        self._repository = repository

    async def create_beehive(self, data: BeehiveCreateModel) -> BeehiveModel:
        """Create a new beehive with business validation."""
        # Business rule: Maximum 10 hives per location
        existing_count = await self._repository.count_by_location(data.location)
        if existing_count >= 10:
            raise TooManyHivesError("Maximum 10 hives per location")

        beehive = BeehiveModel(
            name=data.name,
            location=data.location,
            installation_date=datetime.utcnow(),
        )

        return await self._repository.save(beehive)
```

**Infrastructure Layer (`infrastructure/`)**:
- Database access and repositories
- External service integrations
- Configuration management
- Technical implementations

```python
# infrastructure/database/repositories/beehive.py
class SQLAlchemyBeehiveRepository(BeehiveRepository):
    """SQLAlchemy implementation of beehive repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, beehive: BeehiveModel) -> BeehiveModel:
        """Save beehive to database."""
        db_beehive = BeehiveEntity.from_domain_model(beehive)
        self._session.add(db_beehive)
        await self._session.flush()
        return db_beehive.to_domain_model()
```

### aiohttp Patterns

#### Application Factory Pattern

```python
# app/app.py
async def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application(
        middlewares=[
            logging_middleware,
            error_handling_middleware,
        ]
    )

    # Configure dependencies
    app[DatabaseSessionKey] = create_database_session_factory()
    app[BeehiveServiceKey] = BeehiveService(
        repository=SQLAlchemyBeehiveRepository()
    )

    # Setup routes
    from cityhive.app.routes import setup_routes, setup_static_routes
    setup_routes(app)
    setup_static_routes(app)

    return app
```

#### Type-Safe Application Keys

```python
# app/keys.py
from aiohttp.web import AppKey

DatabaseSessionKey = AppKey("database_session", AsyncSession)
BeehiveServiceKey = AppKey("beehive_service", BeehiveService)
ConfigKey = AppKey("config", AppConfig)
```

### Database Patterns

#### Async Session Management

```python
# infrastructure/database/session.py
@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## Experimental Areas

### Current Experiments

1. **Modern Async Patterns**
   - Full async/await throughout the application stack
   - Proper resource management with async context managers
   - Type-safe dependency injection with aiohttp AppKeys

2. **Structured Logging with structlog**
   - JSON-only output to stdout for 12-factor app compliance
   - Request-scoped context using contextvars for distributed tracing
   - Machine-readable logs with structured key-value pairs
   - Integration with modern observability platforms

3. **AI-Assisted Development**
   - Cursor AI integration with custom development rules
   - MCP (Model Context Protocol) for direct database querying
   - AI-powered code suggestions and architectural guidance

4. **Developer Experience Optimization**
   - Ultra-fast dependency management with uv
   - Lightning-fast linting and formatting with ruff
   - Comprehensive pre-commit hooks and quality gates

5. **Clean Architecture in Python**
   - Strict layer separation with dependency inversion
   - Domain-driven design with rich business models
   - Hexagonal architecture patterns for external integrations

6. **DevOps Automation**
   - GitHub Actions with intelligent concurrency control
   - Automated dependency updates via Dependabot
   - Comprehensive CI/CD pipeline with quality gates

### Areas for Future Experimentation

We welcome contributions exploring:

- **Observability**: Structured logging, metrics, distributed tracing
- **Security**: Authentication patterns, authorization, data validation
- **Performance**: Query optimization, caching strategies, async patterns
- **Testing**: Property-based testing, contract testing, performance testing
- **Documentation**: Auto-generated API docs, architectural decision records
- **Deployment**: Container optimization, Kubernetes patterns, blue-green deployments

## Pull Request Process

### Before Submitting

1. **Run quality checks**: `make format lint test`
2. **Verify test coverage**: Ensure new code has appropriate test coverage
3. **Update documentation**: Include docstrings and update relevant docs
4. **Check pre-commit hooks**: Ensure all automated checks pass

### PR Guidelines

1. **Fill out the PR template** completely with clear description
2. **Link related issues** using GitHub keywords (fixes #123)
3. **Keep PRs focused** on a single feature, bug fix, or refactoring
4. **Include examples** for UI changes or new features
5. **Explain complex changes** in the PR description

### PR Review Checklist

- **Architecture**: Follows clean architecture principles
- **Type Safety**: Comprehensive type hints throughout
- **Testing**: New functionality is well-tested
- **Documentation**: Public APIs are documented
- **Performance**: Efficient async patterns and database usage
- **Learning Value**: Demonstrates interesting patterns or techniques

## Code Review Guidelines

### What We Look For

- **Architectural Alignment**: Does it fit clean architecture principles?
- **Code Quality**: Proper type hints, error handling, documentation
- **Test Coverage**: Comprehensive tests with meaningful assertions
- **Async Patterns**: Correct use of async/await and resource management
- **Educational Value**: Does it showcase interesting patterns or techniques?

### Review Process

1. **Technical Review**: Code quality, architecture, performance
2. **Learning Discussion**: What patterns or techniques are demonstrated?
3. **Experimental Value**: How does this contribute to our technology exploration?
4. **Documentation**: Are the changes well-documented and explained?

## Dependency Management

**Use uv exclusively** for dependency management:

```bash
# Add production dependency
uv add "package-name>=1.0.0"

# Add development dependency
uv add --group dev "package-name>=1.0.0"

# Add testing dependency
uv add --group testing "package-name>=1.0.0"

# Update dependencies
uv sync --upgrade

# Never use pip directly - always use uv
```

**Dependency Guidelines**:
- Always specify version constraints
- Use semantic versioning ranges (`>=1.0.0,<2.0.0`)
- Document why dependencies are needed
- Prefer well-maintained, actively developed packages

## AI Integration

### Cursor AI Features

**Pre-configured Rules**: Smart development guidelines in `.cursor/rules/`

**MCP Integration**: Direct database querying through AI interface

**Usage Examples**:
```bash
# Query database schema through AI
"Show me the beehive table structure"

# Generate code with AI assistance
"Create a new beehive inspection endpoint following clean architecture"

# Get architectural guidance
"How should I implement the harvest tracking feature?"
```

### MCP Server Configuration

Custom PostgreSQL MCP server enables AI to:
- Query database schema and relationships
- Generate accurate SQL queries
- Understand data constraints and business rules
- Provide context-aware suggestions

Configure in `.cursor/mcp.json` for optimal AI assistance.

## Troubleshooting Guide

### Common Issues

**Python Environment Issues**:
```bash
# Reset virtual environment
rm -rf .venv
uv venv
uv sync --all-groups
```

**Docker Issues**:
```bash
# Clean rebuild
docker compose down --volumes
docker compose up --build

# View logs
docker compose logs -f cityhive_app
```

**Database Issues**:
```bash
# Reset database
docker compose down postgres
docker volume rm cityhive_postgres_data
docker compose up postgres
make migrate
```

**Test Issues**:
```bash
# Run specific test with verbose output
uv run pytest tests/unit/domain/test_beehive.py -v -s

# Debug test with breakpoint
uv run pytest --pdb tests/unit/domain/test_beehive.py::test_specific_function
```

### Performance Issues

**Database Query Optimization**:
- Use `explain analyze` for slow queries
- Add appropriate indexes for spatial queries
- Use connection pooling for high concurrency

**Async Performance**:
- Profile with `aiohttp-devtools`
- Monitor async task execution
- Use proper connection pooling

## Additional Resources

### Learning the Codebase

- **Start with**: `cityhive/app/app.py` for application entry point
- **Architecture**: Study clean architecture layer separation
- **Patterns**: Look for dependency injection and async patterns
- **Testing**: Examine test structure for testing strategies
- **Logging**: Review structured logging patterns in `cityhive/infrastructure/logging.py`

### External Documentation

- **[aiohttp Documentation](https://docs.aiohttp.org/)**: Web framework patterns
- **[SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)**: Database ORM
- **[structlog Documentation](https://www.structlog.org/)**: Structured logging patterns and best practices
- **[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)**: Architectural principles
- **[Python Type Hints](https://docs.python.org/3/library/typing.html)**: Modern typing practices
- **[FastAPI](https://fastapi.tiangolo.com/)**: Similar async patterns and practices
- **[Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)**: Business modeling approaches

### Community Resources

- [GitHub Discussions](https://github.com/sergeyklay/cityhive/discussions): Questions and general discussion
- [GitHub Issues](https://github.com/sergeyklay/cityhive/issues): Bug reports and feature requests

---

**Happy Contributing!**
