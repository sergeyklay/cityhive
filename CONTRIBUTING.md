# Contributing to CityHive

Welcome to CityHive! This project serves as an experimental playground for modern Python web development patterns, tools, and practices. Whether you're here to learn, experiment, or contribute, this guide will help you get started.

## 🧪 Project Philosophy

CityHive is intentionally experimental and educational. Our goals are to:

- **Explore**: Test modern Python tools, frameworks, and architectural patterns
- **Learn**: Provide a realistic codebase for studying contemporary web development
- **Share**: Demonstrate best practices and emerging patterns in the Python ecosystem
- **Experiment**: Try new approaches without the constraints of production requirements

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**: We use the latest Python features and type hints
- **PostgreSQL 13+**: With PostGIS extension for spatial data
- **Docker**: For containerized development (optional but recommended)
- **Git**: For version control

### Development Setup

1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/sergeyklay/cityhive.git
   cd cityhive
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install all dependencies**
   ```bash
   uv sync --all-groups
   ```

4. **Set up environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Start app (with Docker)**
   ```bash
   docker compose up --build
   ```

## 🏗️ Project Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│           Web Layer (app/)          │  ← aiohttp routes, middleware, views
├─────────────────────────────────────┤
│         Domain Layer (domain/)      │  ← Business logic, services, models
├─────────────────────────────────────┤
│    Infrastructure (infrastructure/) │  ← Database, external APIs, config
└─────────────────────────────────────┘
```

- **Web Layer**: HTTP handling, request/response processing, view logic
- **Domain Layer**: Core business logic, domain models, use cases
- **Infrastructure Layer**: Database access, external services, configuration

### Key Patterns We're Exploring

- **Dependency Injection**: Using aiohttp's `AppKey` for type-safe dependency management
- **Async Throughout**: Full async/await from web layer to database
- **Type Safety**: Comprehensive type hints with Pydantic models
- **Resource Management**: Proper cleanup with async context managers
- **Domain-Driven Design**: Rich domain models with business logic

## 🔧 Development Workflow

### Code Standards

We maintain high code quality through automated tooling:

#### Formatting & Linting
```bash
# Auto-format code (mandatory before commits)
make format

# Check formatting without changes
make format-check

# Run linter checks
make lint
```

#### Type Checking
- All code must have proper type hints
- Use `mypy` for static type checking
- Pydantic for runtime validation

#### Testing Requirements
```bash
# Run all tests with coverage
make test

# View coverage report
make ccov
```

**Testing Standards:**
- Minimum 90% test coverage required
- Use pytest with async support
- Write both unit and integration tests
- Mock external dependencies appropriately

### Code Style Guidelines

#### Python Code
- **Line length**: 88 characters (Black default)
- **Imports**: Sorted alphabetically, grouped by type
- **Type hints**: Required for all functions and methods
- **Docstrings**: Google-style for public APIs
- **Error handling**: Explicit exception handling with context

#### Example Function
```python
async def create_beehive(
    session: AsyncSession,
    hive_data: BeehiveCreateModel,
    user_id: int,
) -> BeehiveModel:
    """Create a new beehive in the system.

    Args:
        session: Database session for the operation
        hive_data: Validated hive creation data
        user_id: ID of the user creating the hive

    Returns:
        The created beehive model

    Raises:
        BeehiveValidationError: If hive data is invalid
        DatabaseError: If the database operation fails
    """
    # Implementation here
```

### Dependency Management

We use **uv** exclusively for dependency management:

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --group dev package-name

# Add a testing dependency
uv add --group testing package-name

# Update dependencies
uv sync
```

**Never use pip directly** - this ensures consistent dependency resolution and lockfile management.

## 🧪 Experimental Areas

### Current Experiments

1. **Modern Async Patterns**
   - aiohttp with full async pipeline
   - SQLAlchemy async with proper session management
   - Async context managers for resource cleanup

2. **AI-Assisted Development**
   - Cursor AI integration with custom rules
   - MCP (Model Context Protocol) for database queries
   - AI-powered code suggestions and documentation

3. **Developer Experience Tools**
   - uv for ultra-fast dependency management
   - ruff for lightning-fast linting and formatting
   - Pre-commit hooks for automated quality checks

4. **Clean Architecture in Python**
   - Strict layer separation
   - Dependency inversion with interfaces
   - Domain-driven design patterns

5. **DevOps Automation**
   - GitHub Actions with concurrency control
   - Automated dependency updates via Dependabot
   - Comprehensive CI/CD pipeline with quality gates

### Areas for Experimentation

