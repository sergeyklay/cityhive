# CityHive

[![codecov](https://codecov.io/gh/sergeyklay/cityhive/graph/badge.svg?token=aXIi7iNGl3)](https://codecov.io/gh/sergeyklay/cityhive)
[![CI](https://github.com/sergeyklay/cityhive/actions/workflows/ci.yml/badge.svg)](https://github.com/sergeyklay/cityhive/actions/workflows/ci.yml)

**An experimental aiohttp microservice for urban beehive management and technology exploration.**

CityHive is a synthetic yet realistic sandbox project designed to explore modern Python web development patterns, architectural approaches, and DevOps practices. While grounded in the domain of urban beehive management, this project serves as a comprehensive technology playground rather than a production application.

## Quick Start

### Prerequisites
- Python 3.12+
- Docker and Docker Compose

### Get Started in 3 Steps

1. **Clone and setup dependencies**
   ```bash
   git clone https://github.com/sergeyklay/cityhive.git
   cd cityhive
   uv sync --all-groups
   ```

2. **Start the application**
   ```bash
   docker compose up --build
   ```

3. **Verify everything works**
   ```bash
   make test
   ```

The application will be available at `http://localhost:8080`.

## Project Focus

This project serves as an experimental playground for:

- **Clean Architecture**: Domain-driven design with strict layer separation
- **Async Python**: Modern aiohttp web framework with SQLAlchemy async ORM
- **Developer Experience**: AI-assisted development, comprehensive tooling
- **Production Practices**: Docker, CI/CD, monitoring, comprehensive testing

## Essential Commands

```bash
make test-unit          # Run unit tests with coverage
make test-integration   # Running integration tests (needs DB to be up)
make test               # Run all tests
make format             # Format code with ruff
make lint               # Run linter checks
make migrate            # Apply database migrations
```

## Documentation

📖 **Comprehensive guides available in the `docs/` folder:**

- **[Development Guide](./docs/development.md)** - Setup, workflows, testing, and best practices
- **[Architecture](./docs/architecture.md)** - Clean architecture principles, layer separation, and design patterns
- **[Technology Stack](./docs/technology-stack.md)** - Detailed technology choices and rationale
- **[Coding Standards](./docs/coding-standards.md)** - Code style, naming conventions, and best practices
- **[AI Integration](./docs/ai-integration.md)** - Cursor AI setup, MCP server, and AI-assisted development
- **[Logging](./docs/logging.md)** - Structured logging with JSON output

## Key Technologies

- **Python 3.12** with **aiohttp** web framework
- **PostgreSQL + PostGIS** with **SQLAlchemy** async ORM
- **Docker** containerization and **uv** package management
- **Pytest** testing with **ruff** linting and formatting

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and contribution process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
