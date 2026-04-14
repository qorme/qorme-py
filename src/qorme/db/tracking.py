from contextlib import contextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

import wrapt

from qorme.context.tracking import get_query_context
from qorme.orm.tracking import get_orm_query
from qorme.utils.datetime import utcnow

from .datastructures import ConnectionData, SQLQueryData, TimeInterval

if TYPE_CHECKING:
    from qorme.events import Events


@contextmanager
def record_interval():
    """Context manager that records a time interval."""
    interval = TimeInterval(start=utcnow())
    try:
        yield interval
    finally:
        interval.end = utcnow()


def track_connection(wrapped, args, kwargs, events, db_info):
    with record_interval() as creation:
        connection = wrapped(*args, **kwargs)

    data = ConnectionData(uuid4(), db_info, creation)
    proxy = ConnectionProxy(connection, data, events)
    events.on_connection_created(proxy)
    return proxy


class ConnectionProxy(wrapt.ObjectProxy):
    def __init__(self, connection, data: "ConnectionData", events: "Events"):
        super().__init__(connection)
        self._self_data = data
        self._self_events = events

    def set_db_version(self, version: str):
        self._self_data.db.version = version

    def cursor(self, *args, **kwargs):
        cursor = self.__wrapped__.cursor(*args, **kwargs)
        return CursorProxy(cursor, self._self_data.uid, self._self_events)


class CursorProxy(wrapt.ObjectProxy):
    def __init__(self, cursor, conn_uid, events):
        super().__init__(cursor)
        self._self_conn_uid = conn_uid
        self._self_events = events
        self._self_query_uid = None
        self._self_query_start_time = None
        self._self_fetch_in_progress = False

    def execute(self, *args, **kwargs):
        return self.record_query_execution(self.__wrapped__.execute, args, kwargs)

    def executemany(self, *args, **kwargs):
        return self.record_query_execution(self.__wrapped__.executemany, args, kwargs)

    def record_query_execution(self, execute, args, kwargs):
        self._fetch_done()
        if not (context := get_query_context(None)):
            return execute(*args, **kwargs)

        with record_interval() as time:
            result = execute(*args, **kwargs)

        traceback = None
        orm_query_uid = None
        orm_query_ts = None
        if orm_query := get_orm_query(None):
            traceback = orm_query.data.traceback
            orm_query_uid = orm_query.data.uid
            orm_query_ts = orm_query.data.timestamp
        else:
            traceback = context.deps.traceback.get_stack()

        query = SQLQueryData(
            uuid4(),
            context.data.uid,
            context.data.timestamp,
            self._self_conn_uid,
            args[0],
            time,
            traceback,
            orm_query_uid,
            orm_query_ts,
        )
        params = args[1] if len(args) > 1 else kwargs.get("parameters")
        self._self_events.on_query_executed(query, params)
        self._self_query_uid = query.uid
        self._self_query_start_time = query.time.start
        return result

    def _fetch_started(self):
        if self._self_fetch_in_progress:
            return
        self._self_events.on_fetch_started(self)
        self._self_fetch_in_progress = True

    def _fetch_done(self):
        if not self._self_fetch_in_progress:
            return
        self._self_events.on_fetch_done(self)
        self._self_fetch_in_progress = False
        self._self_query_uid = None
        self._self_query_start_time = None

    def fetchone(self):
        self._fetch_started()
        ret = self.__wrapped__.fetchone()
        if ret is None:
            self._fetch_done()
        return ret

    def fetchmany(self, *args, **kwargs):
        self._fetch_started()
        ret = self.__wrapped__.fetchmany(*args, **kwargs)
        if not ret:
            self._fetch_done()
        return ret

    def fetchall(self):
        self._fetch_started()
        ret = self.__wrapped__.fetchall()
        self._fetch_done()
        return ret

    def close(self):
        ret = self.__wrapped__.close()
        self._fetch_done()
        return ret
