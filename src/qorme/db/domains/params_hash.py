from __future__ import annotations

from typing import TYPE_CHECKING

from qorme.domain import Domain
from qorme.utils.hash import Hasher

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qorme.db.datastructures import SQLQueryData


class ParamsHash(Domain):
    name = "db.params_hash"

    __slots__ = ()

    def register_event_handlers(self):
        self.deps.events.register_sql_query_started_handler(self._sql_query_started_handler)

    def unregister_event_handlers(self):
        self.deps.events.unregister_sql_query_started_handler(self._sql_query_started_handler)

    def _sql_query_started_handler(self, query_data: SQLQueryData, params: dict | Sequence | None):
        if not query_data.is_select():
            return

        params_iter = params
        if params_iter is None:
            params_iter = ()
        elif isinstance(params_iter, dict):
            params_iter = params_iter.values()

        hasher = Hasher()
        for param in params_iter:
            hasher.update(param)

        query_data.params_hash = hasher.digest()
