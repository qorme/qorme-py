from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import msgspec

from qorme.utils.bitset import BitSet

from .types import QueryType, RowType

if TYPE_CHECKING:
    from qorme.ml.datastructures import MLPrediction
    from qorme.utils.traceback import TracebackEntry


# An ORM 'read' query e.g User.objects.filter(name='John')
class ORMQueryData(msgspec.Struct, omit_defaults=True):
    timestamp: datetime
    uid: UUID
    context_ts: datetime
    context_uid: UUID
    model: str
    row_type: RowType
    query_type: QueryType
    traceback: list[TracebackEntry]
    duration: int = 0
    template: TracebackEntry | None = None
    relation: Relation | None = None
    # ML predictions by ML category
    ml_predictions: dict[str, list[MLPrediction]] = {}


class Relation(msgspec.Struct, omit_defaults=True):
    from_model: str
    from_field: str
    # Indicates whether the associated query results from accessing a deferred field.
    from_deferred: bool
    path: str
    depth: int
    from_query_ts: datetime | None = None
    from_query_uid: UUID | None = None


class Rows(msgspec.Struct):
    timestamp: datetime
    query_uid: UUID
    path: str
    model: str
    count: int
    # Columns that were loaded in the query
    columns_loaded: BitSet
    # Columns that we can't defer (e.g. primary key or fk in Joins in Django)
    columns_required: BitSet
    # Columns that were actually accessed
    columns_accessed: BitSet
