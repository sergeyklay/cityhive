# AI Integration

CityHive includes AI-assisted development configuration for working with AI coding assistants, particularly Cursor AI and MCP (Model Context Protocol) integration.

## Cursor AI Integration

### Pre-configured Development Rules

The project includes Cursor AI configuration in the `.cursor/rules/` directory with actual rule files:

- `ai-collaboration.mdc`: Guidelines for working with AI assistants
- `cursor-rules.mdc`: Cursor-specific development rules
- `dependency-management.mdc`: Package management guidelines
- `project-overview.mdc`: Project structure and overview
- `python-standards.mdc`: Python coding standards
- `testing-guidelines.mdc`: Test writing best practices

These files provide context and guidelines that help AI assistants understand the project structure and coding standards.

### Editor Integration

The project is configured for use with Cursor AI editor, which provides:
- Context-aware code suggestions based on project patterns
- Understanding of clean architecture layers
- Type hint assistance and validation
- Import resolution and style guidance

## MCP (Model Context Protocol) Server

### PostgreSQL Database Access

The project includes an actual MCP server at `.cursor/postgres.py` that provides AI assistants with read-only database access for better context understanding.

### Configuration

The MCP server configuration is defined in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cityhive_db": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--python",
        "./.venv/bin/python",
        "./.cursor/postgres.py",
        "--db",
        "postgresql://cityhive:cityhive@127.0.0.1:5432/cityhive",
        "--debug",
        "--min-connections",
        "1",
        "--max-connections",
        "10"
      ]
    }
  }
}
```

### Capabilities

The MCP server provides AI assistants with:
- Database schema inspection capabilities
- Read-only query execution
- Understanding of data relationships and constraints
- Context for generating database-related code

### Security

- **Read-Only Access**: The MCP server only allows SELECT operations
- **Development Environment**: Configured for local development database only
- **Isolated Connection**: Uses separate connection pool for AI queries

## Using AI Integration

### Development Workflow

With the AI integration configured, you can:

1. **Ask about database schema**: AI can query the actual database structure
2. **Get architecture guidance**: AI understands the clean architecture patterns from the rules
3. **Receive code suggestions**: AI follows the established coding standards
4. **Generate tests**: AI knows the testing patterns and requirements

### Code Generation

The AI integration helps with:
- Generating aiohttp route handlers following project patterns
- Creating SQLAlchemy models with proper relationships
- Writing tests that follow the established structure
- Adding proper type hints and documentation

### Best Practices

When working with the AI integration:

1. **Reference Architecture**: Ask AI to follow clean architecture principles
2. **Use Type Hints**: Request properly typed code generation
3. **Include Tests**: Always ask for tests with new functionality
4. **Follow Standards**: Reference the coding standards in your requests

## Configuration Files

### Cursor Rules Directory

The `.cursor/rules/` directory contains:
- **ai-collaboration.mdc**: How to work effectively with AI
- **cursor-rules.mdc**: Cursor-specific configuration
- **dependency-management.mdc**: uv usage guidelines
- **project-overview.mdc**: Project structure and goals
- **python-standards.mdc**: Code formatting and style rules
- **testing-guidelines.mdc**: Testing approach and patterns

### MCP Server

The `.cursor/postgres.py` file implements the MCP server that allows AI to:
- Query database schema information
- Understand table relationships
- Provide context-aware database suggestions
- Generate accurate SQL queries

## Troubleshooting

### Common Issues

**MCP Server Connection:**
If the AI cannot access the database:
1. Ensure PostgreSQL is running: `docker compose up postgres`
2. Check database connectivity: `uv run python -c "import asyncpg; print('ok')"`
3. Verify the database URL in `.cursor/mcp.json` matches your setup

**Cursor AI Not Working:**
- Restart Cursor editor
- Check internet connection
- Verify that `.cursor/rules/` files are present and readable

**Database Access Issues:**
- Ensure the development database is running
- Check that the connection string in `mcp.json` is correct
- Verify that the Python environment can access the database

### Manual Verification

To test the MCP server manually:
```bash
# Check if database is accessible
docker compose ps postgres

# Test Python database connectivity
uv run python -c "
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect('postgresql://cityhive:cityhive@127.0.0.1:5432/cityhive')
    print('Database connection successful')
    await conn.close()

asyncio.run(test())
"
```

## Future Enhancements

The AI integration provides a foundation for enhanced development workflows. The current setup focuses on:
- Understanding project architecture and patterns
- Providing database context for code generation
- Following established coding standards and testing practices

This creates a development environment where AI assistance is informed by the actual project structure and requirements.
