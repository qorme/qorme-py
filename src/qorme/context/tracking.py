from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING
from uuid import uuid4

from qorme.utils.datetime import utcnow

from .datastructures import ContextData
from .types import ContextType

if TYPE_CHECKING:
    from qorme.deps import Deps

# Keeps track of the current context.
_query_context_var: ContextVar["QueryContext"] = ContextVar("qorme")

# Retrieves the current context.
get_query_context = _query_context_var.get


class QueryContextLookupError(LookupError): ...


class QueryContext:
    __slots__ = "data", "deps", "_state", "_token_var"

    def __init__(
        self,
        name: str,
        deps: "Deps",
        type: ContextType = ContextType.UNDEFINED,
        **data: str,
    ):
        self.data = ContextData(uuid4(), name, type, utcnow(), data)
        self.deps = deps
        self._state = {}

    def __enter__(self) -> "QueryContext":
        """Enter the context and set it as the current context."""
        if parent_ctx := get_query_context(None):
            self.data.parent_ts = parent_ctx.data.timestamp
            self.data.parent_uid = parent_ctx.data.uid
        self.deps.events.on_context_created(self)
        self._token_var = _query_context_var.set(self)
        return self

    def __exit__(self, *exception) -> None:
        """Exit the context and restore the previous context."""
        _query_context_var.reset(self._token_var)

    @contextmanager
    def state(self, **kwargs):
        self._state.update(kwargs)
        try:
            yield
        finally:
            for k in kwargs:
                self._state.pop(k)

    def get_state(self, key):
        return self._state.get(key)
