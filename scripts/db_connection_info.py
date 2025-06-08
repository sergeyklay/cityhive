#!/usr/bin/env python3

"""Extract database connection details from DATABASE_URI environment variable.

This script parses a PostgreSQL connection URI and extracts host, port, username,
and database name for use in shell scripts. It provides sensible defaults for
missing components like port numbers.
"""

import os
import sys
from urllib.parse import urlparse


def get_default_port(scheme: str) -> int:
    """Get default port based on database scheme."""
    if scheme.startswith("postgres"):
        return 5432
    if scheme.startswith("mysql"):
        return 3306

    # Default to PostgreSQL port for unknown schemes
    return 5432


def main() -> None:
    """Extract and validate database connection information."""
    try:
        uri = os.environ.get("DATABASE_URI", "")
        if not uri:
            print(
                "ERROR: DATABASE_URI environment variable is not set",
                file=sys.stderr,
            )
            sys.exit(1)

        u = urlparse(uri)

        # Validate required components (port is optional)
        if not all([u.hostname, u.username, u.path]):
            missing_components = []
            if not u.hostname:
                missing_components.append("hostname")
            if not u.username:
                missing_components.append("username")
            if not u.path:
                missing_components.append("database path")

            error_msg = (
                "ERROR: Missing required components in DATABASE_URI: "
                + ", ".join(missing_components)
            )
            print(error_msg, file=sys.stderr)
            sys.exit(1)

        # Extract components with defaults
        hostname = u.hostname
        port = u.port or get_default_port(u.scheme or "postgresql")
        username = u.username
        db_name = u.path.lstrip("/")

        # Validate database name is not empty after stripping
        if not db_name:
            print(
                "ERROR: Database name cannot be empty in DATABASE_URI",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"{hostname} {port} {username} {db_name}")

    except Exception as e:
        print(f"ERROR: Failed to parse DATABASE_URI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
