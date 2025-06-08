"""Tests for cityhive.app.__main__ module."""

import inspect
import subprocess
import sys

import pytest

from cityhive.app.__main__ import run


def test_run_calls_main(mocker):
    mock_main = mocker.patch("cityhive.app.__main__.main")

    run()
    mock_main.assert_called_once()


def test_run_propagates_exceptions(mocker):
    mock_main = mocker.patch("cityhive.app.__main__.main")
    mock_main.side_effect = ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        run()


def test_run_returns_none(mocker):
    mocker.patch("cityhive.app.__main__.main")

    result = run()
    assert result is None


def test_module_has_main_guard_pattern():
    import cityhive.app.__main__ as main_module

    module_source = inspect.getsource(main_module)
    assert 'if __name__ == "__main__":' in module_source
    assert "run()" in module_source


def test_module_execution_imports_correctly():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import cityhive.app.__main__; print('import successful')",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "import successful" in result.stdout


def test_importing_module_does_not_execute_run(mocker):
    mock_run = mocker.patch("cityhive.app.__main__.run")

    mock_run.assert_not_called()


def test_run_function_is_callable_with_proper_docstring():
    from cityhive.app.__main__ import run

    assert callable(run)
    assert run.__doc__ is not None
    assert "run the main application" in run.__doc__.lower()


def test_module_can_be_imported_without_side_effects():
    import cityhive.app.__main__

    assert hasattr(cityhive.app.__main__, "run")


def test_module_has_proper_docstring():
    import cityhive.app.__main__

    assert cityhive.app.__main__.__doc__ is not None
    doc = cityhive.app.__main__.__doc__
    assert "application entry point" in doc.lower()
    assert "cityhive" in doc.lower()


def test_run_function_has_expected_signature():
    sig = inspect.signature(run)

    assert len(sig.parameters) == 0
    assert sig.return_annotation is None


def test_run_delegates_to_main_function():
    from cityhive.app import main

    assert callable(main)
    assert main.__module__ == "cityhive.app.app"
