# Architecture

CityHive follows clean architecture principles with strict layer separation to ensure maintainability, testability, and scalability.

## Project Structure

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
├── scripts/                     # Utility and maintenance scripts
├── .cursor/                     # Cursor AI configuration
│   ├── mcp.json                 # MCP server configuration
│   └── postgres.py              # Custom PostgreSQL MCP server
├── .github/                     # GitHub Actions workflows
└── docker-compose.yml           # Development environment
```

## Layer Responsibilities

### Web Layer (`cityhive/app/`)
- **Routes**: HTTP endpoint definitions and URL routing
- **Views**: Request handlers and response formatting
- **Middleware**: Cross-cutting concerns (logging, error handling, authentication)
- **Templates**: Jinja2 HTML templates for web responses

**Key Principles:**
- No business logic in web layer
- Type-safe request/response handling
- Dependency injection for services
- Use `web.AppKey` for application data storage

### Domain Layer (`cityhive/domain/`)
- **Business Logic**: Core application logic and rules
- **Domain Models**: Data structures representing business concepts
- **Services**: Domain services for complex business operations
- **Interfaces**: Abstractions for external dependencies

**Key Principles:**
- Framework-agnostic business logic
- No external dependencies
- Pure functions where possible
- Domain-driven design patterns

### Infrastructure Layer (`cityhive/infrastructure/`)
- **Database**: SQLAlchemy models and repositories
- **External APIs**: Third-party service integrations
- **Configuration**: Application settings and environment management
- **Utilities**: Cross-cutting technical concerns

**Key Principles:**
- Implements domain interfaces
- Handles all external I/O
- Configuration management
- Database connection pooling

## Design Patterns

### Application Factory Pattern
```python
async def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application(middlewares=[...])
    # Dependency injection setup
    # Route registration
    # Database initialization
    return app
```

### Dependency Injection
- Services injected into request handlers
- Database sessions managed via cleanup contexts
- Configuration provided through application keys

### Repository Pattern
- Abstract data access through repository interfaces
- SQLAlchemy repositories in infrastructure layer
- Testable with mock repositories

### Middleware Pipeline
1. **Logging Middleware**: Request/response logging with structured data
2. **Error Handling Middleware**: Centralized exception handling
3. **Application Routes**: Business logic handlers

## Database Architecture

### PostgreSQL + PostGIS
- Spatial data capabilities for geographic features
- ACID compliance for data integrity
- Connection pooling for performance

### SQLAlchemy Async ORM
- Async/await patterns throughout
- Session management with cleanup contexts
- Alembic migrations for schema changes

### Migration Strategy
- Version-controlled schema changes
- Forward and backward migrations
- Environment-specific configurations

## Testing Architecture

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution for development feedback

### Integration Tests (`tests/integration/`)
- Test component interactions
- Real database connections
- End-to-end scenario validation

### Test Database
- Separate test database instance
- Automatic schema setup/teardown
- Parallel test execution support

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

### Caching Strategy
- Application-level caching for expensive operations
- Database query optimization
- Static asset serving optimization

### Monitoring & Observability
- Structured logging with JSON output
- Health check endpoints
- Performance metrics collection

## Deployment Architecture

### Containerization
- Docker multi-stage builds
- Minimal production images
- Environment-specific configurations

### Development Environment
- Docker Compose for local development
- Hot reloading during development
- Consistent development/production parity

### CI/CD Pipeline
- Automated testing on all commits
- Code quality checks with ruff
- Automated dependency updates
