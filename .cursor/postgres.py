import json
import logging
import os
import select
import signal
import sys
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

import asyncpg
import click
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, Field

# -------------------------------- zombie-killer --------------------------------

# When you close Cursor, the MCP server process (like this .cursor/postgres.py) is not
# always killed. This leads to orphaned MCP processes, and if you reopen Cursor, new MCP
# processes are started, resulting in multiple lingering processes. This is not specific
# to this implementation; it affects other Cursor users and MCP server types as well.
#
# For details see:
# - https://forum.cursor.com/t/exiting-the-cursor-will-not-kill-the-mcp-process/74296
#
# A temporary workaround:
#
# % pgrep -fl .cursor/postgres.py | awk '{print $1}' | xargs kill -9
#
# Another temporary workaround is to use the following zombie-killer logic:

_PARENT_PID = os.getppid()


def _stdin_hup():
    poller = select.poll()
    poller.register(sys.stdin, select.POLLHUP)
    while True:
        if poller.poll(1000):  # ≥1 second; does not block the thread
            os.kill(os.getpid(), signal.SIGTERM)


def _parent_watcher() -> None:
    while True:
        if os.getppid() != _PARENT_PID:  # Parent process died
            os.kill(os.getpid(), signal.SIGTERM)  # Gracefully stop the service
        time.sleep(2)


def _graceful_exit(*_):
    logger.info("STDIN closed or signal received, shutting down MCP server...")
    sys.exit(0)


for fn in (_parent_watcher, _stdin_hup):
    threading.Thread(target=fn, daemon=True).start()

signal.signal(signal.SIGINT, _graceful_exit)
signal.signal(signal.SIGTERM, _graceful_exit)

# -------------------------------- logging --------------------------------

logger = get_logger("postgres_mcp")

cwd = os.path.dirname(__file__)

logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(cwd, "postgres_mcp.log"))
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


# -------------------------------- database service --------------------------------


