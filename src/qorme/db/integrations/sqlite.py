import sqlite3

from qorme.db.datastructures import DatabaseInfo, DatabaseVendor
from qorme.db.tracking import track_connection
from qorme.domain import Domain

SQLITE_VENDOR = DatabaseVendor.SQLITE
SQLITE_VERSION = sqlite3.sqlite_version


class SQLiteTracking(Domain):
    name = "db.sqlite"

    __slots__ = ()

    def install_wrappers(self):
        self.wrapper.wrap(sqlite3, "connect", self._connect_wrapper)

    def _connect_wrapper(self, wrapped, instance, args, kwargs):
        db_name = args[0] if args else kwargs["database"]
        db_info = DatabaseInfo(SQLITE_VENDOR, SQLITE_VERSION, db_name)
        return track_connection(wrapped, args, kwargs, self.deps.events, db_info)
