# CityHive

[![codecov](https://codecov.io/gh/sergeyklay/cityhive/graph/badge.svg?token=aXIi7iNGl3)](https://codecov.io/gh/sergeyklay/cityhive)

**An experimental aiohttp microservice for urban beehive management and technology exploration.**

CityHive is a synthetic yet realistic sandbox project designed to explore modern Python web development patterns, architectural approaches, and DevOps practices. While grounded in the domain of urban beehive management (featuring sensor data ingestion, inspection scheduling, harvest tracking, and spatial analytics), this project serves as a comprehensive technology playground rather than a production application.

## 🧪 Experimental Focus

This project is intentionally experimental—not because it uses unconventional tools, but because it serves as a testing ground for:

- **Architectural Patterns**: Clean architecture, domain-driven design, dependency injection
- **Async Patterns**: aiohttp web framework, asyncpg database drivers, SQLAlchemy async ORM
- **Developer Experience**: Modern tooling with uv, ruff, Cursor AI integration, MCP protocols
- **DevOps Practices**: Docker containerization, GitHub Actions CI/CD, automated dependency management
- **Code Quality**: Comprehensive testing with pytest, coverage tracking, automated formatting
- **Infrastructure**: PostgreSQL with PostGIS spatial extensions, database migrations with Alembic

## 🔧 Technology Stack

### Core Framework & Language
- **Python 3.12**: Latest Python with modern async capabilities
- **aiohttp**: High-performance async web framework
- **Jinja2**: Template engine for server-side rendering
- **Pydantic**: Data validation and settings management

### Database & Persistence
- **PostgreSQL**: Primary database with advanced features
- **PostGIS**: Spatial database extensions for geographic data
- **SQLAlchemy**: Modern async ORM with type safety
- **asyncpg**: High-performance async PostgreSQL driver
- **Alembic**: Database migration management

### Development Tooling
- **uv**: Ultra-fast Python package manager and resolver
- **ruff**: Lightning-fast Python linter and formatter
- **pytest**: Comprehensive testing framework with async support
- **coverage**: Code coverage analysis and reporting

### DevOps & Infrastructure
- **Docker**: Containerized application deployment
- **GitHub Actions**: CI/CD automation with concurrency control
- **Dependabot**: Automated dependency updates
- **Codecov**: Coverage tracking and reporting
- **Make**: Build automation and task orchestration

### AI & Editor Integration
- **Cursor Rules**: AI-assisted development guidelines
- **MCP (Model Context Protocol)**: Direct database integration for AI assistants
- **FastMCP**: High-performance MCP server implementation

### Configuration & Best Practices
- **12-Factor App**: Configuration via environment variables
- **python-dotenv**: Environment configuration management
- **Pre-commit**: Git hooks for code quality
- **Clean Architecture**: Separation of concerns across layers

## 🏗️ Project Structure

```
cityhive/
├── cityhive/                 # Main application package
│   ├── app/                  # Web layer (aiohttp routes, middleware, views)
│   ├── domain/               # Business logic and domain models
│   ├── infrastructure/       # External integrations and database
│   ├── static/               # Static assets
│   └── templates/            # Jinja2 templates
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── migration/                # Alembic database migrations
├── scripts/                  # Utility scripts
├── .cursor/                  # Cursor AI configuration
│   ├── mcp.json             # MCP server configuration
│   └── postgres.py          # Custom PostgreSQL MCP server
├── .github/                  # GitHub Actions workflows
└── docker-compose.yml       # Development environment
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL with PostGIS
- Docker (optional, for containerized development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sergeyklay/cityhive.git
   cd cityhive
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync --all-groups
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start app (with Docker)**
   ```bash
   docker compose up --build
   ```

## 🧪 Development Workflow

### Code Quality & Formatting
```bash
# Format code
make format

# Check formatting
make format-check

# Run linter
make lint
```

### Testing
```bash
# Run tests with coverage
make test

# Generate coverage reports
make ccov
```

### Database Management
```bash
# Run migrations
make migrate

# Create new migration
uv run alembic revision --autogenerate -m "Description"
```

## 🤖 AI Integration Features

### Cursor AI Integration
- **Smart rules**: Pre-configured coding standards and patterns
- **MCP integration**: Direct database querying through AI interface
- **Auto-completion**: Context-aware code suggestions

### MCP Server
Custom PostgreSQL MCP server enables AI assistants to:
- Query database schema and data directly
- Generate accurate SQL queries
- Understand data relationships and constraints

## 🔍 Key Experimental Areas

### 1. **Clean Architecture Implementation**
- Strict separation of web, domain, and infrastructure layers
- Dependency injection patterns
- Domain-driven design principles

### 2. **Modern Python Async Patterns**
- Full async/await throughout the stack
- Proper resource management with context managers
- Type-safe application state management

### 3. **Developer Experience Optimization**
- Zero-config development setup
- Automated code formatting and linting
- Comprehensive testing infrastructure
- AI-assisted development workflows

### 4. **DevOps Automation**
- Container-first development
- Automated dependency management
- Comprehensive CI/CD pipelines
- Coverage tracking and quality gates

## 📊 Project Metrics

- **Test Coverage**: Maintained above 90%
- **Code Quality**: Enforced with ruff and type hints
- **Dependencies**: Automatically updated via Dependabot
- **CI/CD**: Full automation with GitHub Actions

## 🤝 Contributing

This is an open-source project! Whether you want to:
- Explore the codebase and learn from the patterns
- Experiment with new technologies or approaches
- Contribute improvements or additional examples
- Use this as a starting point for your own projects

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Project Goals

CityHive demonstrates:
- Modern Python web development best practices
- Comprehensive testing and quality assurance
- Clean architecture and domain-driven design
- Effective use of async patterns and type safety
- Integration of AI tools in development workflows
- Professional DevOps practices and automation

Perfect for developers wanting to explore contemporary Python web development patterns or as a foundation for building robust, async web applications.
