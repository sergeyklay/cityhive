# Architecture

CityHive follows clean architecture principles with strict layer separation, domain-driven design, and dependency injection to ensure maintainability, testability, and scalability.

## Project Structure

```
cityhive/
├── app/                         # Web Layer
│   ├── routes/                  # Route definitions organized by functionality
│   │   ├── web.py               # Web interface routes (HTML)
│   │   ├── api.py               # REST API routes (JSON)
│   │   ├── monitoring.py        # Health and monitoring routes
│   │   └── main.py              # Route setup and configuration
│   ├── views/                   # View handlers organized by functionality
│   │   ├── web.py               # Web interface views
│   │   ├── users.py             # User API endpoints
│   │   ├── hives.py             # Hive API endpoints
│   │   └── monitoring.py        # Health check views
│   ├── helpers/                 # Web layer utilities
│   │   ├── request.py           # Request/response helpers
│   │   └── validation.py        # Input validation utilities
│   ├── middlewares.py           # Request/response middleware
│   └── app.py                   # Application factory + service initialization
├── domain/                      # Domain Layer
│   ├── models.py                # Domain entities (SQLAlchemy models)
│   ├── services/                # Cross-cutting domain services
│   │   └── health.py            # Health check service
│   ├── user/                    # User domain aggregate
│   │   ├── __init__.py          # Domain exports
│   │   ├── service.py           # User business logic
│   │   ├── repository.py        # User data access interface
│   │   └── exceptions.py        # User-specific exceptions
│   └── hive/                    # Hive domain aggregate
│       ├── __init__.py          # Domain exports
│       ├── service.py           # Hive business logic
│       ├── repository.py        # Hive data access interface
│       └── exceptions.py        # Hive-specific exceptions
├── infrastructure/              # Infrastructure Layer
│   ├── db.py                    # Database session management
│   ├── config.py                # Configuration management
│   ├── logging.py               # Structured logging infrastructure
│   └── typedefs.py              # Type-safe application keys
├── static/                      # Static assets (CSS, JS, images)
├── templates/                   # Jinja2 HTML templates
tests/                           # Test suites
├── unit/                        # Unit tests (fast, isolated, mocked)
│   ├── app/                     # Web layer tests
│   ├── domain/                  # Domain layer tests
│   │   ├── user/                # User domain tests
│   │   └── hive/                # Hive domain tests
│   └── infrastructure/          # Infrastructure tests
└── integration/                 # Integration tests (real dependencies)
migration/                       # Alembic database migrations
scripts/                         # Utility and maintenance scripts
.cursor/                         # Cursor AI configuration
├── mcp.json                     # MCP server configuration
└── postgres.py                  # Custom PostgreSQL MCP server
.github/                         # GitHub Actions workflows
docker-compose.yml               # Development environment
```

## Architecture Layers

### Web Layer (`cityhive/app/`)

**Responsibilities:**
- HTTP request/response handling
- Input validation and sanitization
- Route definitions and URL routing
- Response formatting (JSON/HTML)
- Middleware pipeline (logging, error handling)
- Dependency injection coordination

**Key Components:**
- **Views**: Pure HTTP handlers that delegate to domain services
- **Routes**: URL-to-handler mapping with RESTful conventions
- **Helpers**: Request parsing, response formatting, validation utilities
- **Middleware**: Cross-cutting concerns (logging, error handling)

**Principles:**
- No business logic - delegate to domain services
- Explicit transaction management (`commit`/`rollback`)
- Convert domain exceptions to HTTP responses
- Use service factories for dependency injection

### Domain Layer (`cityhive/domain/`)

**Responsibilities:**
- Business rules and logic implementation
- Domain model definitions
- Use case orchestration
- Domain-specific exception handling

**Key Components:**
- **Models**: SQLAlchemy entities representing business concepts
- **Services**: Business logic orchestration and use cases
- **Repositories**: Abstract data access interfaces (concrete implementations in infrastructure)
- **Exceptions**: Domain-specific error types
- **Aggregates**: Organized by business domain (e.g., `user/`, `hive/`)

**Principles:**
- Framework-agnostic business logic
- No external dependencies (databases, HTTP, etc.)
- Pure functions where possible
- Domain-driven design with aggregates

### Infrastructure Layer (`cityhive/infrastructure/`)

**Responsibilities:**
- External system integrations
- Database connection management
- Configuration and environment handling
- Cross-cutting technical concerns

**Key Components:**
- **Database**: Session management, connection pooling
- **Configuration**: Environment-based settings with validation
- **Logging**: Structured logging with JSON output
- **Type Definitions**: Type-safe application keys for dependency injection

**Principles:**
- Implements domain interfaces
- Handles all external I/O
- Environment-specific configuration
- Type-safe dependency management

## Core Design Patterns

### Service Factory Pattern

Services are created through factories that manage dependencies and lifecycle:

```python
# Service factory manages session-scoped dependencies
class UserServiceFactory:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    def create_service(self, session: AsyncSession) -> UserService:
        repository = UserRepository(session)
        return UserService(repository)

class HiveServiceFactory:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    def create_service(self, session: AsyncSession) -> HiveService:
        repository = HiveRepository(session)
        return HiveService(repository)

# Application-level registration
async def init_services(app: web.Application) -> None:
    session_factory = app[db_key]

    # Register all service factories
    user_service_factory = UserServiceFactory(session_factory)
    app[user_service_factory_key] = user_service_factory

    hive_service_factory = HiveServiceFactory(session_factory)
    app[hive_service_factory_key] = hive_service_factory
```

