from contextvars import ContextVar
from typing import Generic, TypeVar
from uuid import uuid4
from weakref import ref as weaf_reference

from qorme.context.tracking import QueryContextLookupError, get_query_context
from qorme.utils.bitset import BitSet
from qorme.utils.datetime import microseconds_since, utcnow

from .datastructures import ORMQueryData, Rows
from .types import QueryType, RowType

# Generic query type.
Q = TypeVar("Q")

# Keeps track of the current ORM query being executed.
_orm_query_var: ContextVar["ORMQuery"] = ContextVar("orm-query")

# Retrieves the current ORM query.
get_orm_query = _orm_query_var.get


class ORMQuery(Generic[Q]):
    __slots__ = "rows", "data", "context", "_query", "_token_var", "__weakref__"

    def __init__(self, query: Q, model: str, row_type: RowType, query_type: QueryType):
        if not (context := get_query_context(None)):
            raise QueryContextLookupError

        self.query = query
        self.context = context
        self.rows: dict[str, Rows] = {}
        self.data = ORMQueryData(
            utcnow(),
            uuid4(),
            context.data.timestamp,
            context.data.uid,
            model,
            row_type,
            query_type,
            context.deps.traceback.get_stack(),
        )

    @property
    def query(self) -> Q | None:
        """
        Returns the query this tracker is attached to.
        Since we are only storing a weak reference to the query,
        this return None when the query is finalized.
        """
        return self._query()

    @query.setter
    def query(self, query: Q) -> None:
        """
        Sets the query this tracker is attached to.
        Store a weak reference to the query to prevent leaks.
        """
        self._query = weaf_reference(query)

    def get_rows(
        self, instance, path, select_related, get_columns_loaded, get_columns_required
    ) -> Rows:
        if path not in self.rows:
            self.rows[path] = Rows(
                self.data.timestamp,
                self.data.uid,
                path,
                instance._meta.label,
                0,
                get_columns_loaded(instance, select_related),
                get_columns_required(instance, select_related),
                BitSet(),
            )
        return self.rows[path]

    def __enter__(self) -> "ORMQuery[Q]":
        """Enters the query, setting it as the current query."""
        self._token_var = _orm_query_var.set(self)
        self.context.deps.events.on_query_started(self)
        # Fire separate optimization event to make sure all
        # data from `query_started` event handlers is available
        # like template info...
        self.context.deps.events.on_optimization_request(self)
        return self

    def __exit__(self, *exception) -> None:
        """Exits the query, resetting the current query."""
        self.data.duration = microseconds_since(self.data.timestamp)
        self.context.deps.events.on_query_done(self)
        _orm_query_var.reset(self._token_var)
