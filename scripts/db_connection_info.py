import os
import sys
from urllib.parse import urlparse

try:
    uri = os.environ.get("DATABASE_URI", "")
    if not uri:
        raise SystemExit("ERROR: DATABASE_URI environment variable is not set")

    u = urlparse(uri)

    if not all([u.hostname, u.port, u.username, u.path]):
        raise SystemExit("ERROR: Incomplete DATABASE_URI environment variable")

    db_name = u.path.lstrip("/")
    username = u.username

    print(f"{u.hostname} {u.port} {username} {db_name}")
except Exception as e:
    print(f"Error parsing DATABASE_URI: {e}", file=sys.stderr)
    sys.exit(1)