### Repository Pattern

Data access is abstracted through repository interfaces:

```python
# Concrete repository implementing data access
class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()  # Get ID without committing
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### Domain Service Pattern

Business logic is encapsulated in domain services:

```python
class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def register_user(self, input_data: UserRegistrationInput) -> User:
        # Business rule: no duplicate emails
        if await self._repository.exists_by_email(input_data.email):
            raise DuplicateUserError(input_data.email)

        # Create and persist user
        user = User(name=input_data.name, email=input_data.email)
        return await self._repository.save(user)
```

### Type-Safe Dependency Injection

Dependencies are registered with type-safe keys:

```python
# Type-safe application keys
user_service_factory_key = web.AppKey("user_service_factory", UserServiceFactory)
hive_service_factory_key = web.AppKey("hive_service_factory", HiveServiceFactory)
db_key = web.AppKey("database", async_sessionmaker)

# Registration in application factory
app[user_service_factory_key] = user_service_factory
app[hive_service_factory_key] = hive_service_factory

# Usage with full type safety
user_service_factory = request.app[user_service_factory_key]  # Type: UserServiceFactory
hive_service_factory = request.app[hive_service_factory_key]  # Type: HiveServiceFactory
```

### Transaction Management

Explicit transaction control in web layer:

```python
async def create_user(request: web.Request) -> web.Response:
    service_factory = request.app[user_service_factory_key]

    async with request.app[db_key]() as session:
        try:
            user_service = service_factory.create_service(session)
            user = await user_service.register_user(input_data)
            await session.commit()  # Explicit commit on success

            return create_success_response({"user": user.dict()}, status=201)
        except DuplicateUserError:
            await session.rollback()  # Explicit rollback on domain error
            return create_error_response("Email already exists", status=409)
        except Exception:
            await session.rollback()  # Rollback on unexpected errors
            raise
```

### Domain Exception Handling

Domain exceptions are converted to HTTP responses in the web layer:

```python
# User domain exceptions
class UserError(Exception):
    """Base exception for user domain."""

class DuplicateUserError(UserError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} already exists")

# Hive domain exceptions
class HiveError(Exception):
    """Base exception for hive domain."""

class UserNotFoundError(HiveError):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")

class InvalidLocationError(HiveError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

# Web layer conversion - User endpoints
try:
    user = await user_service.register_user(input_data)
except DuplicateUserError:
    return create_error_response("Email already exists", status=409)
except UserError as e:
    return create_error_response(str(e), status=400)

# Web layer conversion - Hive endpoints
try:
    hive = await hive_service.create_hive(input_data)
except UserNotFoundError:
    return create_error_response("User not found", status=404)
except InvalidLocationError as e:
    return create_error_response(e.message, status=400)
except HiveError as e:
    return create_error_response(str(e), status=400)
```

## Database Architecture

### PostgreSQL + PostGIS
- Spatial data capabilities for geographic features
- ACID compliance for data integrity
- Connection pooling for performance

### SQLAlchemy Async ORM
- Async/await patterns throughout
- Session management with cleanup contexts
- Repository pattern for data access abstraction
- Explicit transaction boundaries

### Migration Strategy
- Version-controlled schema changes with Alembic
- Forward and backward migrations
- Environment-specific configurations

## Testing Architecture

### Unit Tests (`tests/unit/`)
- **Pure functional style** - no class-based tests
- **Mocked dependencies** - fast execution with isolated components
- **Domain focus** - test business logic without external dependencies
- **Repository tests** - verify data access logic with mocked sessions

### Integration Tests (`tests/integration/`)
- **Real dependencies** - actual database connections and HTTP servers
- **End-to-end scenarios** - complete request/response cycles
- **Infrastructure validation** - test database migrations, health checks

### Test Organization
- **Domain-specific fixtures** - kept in test files when domain-specific
- **Shared utilities** - moved to `conftest.py` when used across modules
- **Descriptive names** - test functions describe scenario and expected outcome
- **No comments** - tests should be self-documenting

## Security Considerations

### Input Validation
- Pydantic models for request validation
- SQL injection prevention via ORM
- XSS protection in templates

### Authentication & Authorization
- Session-based authentication
- Role-based access control
- Secure cookie configuration

### Data Protection
- Environment-based secrets management
- Database connection encryption
- Audit logging for sensitive operations

## Performance Optimization

### Async Architecture
- Non-blocking I/O throughout the stack
- Connection pooling for database access
- Efficient request handling with aiohttp

### Service Lifecycle
- Request-scoped services for optimal resource usage
- Session-per-request pattern
- Cleanup contexts for resource management

### Monitoring & Observability
- Structured logging with JSON output
- Health check endpoints with database connectivity
- Performance metrics collection

## Development Workflow

### Code Organization
- **One aggregate per domain module** - `domain/user/`, `domain/hive/`
- **Service factories** - manage dependencies and lifecycle
- **Type safety** - use `web.AppKey` for application data
- **Explicit transactions** - commit/rollback in web layer

### Testing Strategy
- **Unit tests first** - fast feedback with mocked dependencies
- **Integration tests** - validate end-to-end scenarios
- **Functional style** - pure functions for easier testing

### Dependency Management
- **uv only** - never use pip for package management
- **Type hints required** - all functions and methods
- **Clean imports** - organized by standard library, third-party, first-party
