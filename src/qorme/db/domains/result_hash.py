from typing import TYPE_CHECKING

from qorme.db.datastructures import SQLResultHash
from qorme.domain import Domain
from qorme.utils.hash import Hasher

if TYPE_CHECKING:
    from qorme.db.tracking import CursorProxy


class ResultHash(Domain):
    # Only works with sqlite3 and psycopg drivers for now.
    name = "db.result_hash"

    __slots__ = "_row_factory"

    def setup(self):
        self._row_factory = _get_row_factory(self.config.driver)

    def register_event_handlers(self):
        self.deps.events.register_fetch_started_handler(self._fetch_started_handler)
        self.deps.events.register_fetch_done_handler(self._fetch_done_handler)

    def unregister_event_handlers(self):
        self.deps.events.unregister_fetch_started_handler(self._fetch_started_handler)
        self.deps.events.unregister_fetch_done_handler(self._fetch_done_handler)

    def _fetch_started_handler(self, cursor: "CursorProxy"):
        cursor._self_row_factory = cursor.row_factory
        cursor.row_factory = self._row_factory(cursor.row_factory)

    def _fetch_done_handler(self, cursor: "CursorProxy"):
        row_factory, cursor.row_factory = cursor.row_factory, cursor._self_row_factory
        result_hash = SQLResultHash(
            cursor._self_query_start_time, cursor._self_query_uid, row_factory.digest()
        )
        self.deps.events.on_sql_result_hash_computed(result_hash)


class SqliteRowHasherFactory:
    __slots__ = "_hasher", "_factory"

    def __init__(self, factory):
        self._hasher = Hasher()
        self._factory = factory if factory else self.noop_factory

    def __call__(self, cursor, row):
        self._hasher.update(row)
        return self._factory(cursor, row)

    def digest(self):
        return self._hasher.digest()

    def noop_factory(self, _, row):
        return row


class PsycopgRowHasherFactory:
    __slots__ = "_hasher", "_factory"

    def __init__(self, factory):
        self._hasher = Hasher()
        self._factory = factory

    def __call__(self, cursor):
        return PsycopgRowHasher(self._hasher, self._factory(cursor) if self._factory else None)

    def digest(self):
        return self._hasher.digest()


class PsycopgRowHasher:
    __slots__ = "_hasher", "_factory"

    def __init__(self, hasher, factory):
        self._hasher = hasher
        self._factory = factory if factory else self.noop_factory

    def __call__(self, row):
        self._hasher.update(row)
        return self._factory(row)

    def noop_factory(self, row):
        return row


def _get_row_factory(driver):
    match driver:
        case "psycopg":
            return PsycopgRowHasherFactory
        case "sqlite":
            return SqliteRowHasherFactory
        case _:
            raise ValueError(f"Unsupported driver for result hash: {driver}")
