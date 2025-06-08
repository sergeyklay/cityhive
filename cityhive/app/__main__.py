#!/usr/bin/env python3

"""
Application entry point for running the CityHive web application.

This module provides the main entry point when the app package is executed
directly with `python -m cityhive.app`.
"""

from cityhive.app import main


def run() -> None:
    """
    Run the main application.

    This function ensures that the main application is only executed when this
    file is run directly, not when imported as a module.
    """
    main()


if __name__ == "__main__":
    run()
