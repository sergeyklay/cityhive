# CityHive

[![codecov](https://codecov.io/gh/sergeyklay/cityhive/graph/badge.svg?token=aXIi7iNGl3)](https://codecov.io/gh/sergeyklay/cityhive)
[![CI](https://github.com/sergeyklay/cityhive/actions/workflows/ci.yml/badge.svg)](https://github.com/sergeyklay/cityhive/actions/workflows/ci.yml)

**An experimental aiohttp microservice for urban beehive management and technology exploration.**

CityHive is a synthetic yet realistic sandbox project designed to explore modern Python web development patterns, architectural approaches, and DevOps practices. While grounded in the domain of urban beehive management (featuring sensor data ingestion, inspection scheduling, harvest tracking, and spatial analytics), this project serves as a comprehensive technology playground rather than a production application.

## Project Focus

This project serves as an experimental playground for:

- **Architectural Patterns**: Clean architecture, domain-driven design, dependency injection
- **Async Development**: aiohttp web framework, asyncpg database drivers, SQLAlchemy async ORM
- **Modern Tooling**: uv package management, ruff linting, AI-assisted development
- **DevOps Practices**: Docker containerization, GitHub Actions CI/CD, automated testing
- **Code Quality**: Comprehensive testing with pytest, coverage tracking, type safety

## Technology Stack

### Core Framework
- **Python 3.12** with **aiohttp** web framework
- **PostgreSQL + PostGIS** for spatial data with **SQLAlchemy** async ORM
- **Jinja2** templates and **Pydantic** validation

### Development Tools
- **uv**: Ultra-fast Python package manager
- **ruff**: Lightning-fast linting and formatting
- **pytest**: Comprehensive testing with async support
- **Docker**: Containerized development environment

## Architecture

Clean architecture with strict layer separation:

```
cityhive/
├── cityhive/
├── cityhive/                 # Main application package
│   ├── app/                  # Web layer (aiohttp routes, middleware, views)
│   │   ├── routes/           # Route definitions organized by functionality
│   │   ├── views/            # View handlers organized by functionality
│   │   └── middlewares.py    # Request/response middleware
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
│   ├── mcp.json              # MCP server configuration
│   └── postgres.py           # Custom PostgreSQL MCP server
├── .github/                  # GitHub Actions workflows
└── docker-compose.yml        # Development environment
```

## Quick Start

### Prerequisites
- Python 3.12+
- Docker and Docker Compose

### Getting Started

1. **Clone and setup**
   ```bash
   git clone https://github.com/sergeyklay/cityhive.git
   cd cityhive
   uv sync --all-groups
   ```

2. **Start the application**
   ```bash
   docker compose up --build
   ```

3. **Verify installation**
   ```bash
   make test
   ```

## Development

### Essential Commands
```bash
make format         # Format code
make lint           # Run linter
make test           # Run tests with coverage
make migrate        # Run database migrations
```

### AI Integration
- **Cursor AI**: Pre-configured development rules and patterns
- **MCP Server**: Direct database querying through AI interface
- **Smart Completion**: Context-aware code suggestions

## Project Metrics

- **Test Coverage**: Maintained above 90%
- **Code Quality**: Enforced with ruff and comprehensive type hints
- **CI/CD**: Full automation with GitHub Actions
- **Dependencies**: Automatically updated via Dependabot

## Documentation

- [Logging](./docs/logging.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
