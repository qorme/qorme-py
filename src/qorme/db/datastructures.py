from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import msgspec

from .types import DatabaseVendor

if TYPE_CHECKING:
    from qorme.utils.traceback import TracebackEntry


class TimeInterval(msgspec.Struct):
    start: datetime
    end: datetime | None = None


class DatabaseInfo(msgspec.Struct):
    vendor: DatabaseVendor
    version: str
    name: str = "default"


class ConnectionData(msgspec.Struct):
    uid: UUID
    db: DatabaseInfo
    creation: TimeInterval


class SQLQueryData(msgspec.Struct, omit_defaults=True):
    uid: UUID
    context_uid: UUID
    context_ts: datetime
    connection_uid: UUID
    sql: str
    time: TimeInterval
    traceback: list[TracebackEntry]
    orm_query_uid: UUID | None = None  # ORM query if any.
    orm_query_ts: datetime | None = None  # ORM query timestamp if linked to ORM query.
