"""
Logging infrastructure module using structlog for structured JSON logging.

This module provides centralized logging configuration for the CityHive application,
ensuring consistent structured logging across all components with JSON output to stdout.
"""

import logging
import logging.config
import sys
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger, Processor


def configure_stdlib_logging() -> None:
    """
    Configure Python's standard library logging to work with structlog.

    Sets up basic logging configuration to direct all log messages to stdout
    in a 12-factor app compatible way.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_shared_processors() -> list[Processor]:
    """
    Get the shared processors used by both development and production configurations.

    Returns:
        List of structlog processors for common log processing
    """
    return [
        # Merge context variables (for request-scoped context)
        structlog.contextvars.merge_contextvars,
        # Add log level to the event dict
        structlog.processors.add_log_level,
        # Add logger name to the event dict
        structlog.stdlib.add_logger_name,
        # Handle positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add ISO timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Render stack info if present
        structlog.processors.StackInfoRenderer(),
        # Format exception info
        structlog.processors.format_exc_info,
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
        # Add call site information (filename, function name, line number)
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]


def get_processors_for_production() -> list[Processor]:
    """
    Get processors configured for production environment.

    Uses JSON renderer for structured logging and includes structured tracebacks.

    Returns:
        List of structlog processors for production
    """
    return get_shared_processors() + [
        # Use structured tracebacks for better error analysis
        structlog.processors.dict_tracebacks,
        # Render as JSON for production logging systems
        structlog.processors.JSONRenderer(sort_keys=True),
    ]


def get_processors_for_development() -> list[Processor]:
    """
    Get processors configured for development environment.

    Uses console renderer for human-readable output during development.

    Returns:
        List of structlog processors for development
    """
    return get_shared_processors() + [
        # Pretty print for terminal during development
        structlog.dev.ConsoleRenderer(colors=True),
    ]


def configure_structlog(*, force_json: bool = True) -> None:
    """
    Configure structlog for the application.

    Args:
        force_json: If True, always use JSON output. If False, auto-detect based on TTY.
    """
    # Configure standard library logging first
    configure_stdlib_logging()

    # Choose processors based on environment
    if force_json or not sys.stderr.isatty():
        # Use JSON for production or when explicitly requested
        processors = get_processors_for_production()
    else:
        # Use pretty printing for development terminal sessions
        processors = get_processors_for_development()

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """
    Get a configured structlog logger.

    Args:
        name: Optional logger name. If None, uses the calling module's name.

    Returns:
        Configured structlog bound logger
    """
    return structlog.get_logger(name)


def setup_logging(*, force_json: bool = True) -> None:
    """
    Setup application-wide logging configuration.

    This is the main entry point for configuring logging in the application.
    Should be called early in the application startup process.

    Args:
        force_json: If True, always use JSON output. If False, auto-detect based on TTY.
    """
    configure_structlog(force_json=force_json)

    # Get a logger to test the configuration
    logger = get_logger(__name__)
    logger.info("Logging system initialized", force_json=force_json)


def configure_request_logging() -> None:
    """
    Configure request-specific logging context.

    This function can be called from middleware to set up request-scoped
    logging context using structlog's contextvars.
    """
    # Clear any existing context variables to ensure clean state per request
    structlog.contextvars.clear_contextvars()


def bind_request_context(**kwargs: Any) -> None:
    """
    Bind request-specific context to logging.

    Args:
        **kwargs: Key-value pairs to bind to the logging context
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    """Clear request-specific logging context."""
    structlog.contextvars.clear_contextvars()


class StructlogHandler(logging.Handler):
    """
    Custom logging handler that routes standard library logs to structlog.

    This allows third-party libraries (like Alembic, SQLAlchemy) that use
    standard Python logging to integrate with our structured logging system.
    """

    def __init__(self, logger_name: str = "third_party"):
        super().__init__()
        self.structlog_logger = structlog.get_logger(logger_name)

    def emit(self, record: logging.LogRecord) -> None:
        """Convert stdlib log record to structured log entry."""
        level_name = record.levelname.lower()
        log_method = getattr(
            self.structlog_logger, level_name, self.structlog_logger.info
        )

        log_kwargs = {
            "logger_name": record.name,
            "module": getattr(record, "module", "unknown"),
            "func_name": record.funcName,
            "lineno": record.lineno,
        }

        # Include exception information if present
        if record.exc_info:
            log_kwargs["exc_info"] = record.exc_info

        log_method(record.getMessage(), **log_kwargs)


def configure_third_party_loggers(
    *logger_names: str, level: int = logging.INFO
) -> None:
    """
    Configure third-party loggers to use structured logging.

    Args:
        *logger_names: Names of loggers to configure
            (e.g., 'alembic', 'sqlalchemy.engine')
        level: Log level to set for these loggers
    """
    handler = StructlogHandler("third_party")

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