class DatabaseService:
    """Service for managing database connections and operations.

    Args:
        database_url: The database URL.
        min_connections: The minimum number of connections in the pool.
        max_connections: The maximum number of connections in the pool.
    """

    def __init__(
        self,
        database_url: str,
        min_connections: int = 1,
        max_connections: int = 10,
    ):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create and open the connection pool."""
        if self.pool is not None:
            logger.warning("Connection pool already exists, not creating a new one.")
            return

        logger.info("Creating database connection pool...")
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=self.min_connections,
            max_size=self.max_connections,
        )
        logger.info("Database pool created.")

    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool is None:
            logger.warning("No connection pool to close.")
            return

        logger.info("Closing database pool...")
        await self.pool.close()
        self.pool = None
        logger.info("Database pool closed.")

    def _check_connection(self) -> asyncpg.Pool:
        """Check if the connection pool exists."""
        if self.pool is None:
            raise ValueError(
                "Database connection pool not initialized. Call connect() first."
            )
        return self.pool

    async def execute_query(
        self, query: str, params: tuple | None = None
    ) -> list[dict[str, Any]]:
        """Execute a read-only query and return results as a list of dictionaries.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries, one for each row
        """
        pool = self._check_connection()
        truncated = query[:100] + "..." if len(query) > 100 else query
        logger.info("Executing query: %s", truncated)

        try:
            async with pool.acquire() as conn:
                # Execute the query with parameters if provided
                if params:
                    results = await conn.fetch(query, *params)
                else:
                    results = await conn.fetch(query)

                # Convert Record objects to dictionaries
                rows_as_dicts = [dict(row) for row in results]

                # Log the result count
                row_count = len(results)
                logger.info("Query executed: %d rows returned.", row_count)
                return rows_as_dicts

        except Exception as db_err:
            # Handle asyncpg errors and other database-related exceptions
            if hasattr(db_err, "__module__") and "asyncpg" in str(db_err.__module__):
                logger.error("Database error during query: %s", db_err)
                error_message = f"Database error: {str(db_err)}"
            else:
                logger.error("Unexpected error during query: %s", db_err)
                error_message = f"Query execution failed: {db_err}"
            raise ValueError(error_message) from db_err

    async def execute_sql_query(
        self,
        query: str,
        params: tuple | None = None,
    ) -> list[asyncpg.Record]:
        """Execute a parameterized SQL query.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of asyncpg.Record objects with raw query results
        """
        pool = self._check_connection()
        try:
            async with pool.acquire() as conn:
                if params:
                    return await conn.fetch(query, *params)
                return await conn.fetch(query)
        except Exception as e:
            # Handle asyncpg errors and other exceptions
            if hasattr(e, "__module__") and "asyncpg" in str(e.__module__):
                logger.error("Database error: %s", e)
                raise ValueError(f"Database error: {e}") from e
            else:
                logger.error("Unexpected error: %s", e)
                raise ValueError(f"Query execution failed: {e}") from e

    async def list_all_tables(self) -> list[str]:
        """List all tables in all schemas in the search path.

        Returns:
            List of tables in format schema.table
        """
        query = """
            WITH search_path_schemas AS (
              SELECT unnest(string_to_array(current_setting(
                'search_path'), ', ')) AS schema_name
            )
            SELECT
              CONCAT(t.table_schema, '.', t.table_name)
            FROM
              information_schema.tables t
            JOIN
              search_path_schemas s ON t.table_schema = s.schema_name
            WHERE
              t.table_type IN ('BASE TABLE', 'FOREIGN')
            ORDER BY
              t.table_schema;
        """

        try:
            results = await self.execute_sql_query(query)
            tables = [row[0] for row in results]
            logger.info("Found %d tables.", len(tables))
            return tables
        except Exception as e:
            logger.error("Error listing tables: %s", e)
            raise ValueError(f"Failed to list tables: {e}") from e

    async def list_tables_in_schema(self, schema_name: str) -> list[str]:
        """List all tables in a specific schema.

        Args:
            schema_name: Schema name to query

        Returns:
            List of tables in format schema.table
        """
        query = """
            SELECT
              CONCAT(t.table_schema, '.', t.table_name)
            FROM
              information_schema.tables t
            WHERE
              t.table_schema = $1 AND
              t.table_type IN ('BASE TABLE', 'FOREIGN')
            ORDER BY
              t.table_schema;
        """

        try:
            results = await self.execute_sql_query(query, (schema_name,))
            tables = [row[0] for row in results]
            logger.info("Found %d tables in schema %s.", len(tables), schema_name)
            return tables
        except Exception as e:
            logger.error("Error listing tables in schema %s: %s", schema_name, e)
            raise ValueError(f"Failed to list tables: {e}") from e

    async def get_table_schema(self, table_name: str) -> str:
        """Get schema information for a table.

        Args:
            table_name: Table name in format schema.table

        Returns:
            JSON string with column information
        """
        logger.info("Fetching schema for table: %s", table_name)

        # Parse schema and table
        try:
            parts = table_name.split(".", 1)  # Split only once
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid table name format: '{table_name}'."
                    " Expected 'schema.table'."
                )
            schema, table = parts[0], parts[1]
            logger.debug("Parsed schema='%s', table='%s'", schema, table)
        except Exception as e:
            logger.error("Error parsing table name '%s': %s", table_name, e)
            raise ValueError(f"Invalid table name format provided: {table_name}") from e

        # Query for column information
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = $2
            ORDER BY ordinal_position;
        """

        try:
            columns = await self.execute_sql_query(query, (table, schema))
            if not columns:
                logger.warning("Table '%s' not found or has no columns.", table_name)
                raise ValueError(f"Table '{table_name}' not found or is empty.")

            schema_info = [
                {"column_name": col[0], "data_type": col[1]} for col in columns
            ]
            logger.info(
                "Schema fetched for %s with %d columns.", table_name, len(columns)
            )
            return json.dumps(schema_info, indent=2)
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error("Error fetching schema for %s: %s", table_name, e)
            raise ValueError(f"Failed to get schema: {e}") from e

    async def column_type(self, table_name: str, column_name: str) -> str:
        """Get the data type of a column in a table.

        Args:
            table_name: Table name in format schema.table
            column_name: The column name

        Returns:
            The data type as a string
        """
        logger.info("Fetching column type for %s.%s", table_name, column_name)
        # Parse schema and table
        try:
            parts = table_name.split(".", 1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid table name format: '{table_name}'."
                    " Expected 'schema.table'."
                )
            schema, table = parts[0], parts[1]
            logger.debug("Parsed schema='%s', table='%s'", schema, table)
        except Exception as e:
            logger.error("Error parsing table name '%s': %s", table_name, e)
            raise ValueError(f"Invalid table name format provided: {table_name}") from e

        query = """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = $2 AND column_name = $3
            """
        try:
            result = await self.execute_sql_query(query, (table, schema, column_name))
            if not result:
                logger.warning(
                    "Column '%s' not found in table '%s'.",
                    column_name,
                    table_name,
                )
                return "unknown"
            logger.info(
                "Column type for %s.%s: %s",
                table_name,
                column_name,
                result[0][0],
            )
            return result[0][0]
        except Exception as e:
            logger.error(
                "Error fetching column type for %s.%s: %s",
                table_name,
                column_name,
                str(e),
            )
            return "unknown"

    async def list_schemas(self) -> list[dict[str, Any]]:
        """List all schemas in the database.

        Returns:
            List of schema names.
        """
        query = """
            SELECT
            schema_name,
            schema_owner,
            CASE
                WHEN schema_name LIKE 'pg_%' THEN 'System Schema'
                WHEN schema_name = 'information_schema' THEN 'System Information Schema'
                ELSE 'User Schema'
            END as schema_type
            FROM information_schema.schemata
            ORDER BY schema_name;
            """
        try:
            results = await self.execute_sql_query(query)
            schemas = [
                {
                    "schema_name": row[0],
                    "schema_owner": row[1],
                    "schema_type": row[2],
                }
                for row in results
            ]
            logger.info("Found %d schemas", len(schemas))
            return schemas
        except Exception as e:
            logger.error("Error listing schemas: %s", e)
            raise ValueError(f"Failed to list schemas: {e}") from e


