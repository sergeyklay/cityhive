import asyncio
import os
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

project_root = Path(__file__).parent.parent
dotenv_path = project_root / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_uri = os.getenv("DATABASE_URI", None)
if not database_uri or not str(database_uri).strip():
    raise ValueError("DATABASE_URI environment variable is not set")

# Check if we're running in Docker
is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER") == "true"

# Check if we're running in Kubernetes
is_kubernetes = bool(os.getenv("KUBERNETES_SERVICE_HOST"))

# Patch the database URI if we're running in local development
# and the database is running in a container.
if not is_docker and not is_kubernetes:
    parsed = urlparse(database_uri)
    if parsed.hostname in {"cityhive", "cityhive-db"}:
        netloc = ""
        if parsed.username:
            netloc += parsed.username
        if parsed.password:
            netloc += f":{parsed.password}"
        if parsed.username or parsed.password:
            netloc += "@"
        netloc += "127.0.0.1"
        if parsed.port:
            netloc += f":{parsed.port}"

        parsed = parsed._replace(netloc=netloc)
        database_uri = urlunparse(parsed)

# Get the active config section from alembic.ini (typically 'alembic')
ini_section = config.config_ini_section
if not ini_section:
    raise ValueError("Alembic config section is not set, check alembic.ini")

# Set the DATABASE_URI value in the alembic.ini config section
# This makes the database connection string available to Alembic.
#
# Python’s configparser uses % for interpolation (e.g., %(option)s).
# If database URI contains a %, configparser will try to interpret it as an
# interpolation marker, which can cause errors or unexpected behavior.
# For example, this will lead to an error:
#
#     $ DATABASE_URI="postgresql://user:pa%ss@host/db" alembic upgrade head
#
# To include a literal % in a value, we must double it: %%.
config.set_section_option(ini_section, "DATABASE_URI", database_uri.replace("%", "%%"))

# add your model's MetaData object here
# for 'autogenerate' support
from cityhive import models

target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = async_engine_from_config(
        config.get_section(ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
