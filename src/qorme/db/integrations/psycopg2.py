from functools import lru_cache

import psycopg2

from qorme.db.datastructures import DatabaseInfo, DatabaseVendor
from qorme.db.tracking import track_connection
from qorme.domain import Domain

POSTGRESQL_VENDOR = DatabaseVendor.POSTGRESQL


class Psycopg2Tracking(Domain):
    name = "db.psycopg2"

    __slots__ = ()

    def install_wrappers(self):
        self.wrapper.wrap(psycopg2, "connect", self._connect_wrapper)

    def _connect_wrapper(self, wrapped, instance, args, kwargs):
        db_info = DatabaseInfo(POSTGRESQL_VENDOR, "", extract_db_name(args, kwargs))
        proxy = track_connection(wrapped, args, kwargs, self.deps.events, db_info)
        # Update version info after connection is established
        proxy.set_db_version(get_db_version(proxy.__wrapped__))
        return proxy


def get_db_version(conn):
    return format_db_version(getattr(conn, "server_version", None))


@lru_cache
def format_db_version(db_version: int | None) -> str:
    """
    Return server version as a human-readable string.
    psycopg2 exposes ``connection.server_version`` as an *integer* where the layout is
    :: major * 10000 + minor * 100 + patch
    Hence Postgres 15.4 => 150004, 14.11 => 140011.
    We convert that to ``major.minor.patch`` for readability.
    """
    if not db_version:
        return ""
    return f"{db_version // 10000}.{(db_version // 100) % 100}.{db_version % 100}"


def extract_db_name(args, kwargs):
    """Extract database information from psycopg2 connection parameters."""
    # Handle different connection parameter formats
    if args and isinstance(args[0], str):
        # DSN string format: "host=localhost dbname=test user=postgres"
        # db_name = "postgresql"  # Default for DSN
        for part in args[0].split():
            if part.startswith("dbname="):
                return part.split("=", 1)[1]
    # Keyword arguments format
    return kwargs.get("database", kwargs.get("dbname", "postgresql"))