# -------------------------------- models --------------------------------


class Settings(BaseModel):
    """Settings for the PostgreSQL MCP server."""

    # Make database_url optional initially, it will be set by main()
    database_url: str | None = Field(
        None,
        description="PostgreSQL database connection URL (e.g., postgresql://user:pass@host:port/db).",
    )

    debug: bool = Field(
        False,
        description="Enable debug output",
    )

    min_connections: int = Field(
        default=1,
        description="Pool minimum size",
    )

    max_connections: int = Field(
        default=10,
        description="Pool maximum size",
    )


@dataclass
class AppContext:
    db: DatabaseService


# -------------------------------- lifespan --------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage the database service during server lifecycle."""
    logger.info("Starting up database service...")
    if settings.database_url is None:
        raise ValueError("Database URL not configured before lifespan startup.")

    # Create database service
    db = DatabaseService(
        settings.database_url,
        min_connections=settings.min_connections,
        max_connections=settings.max_connections,
    )
    try:
        # Connect to the database
        await db.connect()

        # Make database service available via context
        yield AppContext(db=db)
    finally:
        logger.info("Shutting down database service...")
        await db.close()
        logger.info("Database service closed.")


def get_safe_display_url(url: str) -> str:
    """Returns a safe URL for display, with credentials masked."""
    if not url or "://" not in url:
        return "[URL details hidden]"

    try:
        parsed_url = urlparse(url)
        # Create a netloc string with password hidden
        safe_netloc = parsed_url.hostname or ""
        if parsed_url.port:
            safe_netloc += f":{parsed_url.port}"

        if parsed_url.username:
            if parsed_url.password:
                safe_netloc = f"{parsed_url.username}:*****@{safe_netloc}"
            else:
                safe_netloc = f"{parsed_url.username}@{safe_netloc}"

        # Reconstruct the URL without the password for logging
        safe_url_parts = (
            parsed_url.scheme,
            safe_netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
        return urlunparse(safe_url_parts)
    except Exception:
        return "[URL details hidden]"


# Create a global settings instance
settings = Settings(
    database_url=None,
    debug=False,
    min_connections=1,
    max_connections=10,
)

server = FastMCP(
    name="postgres",
    instructions="Query a Postgres database and return results",
    dependencies=["asyncpg", "click", "pydantic"],
    lifespan=lifespan,  # Register the lifespan manager
)


# -------------------------------- tools --------------------------------


@server.tool()
async def list_all_tables(ctx: Context) -> list[str]:
    """
    Lists all tables in all the schemas in the search_path.

    Returns:
        A list of table names.

    Example:
        list_all_tables()
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        return await db.list_all_tables()
    except Exception as e:
        logger.exception("Error listing all tables: %s", str(e))
        raise ValueError(f"Failed to list tables: {e}") from e


@server.tool()
async def list_tables_in_schema(
    ctx: Context, schema_name: str = Field(..., description="Name of the schema")
) -> list[str]:
    """
    Lists all tables in a specified schema.

    Args:
        schema_name: The name of the schema to list tables from.

    Returns:
        A list of table names.
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        return await db.list_tables_in_schema(schema_name)
    except Exception as e:
        logger.exception("Error listing tables in schema: %s", str(e))
        raise ValueError(f"Failed to list tables: {e}") from e


@server.tool()
async def get_table_schema(
    ctx: Context,
    table_name: str = Field(
        ..., description="Name of the table with schema, i.e. public.my_table"
    ),
) -> str:
    """
    Gets the column names and data types for a specific table.
    Expects the table name in the format 'schema.table'.

    Args:
        table_name: The name of the table to get the schema for.

    Returns:
        A JSON string with column information.
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        return await db.get_table_schema(table_name)
    except Exception as e:
        logger.exception("Error getting table schema: %s", str(e))
        raise ValueError(f"Failed to get table schema: {e}") from e


@server.tool()
async def query(
    ctx: Context,
    sql: str = Field(..., description="Read-only SQL query to execute"),
) -> str:
    """
    Runs a read-only SQL query against the database and returns results as JSON.
    Only SELECT statements are effectively processed due to read-only transaction.
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        results = await db.execute_query(sql)

        # The execute_query method returns a list of dictionaries
        # Convert to JSON string with appropriate formatting
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        logger.exception("Error executing query: %s", str(e))
        raise ValueError(f"Failed to execute query: {e}") from e


@server.tool(description="Get the data type of a column in a given table.")
async def column_type(
    ctx: Context,
    table_name: str = Field(
        ..., description="Name of the table with schema, i.e. public.my_table"
    ),
    column_name: str = Field(..., description="The column name."),
) -> str:
    """
    Returns the data type of a column in a table.

    Args:
        table_name: The table name in format 'schema.table'.
        column_name: The column name.

    Returns:
        The data type as a string.
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        return await db.column_type(table_name, column_name)
    except Exception as e:
        logger.exception("Error getting column type: %s", str(e))
        raise ValueError(f"Failed to get column type: {e}") from e


@server.tool(description="Lists all schemas in the database.")
async def list_schemas(ctx: Context) -> list[dict[str, Any]]:
    """
    Lists all schemas in the database.

    Returns:
        A list of schema names and owners.

    Example:
        list_schemas()
    """
    try:
        app_context: AppContext = ctx.request_context.lifespan_context
        db: DatabaseService = app_context.db
        return await db.list_schemas()
    except Exception as e:
        logger.exception("Error listing schemas: %s", str(e))
        raise ValueError(f"Failed to list schemas: {e}") from e


# -------------------------------- main --------------------------------


@click.command()
@click.option(
    "--db",
    envvar="DATABASE_URI",
    required=True,
    help="PostgreSQL database connection URL (e.g., postgresql://user:pass@host:port/db).",
)
@click.option(
    "--debug",
    required=False,
    is_flag=True,
    help="Enable debug output",
)
@click.option(
    "--min-connections",
    type=int,
    default=1,
    required=False,
    help="Pool minimum size",
)
@click.option(
    "--max-connections",
    type=int,
    default=10,
    required=False,
    help="Pool maximum size",
)
def main(db: str, debug: bool, min_connections: int, max_connections: int):
    """Starts the Postgres MCP server."""
    settings.database_url = db
    settings.debug = debug
    settings.min_connections = min_connections
    settings.max_connections = max_connections

    safe_display_url = get_safe_display_url(settings.database_url)
    logger.info("Starting PostgreSQL MCP server for %s...", safe_display_url)
    logger.info("Running on stdio...")

    if debug:
        logger.setLevel(logging.DEBUG)
        server.settings.debug = True
        server.settings.log_level = "DEBUG"

    # server.run() will now execute with the database_url set above
    try:
        server.run()
    except (EOFError, BrokenPipeError):
        _graceful_exit()


if __name__ == "__main__":
    main()
