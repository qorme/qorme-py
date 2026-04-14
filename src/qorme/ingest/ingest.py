from typing import TYPE_CHECKING

from qorme.domain import Domain
from qorme.ingest.queue import Queue

if TYPE_CHECKING:
    from qorme.context.tracking import QueryContext
    from qorme.db.datastructures import SQLQueryData
    from qorme.db.tracking import ConnectionProxy
    from qorme.orm.tracking import ORMQuery


class Ingest(Domain):
    name = "ingest"

    __slots__ = "_queue"

    def enable(self):
        self._queue: Queue | None = None
        return super().enable()

    def disable(self) -> bool:
        try:
            return super().disable()
        finally:
            if q := self._queue:
                q.close()
                self._queue = None

    @property
    def queue(self) -> Queue:
        if self._queue is None:
            self._queue = Queue(self.config.queue, self.deps)
        return self._queue

    def register_event_handlers(self):
        self.deps.events.register_context_created_handler(self._context_created_handler)
        self.deps.events.register_query_done_handler(self._query_done_handler)
        self.deps.events.register_connection_created_handler(self._connection_created_handler)
        self.deps.events.register_query_executed_handler(self._query_executed_handler)

    def unregister_event_handlers(self):
        self.deps.events.unregister_context_created_handler(self._context_created_handler)
        self.deps.events.unregister_query_done_handler(self._query_done_handler)
        self.deps.events.unregister_connection_created_handler(self._connection_created_handler)
        self.deps.events.unregister_query_executed_handler(self._query_executed_handler)

    def _context_created_handler(self, context: "QueryContext") -> None:
        self.queue.enqueue("contexts", context.data)

    def _query_done_handler(self, tracker: "ORMQuery") -> None:
        self.queue.enqueue("orm_queries", tracker.data)
        for rows in tracker.rows.values():
            self.queue.enqueue_after("rows", rows, delay=self.config.rows_wait_time)

    def _connection_created_handler(self, conn: "ConnectionProxy") -> None:
        self.queue.enqueue("connections", conn._self_data)

    def _query_executed_handler(self, sql_query: "SQLQueryData", *_) -> None:
        self.queue.enqueue("sql_queries", sql_query)
