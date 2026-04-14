from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qorme.client.client import Client
    from qorme.events import Events
    from qorme.ml.store import MLStore
    from qorme.utils.async_worker import AsyncWorker
    from qorme.utils.traceback import Traceback


class Deps:
    """
    This class exposes dependencies needed by various domains.
    Dependencies are lazily initialized and cached for the lifetime of the Deps instance.
    """

    __slots__ = (
        "config",
        "_events",
        "_ml_store",
        "_traceback",
        "_http_client",
        "_async_worker",
    )

    def __init__(self, config) -> None:
        self.config = config
        self._events: Events | None = None
        self._ml_store: MLStore | None = None
        self._traceback: Traceback | None = None
        self._http_client: Client | None = None
        self._async_worker: AsyncWorker | None = None

    @property
    def events(self) -> "Events":
        if self._events is None:
            from qorme.events import Events

            self._events = Events()
        return self._events

    @property
    def traceback(self) -> "Traceback":
        if self._traceback is None:
            from qorme.utils.traceback import Traceback

            self._traceback = Traceback(self.config.traceback)
        return self._traceback

    @property
    def async_worker(self) -> "AsyncWorker":
        if self._async_worker is None:
            from qorme.utils.async_worker import AsyncWorker

            self._async_worker = AsyncWorker(self.config.async_worker)
        return self._async_worker

    @property
    def http_client(self) -> "Client":
        if self._http_client is None:
            from qorme.client.client import Client as HttpxClient

            self._http_client = HttpxClient(self.config.http_client, self.async_worker)
        return self._http_client

    @property
    def ml_store(self) -> "MLStore":
        if self._ml_store is None:
            from qorme.ml.store import MLStore

            self._ml_store = MLStore(self.config.ml_store, self.http_client)
        return self._ml_store

    def close(self) -> None:
        if self._ml_store is not None:
            self._ml_store.close()
            self._ml_store = None
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None
        if self._async_worker is not None:
            self._async_worker.close()
            self._async_worker = None
        self._events = None
        self._traceback = None