We welcome contributions in these areas:

- **Performance Optimization**: Database query optimization, async patterns
- **Observability**: Logging, metrics, tracing, monitoring
- **Security**: Authentication, authorization, data validation
- **Testing**: Advanced testing patterns, property-based testing
- **Documentation**: API documentation, architectural documentation
- **Deployment**: Container optimization, orchestration patterns

## 🤝 Contributing Guidelines

### Types of Contributions

1. **Code Improvements**
   - Bug fixes and performance improvements
   - New features that align with the experimental goals
   - Refactoring that demonstrates better patterns

2. **Documentation**
   - Code documentation and examples
   - Architectural documentation
   - Tutorial content and guides

3. **Testing & Quality**
   - Additional test cases and coverage improvements
   - Quality tooling improvements
   - CI/CD enhancements

4. **Experimental Features**
   - New technology integrations
   - Alternative architectural approaches
   - Developer tooling experiments

### Submission Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Follow** the code standards and run quality checks
4. **Test** your changes thoroughly
5. **Commit** with clear, descriptive messages
6. **Push** to your fork and create a Pull Request

### Pull Request Guidelines

- **Clear Description**: Explain what you're changing and why
- **Test Coverage**: Include tests for new functionality
- **Quality Checks**: Ensure all CI checks pass
- **Documentation**: Update relevant documentation
- **Incremental Changes**: Keep changes focused and atomic

## 🔍 Code Review Process

All contributions go through code review to maintain quality and provide learning opportunities:

### What We Look For

- **Architectural Fit**: Does it align with clean architecture principles?
- **Code Quality**: Proper type hints, error handling, and documentation
- **Test Coverage**: Comprehensive tests with good assertions
- **Performance**: Efficient async patterns and database usage
- **Learning Value**: Does it demonstrate interesting patterns or techniques?

### Review Criteria

- ✅ **Type Safety**: All code has proper type hints
- ✅ **Testing**: New code is well-tested with good coverage
- ✅ **Documentation**: Public APIs are documented
- ✅ **Error Handling**: Proper exception handling and logging
- ✅ **Async Patterns**: Correct use of async/await and context managers
- ✅ **Architecture**: Follows clean architecture layer separation

## 🐛 Bug Reports & Feature Requests

### Reporting Bugs

Use GitHub Issues with the bug report template:

- **Environment**: Python version, OS, dependency versions
- **Steps to Reproduce**: Clear, minimal reproduction steps
- **Expected vs Actual**: What should happen vs what does happen
- **Additional Context**: Logs, screenshots, related issues

### Requesting Features

For feature requests, explain:

- **Use Case**: What problem does this solve?
- **Implementation Ideas**: How might this work?
- **Experimental Value**: What can we learn from this?
- **Alternatives**: What other approaches exist?

## 🤖 AI Integration Features

### Cursor AI Setup

The project includes Cursor AI integration for enhanced development:

1. **Smart Rules**: Pre-configured in `.cursor/rules/`
2. **MCP Integration**: Database queries through AI interface
3. **Code Suggestions**: Context-aware completions

### Using MCP (Model Context Protocol)

The custom PostgreSQL MCP server allows AI to:
- Query database schema directly
- Generate accurate SQL queries
- Understand data relationships

Configure in `.cursor/mcp.json` and use with compatible AI tools.

## 📚 Learning Resources

### Understanding the Codebase

- **Start with**: `cityhive/app/main.py` for application entry point
- **Architecture**: Study the layer separation in each package
- **Patterns**: Look for dependency injection and async patterns
- **Testing**: Examine test structure for testing strategies

### External Resources

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## 🎯 Project Roadmap

### Short-term Goals
- Improve test coverage to 95%+
- Add comprehensive API documentation
- Implement observability patterns
- Enhance AI integration capabilities

### Long-term Vision
- Demonstrate modern Python web development best practices
- Provide a reference implementation for clean architecture
- Showcase effective DevOps automation
- Create educational content around the patterns used

## 💬 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Code Comments**: Inline documentation explains complex patterns
- **Tests**: Often the best documentation for understanding behavior

## 🙏 Acknowledgments

This project is built on the shoulders of giants. We're grateful to:

- The Python community for excellent async tooling
- The aiohttp team for a fantastic web framework
- The SQLAlchemy team for powerful ORM capabilities
- All the open-source contributors who make projects like this possible

---

**Happy Contributing!** 🚀

Remember: This is a learning environment. Don't be afraid to experiment, ask questions, or propose new ideas. Every contribution helps make this a better resource for the community.
