from functools import lru_cache

import psycopg

from qorme.db.datastructures import DatabaseInfo, DatabaseVendor
from qorme.db.tracking import track_connection
from qorme.domain import Domain

POSTGRESQL_VENDOR = DatabaseVendor.POSTGRESQL


def get_db_version(conn):
    """Return server version as a human-readable string from a psycopg3 connection."""
    return format_db_version(getattr(conn.info, "server_version", None))


@lru_cache
def format_db_version(server_version: int | tuple | None) -> str:
    """Convert ``server_version`` (int or tuple) to ``major.minor[.patch]`` string."""
    if server_version is None:
        return ""

    if isinstance(server_version, tuple):
        major, minor, *rest = server_version + (0, 0)  # pad to at least 2 elems
        patch = rest[0] if rest else 0
    else:
        major = server_version // 10000
        minor = (server_version // 100) % 100
        patch = server_version % 100
    return f"{major}.{minor}.{patch}"


def extract_db_name(args, kwargs):
    """Extract database name from psycopg3 connection parameters."""
    # psycopg3 accepts same params as psycopg2.
    if args and isinstance(args[0], str):
        # DSN string or URL
        dsn = args[0]
        if "dbname=" in dsn:
            for part in dsn.split():
                if part.startswith("dbname="):
                    return part.split("=", 1)[1]
        # URL format
        if "//" in dsn:
            from urllib.parse import urlparse

            path = urlparse(dsn).path
            if path.startswith("/"):
                return path.lstrip("/") or "postgres"
            return path or "postgres"
        return "postgres"

    return kwargs.get("dbname", kwargs.get("database", "postgres"))


class PsycopgTracking(Domain):
    """Tracking domain for psycopg (v3) synchronous connections."""

    name = "db.psycopg"

    __slots__ = ()

    def install_wrappers(self):
        self.wrapper.wrap(psycopg, "connect", self._connect_wrapper)

    def _connect_wrapper(self, wrapped, instance, args, kwargs):
        db_info = DatabaseInfo(POSTGRESQL_VENDOR, "", extract_db_name(args, kwargs))
        proxy = track_connection(wrapped, args, kwargs, self.deps.events, db_info)
        proxy.set_db_version(get_db_version(proxy.__wrapped__))
        return proxy
