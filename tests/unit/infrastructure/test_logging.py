"""Unit tests for cityhive.infrastructure.logging module."""

import logging
import sys
from unittest.mock import MagicMock

import pytest
import structlog

from cityhive.infrastructure.logging import (
    bind_request_context,
    clear_request_context,
    configure_request_logging,
    configure_stdlib_logging,
    configure_structlog,
    get_logger,
    get_processors_for_development,
    get_processors_for_production,
    get_shared_processors,
    setup_logging,
)


def test_configure_stdlib_logging_sets_basic_config(mocker):
    mock_basic_config = mocker.patch("logging.basicConfig")

    configure_stdlib_logging()

    mock_basic_config.assert_called_once_with(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def test_get_shared_processors_returns_expected_number_of_processors():
    processors = get_shared_processors()

    assert len(processors) == 9
    assert callable(processors[0])  # merge_contextvars
    assert callable(processors[1])  # add_log_level
    assert callable(processors[2])  # add_logger_name
    assert isinstance(processors[3], structlog.stdlib.PositionalArgumentsFormatter)
    assert isinstance(processors[4], structlog.processors.TimeStamper)
    assert callable(processors[5])  # StackInfoRenderer or similar
    assert callable(processors[6])  # format_exc_info
    assert callable(processors[7])  # UnicodeDecoder
    assert isinstance(processors[8], structlog.processors.CallsiteParameterAdder)


def test_get_shared_processors_timestamper_uses_iso_utc():
    processors = get_shared_processors()

    timestamper = next(
        p for p in processors if isinstance(p, structlog.processors.TimeStamper)
    )

    assert timestamper.fmt == "iso"
    assert timestamper.utc is True


def test_get_shared_processors_includes_callsite_parameter_adder():
    processors = get_shared_processors()

    callsite_adder = next(
        p
        for p in processors
        if isinstance(p, structlog.processors.CallsiteParameterAdder)
    )

    assert isinstance(callsite_adder, structlog.processors.CallsiteParameterAdder)


def test_get_processors_for_production_includes_shared_processors(mocker):
    mock_get_shared = mocker.patch(
        "cityhive.infrastructure.logging.get_shared_processors"
    )
    mock_shared_processors = [MagicMock(), MagicMock()]
    mock_get_shared.return_value = mock_shared_processors

    processors = get_processors_for_production()

    assert processors[:2] == mock_shared_processors
    assert isinstance(processors[-2], type(structlog.processors.dict_tracebacks))
    assert isinstance(processors[-1], structlog.processors.JSONRenderer)


def test_get_processors_for_production_includes_json_renderer():
    processors = get_processors_for_production()

    json_renderer = processors[-1]

    assert isinstance(json_renderer, structlog.processors.JSONRenderer)


def test_get_processors_for_development_includes_shared_processors(mocker):
    mock_get_shared = mocker.patch(
        "cityhive.infrastructure.logging.get_shared_processors"
    )
    mock_shared_processors = [MagicMock(), MagicMock()]
    mock_get_shared.return_value = mock_shared_processors

    processors = get_processors_for_development()

    assert processors[:2] == mock_shared_processors
    assert isinstance(processors[-1], structlog.dev.ConsoleRenderer)


def test_get_processors_for_development_includes_console_renderer():
    processors = get_processors_for_development()

    console_renderer = processors[-1]

    assert isinstance(console_renderer, structlog.dev.ConsoleRenderer)


@pytest.mark.parametrize(
    "force_json,is_tty,expected_processor_type",
    [
        (True, True, "production"),
        (True, False, "production"),
        (False, True, "development"),
        (False, False, "production"),
    ],
)
def test_configure_structlog_chooses_correct_processors(
    mocker, force_json, is_tty, expected_processor_type
):
    mock_configure_stdlib = mocker.patch(
        "cityhive.infrastructure.logging.configure_stdlib_logging"
    )
    mocker.patch("structlog.configure")
    mocker.patch("sys.stderr.isatty", return_value=is_tty)
    mock_get_production = mocker.patch(
        "cityhive.infrastructure.logging.get_processors_for_production"
    )
    mock_get_development = mocker.patch(
        "cityhive.infrastructure.logging.get_processors_for_development"
    )

    configure_structlog(force_json=force_json)

    mock_configure_stdlib.assert_called_once()
    if expected_processor_type == "production":
        mock_get_production.assert_called_once()
        mock_get_development.assert_not_called()
    else:
        mock_get_development.assert_called_once()
        mock_get_production.assert_not_called()


def test_configure_structlog_calls_structlog_configure_with_expected_params(mocker):
    mocker.patch("cityhive.infrastructure.logging.configure_stdlib_logging")
    mock_structlog_configure = mocker.patch("structlog.configure")
    mock_processors = [MagicMock()]
    mocker.patch(
        "cityhive.infrastructure.logging.get_processors_for_production",
        return_value=mock_processors,
    )
    mock_filtering_logger = MagicMock()
    mock_make_filtering = mocker.patch(
        "structlog.make_filtering_bound_logger", return_value=mock_filtering_logger
    )
    mock_logger_factory = MagicMock()
    mocker.patch("structlog.stdlib.LoggerFactory", return_value=mock_logger_factory)

    configure_structlog(force_json=True)

    mock_make_filtering.assert_called_once_with(logging.INFO)
    mock_structlog_configure.assert_called_once_with(
        processors=mock_processors,
        wrapper_class=mock_filtering_logger,
        context_class=dict,
        logger_factory=mock_logger_factory,
        cache_logger_on_first_use=True,
    )


def test_get_logger_returns_structlog_logger(mocker):
    mock_structlog_get_logger = mocker.patch("structlog.get_logger")
    mock_logger = MagicMock()
    mock_structlog_get_logger.return_value = mock_logger

    result = get_logger("test_logger")

    mock_structlog_get_logger.assert_called_once_with("test_logger")
    assert result == mock_logger


def test_get_logger_with_no_name_passes_none(mocker):
    mock_structlog_get_logger = mocker.patch("structlog.get_logger")

    get_logger()

    mock_structlog_get_logger.assert_called_once_with(None)


def test_setup_logging_configures_structlog_and_logs_initialization(mocker):
    mock_configure_structlog = mocker.patch(
        "cityhive.infrastructure.logging.configure_structlog"
    )
    mock_get_logger = mocker.patch("cityhive.infrastructure.logging.get_logger")
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    setup_logging(force_json=True)

    mock_configure_structlog.assert_called_once_with(force_json=True)
    mock_get_logger.assert_called_once_with("cityhive.infrastructure.logging")
    mock_logger.info.assert_called_once_with(
        "Logging system initialized", force_json=True
    )


def test_setup_logging_with_force_json_false(mocker):
    mock_configure_structlog = mocker.patch(
        "cityhive.infrastructure.logging.configure_structlog"
    )
    mock_get_logger = mocker.patch("cityhive.infrastructure.logging.get_logger")
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    setup_logging(force_json=False)

    mock_configure_structlog.assert_called_once_with(force_json=False)
    mock_logger.info.assert_called_once_with(
        "Logging system initialized", force_json=False
    )


def test_configure_request_logging_clears_contextvars(mocker):
    mock_clear = mocker.patch("structlog.contextvars.clear_contextvars")

    configure_request_logging()

    mock_clear.assert_called_once()


def test_bind_request_context_calls_bind_contextvars(mocker):
    mock_bind = mocker.patch("structlog.contextvars.bind_contextvars")
    test_kwargs = {"request_id": "123", "user_id": "456"}

    bind_request_context(**test_kwargs)

    mock_bind.assert_called_once_with(**test_kwargs)


def test_bind_request_context_with_empty_kwargs(mocker):
    mock_bind = mocker.patch("structlog.contextvars.bind_contextvars")

    bind_request_context()

    mock_bind.assert_called_once_with()


def test_clear_request_context_calls_clear_contextvars(mocker):
    mock_clear = mocker.patch("structlog.contextvars.clear_contextvars")

    clear_request_context()

    mock_clear.assert_called_once()


@pytest.mark.parametrize(
    "context_data",
    [
        {"request_id": "req-123"},
        {"user_id": "user-456", "session_id": "sess-789"},
        {"method": "POST", "path": "/api/users", "remote": "192.168.1.1"},
        {},
    ],
)
def test_bind_request_context_with_various_data(mocker, context_data):
    mock_bind = mocker.patch("structlog.contextvars.bind_contextvars")

    bind_request_context(**context_data)

    mock_bind.assert_called_once_with(**context_data)


def test_shared_processors_order_is_correct():
    processors = get_shared_processors()

    processor_types = [type(p).__name__ for p in processors]
    expected_order = [
        "function",  # merge_contextvars
        "function",  # add_log_level
        "function",  # add_logger_name
        "PositionalArgumentsFormatter",
        "TimeStamper",
        "function",  # StackInfoRenderer
        "function",  # format_exc_info
        "function",  # UnicodeDecoder
        "CallsiteParameterAdder",
    ]

    assert len(processor_types) == len(expected_order)
    for i, expected_type in enumerate(expected_order):
        if expected_type == "function":
            assert callable(processors[i])
        else:
            assert processor_types[i] == expected_type


def test_production_processors_include_json_renderer_at_end():
    processors = get_processors_for_production()

    assert isinstance(processors[-1], structlog.processors.JSONRenderer)
    assert isinstance(processors[-2], type(structlog.processors.dict_tracebacks))


def test_development_processors_include_console_renderer_at_end():
    processors = get_processors_for_development()

    assert isinstance(processors[-1], structlog.dev.ConsoleRenderer)
