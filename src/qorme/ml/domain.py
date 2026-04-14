from typing import TYPE_CHECKING, ClassVar

from qorme.domain import Domain

if TYPE_CHECKING:
    from qorme.orm.tracking import ORMQuery


class MLDomain(Domain):
    ml_category: ClassVar[str]

    __slots__ = ()

    def setup(self) -> None:
        self.deps.ml_store.register(self.ml_category)

    def register_event_handlers(self) -> None:
        self.deps.events.register_optimization_request_handler(self._optimization_request_handler)

    def unregister_event_handlers(self) -> None:
        self.deps.events.unregister_optimization_request_handler(self._optimization_request_handler)

    def _optimization_request_handler(self, query_tracker: "ORMQuery") -> None:
        if self.deps.ml_store.connected():
            return self.optimize(query_tracker)

    def optimize(self, query_tracker: "ORMQuery") -> None: ...

    def get_model(self, name: str):
        # This must be called after ensuring ml store is connected.
        return self.deps.ml_store.get_model(self.ml_category, name)
