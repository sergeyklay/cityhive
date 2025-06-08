# Development Guide

This guide covers development setup, workflows, and best practices for CityHive.

## Prerequisites

- **Python 3.12+** - Required for modern async features
- **Docker & Docker Compose** - For local development environment
- **Git** - Version control

## Initial Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/sergeyklay/cityhive.git
cd cityhive
uv sync --all-groups
```

### 2. Environment Configuration

Copy the example environment file and customize:
```bash
cp .env.example .env
# Edit .env with your local settings
```

### 3. Start Development Environment

```bash
docker compose up --build
```

This starts:
- PostgreSQL database with PostGIS extensions
- Application server with hot reloading

### 4. Verify Installation

```bash
make test
```

## Essential Commands

### Code Quality
```bash
make format         # Format code with ruff
make lint           # Run linter checks
make format-check   # Check if code is properly formatted
```

### Testing
```bash
make test           # Run all tests with coverage
make ccov           # Generate coverage reports
```

### Database Management
```bash
make migrate        # Run database migrations
```

### Development Server
```bash
# Start application directly
uv run python -m cityhive.app

# Or with Docker
docker compose up
```

### Container Management
```bash
docker compose up --build    # Start all services
docker compose down          # Stop all services
docker compose logs app      # View application logs
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
make test
make lint

# Commit and push
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

### 2. Code Quality Checks
Always run before committing:
```bash
make format
make lint
make test
```

### 3. Database Changes
When modifying models:
```bash
# Generate migration (manual process with Alembic)
uv run alembic revision --autogenerate -m "Add new model"

# Review generated migration file
# Apply migration
make migrate
```

### 4. Testing New Features
```bash
# Test specific module
uv run pytest tests/unit/app/test_specific.py

# Run with coverage
make test ccov

# Verbose output for debugging
uv run pytest -vvs tests/path/to/test.py
```

## Package Management

CityHive uses `uv` for dependency management. **Never use pip directly.**

### Adding Dependencies
```bash
# Production dependency
uv add package-name

# Development dependency
uv add --group dev package-name
```

### Updating Dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add package-name@latest
```

### Dependency Groups
- **default**: Production dependencies
- **dev**: Development tools (pytest, ruff, etc.)

## Code Style

### Formatting
- **ruff**: Automatic code formatting
- **Line length**: 88 characters (Black compatible)
- **Import sorting**: Automatic with ruff

### Type Hints
Type hints are required for all functions:
```python
def process_data(items: list[dict[str, Any]]) -> ProcessedData:
    """Process input data and return structured result."""
    ...
```

See [Coding Standards](./coding-standards.md) for detailed style guidelines.

## Testing Guidelines

### Unit Tests
- Test individual functions/classes in isolation
- Mock external dependencies
- Fast execution (< 1s per test)
- Located in `tests/unit/`

### Integration Tests
- Test component interactions
- Use real database connections
- Test API endpoints end-to-end
- Located in `tests/integration/`

### Test Structure
```python
def test_function_name():
    # Arrange: Set up test data
    user_data = {"name": "Test User", "email": "test@example.com"}

    # Act: Execute the function
    result = create_user(user_data)

    # Assert: Verify the result
    assert result.name == "Test User"
    assert result.email == "test@example.com"
```

### Coverage Requirements
- **Minimum**: 90% overall coverage
- **Target**: 95% for new code
- **Critical paths**: 100% coverage required

## Database Development

### Migrations
- Use Alembic for all schema changes
- Never edit existing migrations
- Always review generated migrations
- Test both upgrade and downgrade paths

### Database Testing
- Each test gets a fresh transaction
- Automatic rollback after test completion
- Separate test database for isolation

## Debugging

### Application Debugging
```python
import pdb; pdb.set_trace()  # Set breakpoint
```

### Logging
Use structured logging for debugging:
```python
from cityhive.infrastructure.logging import get_logger

logger = get_logger(__name__)
logger.info("Debug info", user_id=123, operation="login")
```

### Database Debugging
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
docker compose down
docker compose up --build
```

**Database connection errors:**
```bash
docker compose down
docker volume rm cityhive_pgdata
docker compose up
make migrate
```

**Import errors:**
```bash
uv sync --all-groups
```

**Test failures:**
```bash
# Run specific failing test with verbose output
uv run pytest -vvs tests/path/to/test.py::test_function
```

### Getting Help

1. Check existing issues in GitHub repository
2. Review documentation in `docs/` folder
3. Check logs: `docker compose logs app`
4. Verify environment: `uv run --frozen --version`

## Editor Configuration

### VS Code / Cursor
Recommended extensions:
- Python extension
- Ruff extension

### Configuration
The project includes:
- `pyproject.toml` - Tool configuration for ruff, pytest, etc.
- `.cursor/` - Cursor AI configuration

### AI Integration
- **Cursor AI**: Pre-configured rules and patterns
- **Code completion**: Context-aware suggestions
- **Error assistance**: Automatic error detection and fixes

See [AI Integration](./ai-integration.md) for detailed AI tooling information.
