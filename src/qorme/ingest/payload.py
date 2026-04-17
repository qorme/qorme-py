from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from qorme.context.datastructures import ContextData
    from qorme.db.datastructures import ConnectionData, SQLQueryData
    from qorme.orm.datastructures import ORMQueryData, Rows


class Payload(msgspec.Struct, omit_defaults=True):
    """Payload structure sent to the Qorme server."""

    contexts: list[ContextData] = []
    orm_queries: list[ORMQueryData] = []
    rows: list[Rows] = []
    connections: list[ConnectionData] = []
    sql_queries: list[SQLQueryData] = []
    idx_to_columns: dict[str, list[str]] = {}
