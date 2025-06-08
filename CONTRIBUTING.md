# Contributing to CityHive

Welcome to CityHive! This project serves as an experimental playground for modern Python web development patterns, tools, and practices. Whether you're here to explore, learn, experiment, or contribute, this guide will help you navigate the contribution process effectively.

## Table of Contents

- [Project Philosophy](#project-philosophy)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Experimental Areas](#experimental-areas)
- [Additional Resources](#additional-resources)

## Project Philosophy

CityHive is intentionally experimental and educational, serving as a comprehensive technology playground. Our goals are to:

- **Explore**: Test cutting-edge Python tools, frameworks, and architectural patterns
- **Learn**: Provide a realistic codebase for studying modern web development practices
- **Share**: Demonstrate best practices and emerging patterns in the Python ecosystem
- **Experiment**: Try innovative approaches without production constraints
- **Demonstrate**: Showcase clean architecture and domain-driven design in Python

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

5. **Start development environment**:
   ```bash
   docker compose up --build
   ```

6. **Verify setup**:
   ```bash
   make test
   ```

For detailed development setup and workflows, see [Development Guide](./docs/development.md).

## Development Workflow

### Creating a New Feature

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/descriptive-feature-name
   ```

2. **Follow clean architecture principles**:
   - Add domain logic in `cityhive/domain/` layer
   - Create web handlers in `cityhive/app/` layer
   - Implement data access in `cityhive/infrastructure/` layer

   See [Architecture](./docs/architecture.md) for detailed architectural guidelines.

3. **Write comprehensive tests**:
   ```bash
   # Add unit tests
   tests/unit/domain/test_your_feature.py

   # Add integration tests
   tests/integration/test_your_feature.py
   ```

4. **Follow coding standards**:
   - Use modern Python 3.12 features and type hints
   - Follow the project's style guide (see [Coding Standards](./docs/coding-standards.md))
   - Use structured logging patterns

5. **Verify quality**:
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

### Code Quality Requirements

- **Type Hints**: Required for all functions and public APIs
- **Test Coverage**: Minimum 90% overall, 95% for new code
- **Documentation**: Google-style docstrings for all public APIs
- **Formatting**: Code must pass `make format lint`

## Pull Request Process

### Before Submitting

1. **Run quality checks**: `make format lint test`
2. **Verify test coverage**: Ensure new code has appropriate test coverage
3. **Update documentation**: Include docstrings and update relevant docs
4. **Check dependencies**: Use `uv` for all dependency management

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

### Feedback Guidelines

- **Be constructive**: Focus on improvement opportunities
- **Be specific**: Provide concrete suggestions and examples
- **Be educational**: Share knowledge and explain reasoning
- **Be respectful**: Remember this is a learning environment

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

### Areas for Future Experimentation

We welcome contributions exploring:

- **Observability**: Advanced metrics, distributed tracing
- **Security**: Authentication patterns, authorization, data validation
- **Performance**: Query optimization, caching strategies, async patterns
- **Testing**: Property-based testing, contract testing, performance testing
- **Documentation**: Auto-generated API docs, architectural decision records
- **Deployment**: Container optimization, monitoring, blue-green deployments

### Contributing to Experiments

When contributing experimental features:

1. **Document the experiment**: Explain what you're trying to achieve
2. **Provide examples**: Show how the pattern should be used
3. **Include tests**: Demonstrate the pattern works correctly
4. **Update documentation**: Add to relevant docs in `docs/` folder
5. **Share learnings**: Explain what you learned from the experiment

## Additional Resources

### Learning the Codebase

- **Start with**: `cityhive/app/app.py` for application entry point
- **Architecture**: Study [Architecture Guide](./docs/architecture.md)
- **Development**: Review [Development Guide](./docs/development.md)
- **Coding Style**: Follow [Coding Standards](./docs/coding-standards.md)
- **Technology Stack**: Understand [Technology Choices](./docs/technology-stack.md)

### External Documentation

- **[aiohttp Documentation](https://docs.aiohttp.org/)**: Web framework patterns
- **[SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)**: Database ORM
- **[structlog Documentation](https://www.structlog.org/)**: Structured logging patterns
- **[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)**: Architectural principles

### Community Resources

- [GitHub Discussions](https://github.com/sergeyklay/cityhive/discussions): Questions and general discussion
- [GitHub Issues](https://github.com/sergeyklay/cityhive/issues): Bug reports and feature requests

---

**Happy Contributing!**

Remember, this is a learning and experimentation environment. Don't hesitate to ask questions, share ideas, or propose new approaches. Every contribution helps make this a better resource for the Python community.
