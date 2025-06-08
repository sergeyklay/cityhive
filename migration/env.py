import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Setup structured logging for Alembic
from cityhive.infrastructure.logging import (
    configure_third_party_loggers,
    get_logger,
    setup_logging,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

project_root = Path(__file__).parent.parent
dotenv_path = project_root / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Setup structured logging with JSON output for consistent logging
setup_logging(force_json=True)
logger = get_logger("migration.env")

# Configure third-party loggers to use our structured logging system
configure_third_party_loggers("alembic", "sqlalchemy.engine")

# Allow DATABASE_URI override via environment variable, this allows running
# migrations with a override for the database URI:
#
#     $ DATABASE_URI=... alembic upgrade head
#
database_uri = os.getenv("DATABASE_URI", None)
if not database_uri or not str(database_uri).strip():
    # This should be imported after the dotenv is loaded
    from cityhive.infrastructure.config import get_config

    database_uri = get_config().database_uri

if not database_uri or not str(database_uri).strip():
    raise ValueError("DATABASE_URI environment variable is not set")

database_uri = str(database_uri).strip()

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
from cityhive.domain import models

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
    logger.info("Starting offline migrations", mode="offline", database_url=url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

    logger.info("Offline migrations completed", mode="offline")


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter objects to include in autogenerate.

    This prevents Alembic from dropping PostGIS-related tables and other
    system tables that exist in the database but aren't part of our models.
    """
    if type_ == "table" and reflected and compare_to is None:
        # Skip PostGIS system tables
        postgis_tables = {
            "spatial_ref_sys",
            "geometry_columns",
            "geography_columns",
            "raster_columns",
            "raster_overviews",
            # TIGER geocoding tables
            "addr",
            "addrfeat",
            "bg",
            "county",
            "county_lookup",
            "countysub_lookup",
            "cousub",
            "direction_lookup",
            "edges",
            "faces",
            "featnames",
            "geocode_settings",
            "geocode_settings_default",
            "layer",
            "loader_lookuptables",
            "loader_platform",
            "loader_variables",
            "pagc_gaz",
            "pagc_lex",
            "pagc_rules",
            "place",
            "place_lookup",
            "secondary_unit_lookup",
            "state",
            "state_lookup",
            "street_type_lookup",
            "tabblock",
            "tabblock20",
            "topology",
            "tract",
            "zip_lookup",
            "zip_lookup_all",
            "zip_lookup_base",
            "zip_state",
            "zip_state_loc",
            "zcta5",
        }

        if name in postgis_tables:
            return False

    return True


def do_run_migrations(connection):
    logger.info("Configuring migration context", mode="online")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        logger.info("Running migrations", mode="online")
        context.run_migrations()
        logger.info("Migrations completed successfully", mode="online")


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    logger.info("Starting async migrations", mode="online")

    connectable = async_engine_from_config(
        config.get_section(ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        logger.info("Database connection established", mode="online")
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
    logger.info("Database connection disposed", mode="online")


def run_migrations_online():
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
