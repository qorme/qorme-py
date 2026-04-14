from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

import msgspec

from qorme.ml.datastructures import MLModel, MLModelsUpdate

if TYPE_CHECKING:
    from concurrent.futures import Future

logger = logging.getLogger(__name__)


_DEAD_STATE = {"dead": True}
_CONNECTED_STATE = {"connected": True}
_DISCONNECTED_STATE = {"disconnected": True}


class MLStore:
    """
    Thread-safe store for ML models received via SSE.

    State Machine:
    --------------
    {} (unitialized)
    -> {connecting: owner}
    -> _CONNECTED_STATE <-> _DISCONNECTED_STATE
    -> _DEAD_STATE
    """

    __slots__ = "config", "_client", "_state", "_models", "_last_event_id", "_sse_task", "_decoder"

    def __init__(self, config, http_client):
        self.config = config
        self._client = http_client
        self._state: dict = {}
        self._models: dict[str, CategoryModels] = {}
        self._last_event_id = ""
        self._sse_task: Future | None = None
        self._decoder = msgspec.msgpack.Decoder(MLModelsUpdate)

    def get_last_event_id(self) -> str:
        """Return the last processed SSE event ID for resumption."""
        return self._last_event_id

    # SSE lifecycle callbacks
    def on_sse_connect(self):
        """Called by SSE client when connection is established."""
        self._mark_connected()

    def on_sse_disconnect(self):
        """Called by SSE client on temporary disconnect (will retry)."""
        self._mark_disconnected()

    def on_sse_exit(self):
        """Called by SSE client when retries exhausted or cancelled."""
        self._mark_dead()

    def _mark_connecting(self) -> bool:
        """
        Atomically claim the connecting state.

        Uses dict.setdefault() for lock-free synchronization:
        - If _state is non-empty, another thread already won
        - Creates unique owner object and attempts atomic insert
        - Only returns True for the thread whose owner was stored

        Returns:
            True if this call successfully claimed the connecting state
        """
        if self._state:
            return False  # Already initialized by another thread
        # Atomic check-and-claim: only one thread's owner will be stored
        owner = object()
        return self._state.setdefault("connecting", owner) is owner

    def _mark_connected(self) -> bool:
        """Transition to connected state. Returns True if state changed."""
        if self._state is _CONNECTED_STATE:
            return False
        self._state = _CONNECTED_STATE
        return True

    def _mark_disconnected(self) -> bool:
        """Transition to disconnected state. Returns True if state changed."""
        if self._state is _DISCONNECTED_STATE:
            return False
        self._state = _DISCONNECTED_STATE
        return True

    def _mark_dead(self) -> bool:
        """Transition to dead state (terminal). Returns True if state changed."""
        if self._state is _DEAD_STATE:
            return False
        self._state = _DEAD_STATE
        self._sse_task = None
        logger.info("ML store marked dead")
        return True

    def connected(self, autostart: bool = True) -> bool:
        """
        Check if store is connected to SSE.

        Args:
            autostart: If True and not connected, trigger SSE connection

        Returns:
            True if currently connected
        """
        if self._state is _CONNECTED_STATE:
            return True
        if autostart:
            self._maybe_start()
        return False

    def disconnected(self):
        """Check if store is in disconnected state (temporary, will retry)."""
        return self._state is _DISCONNECTED_STATE

    def dead(self):
        """Check if store is dead (terminal state, won't reconnect)."""
        return self._state is _DEAD_STATE

    def _maybe_start(self):
        """Start SSE connection if not already started."""
        if not self._mark_connecting():
            logger.debug("sse connection already initated")
            return

        self._sse_task = self._client.sse(
            path=self.config.sse.url_path,
            handler=self,
            max_retries=self.config.sse.max_retries,
            retry_interval=self.config.sse.retry_interval,
            timeout=self.config.sse.read_timeout,
        )

    async def on_event(self, event):
        """Process incoming SSE event."""
        # TODO: Move updates to dedicated queue if they block
        # async worker due to heavy CPU work.
        assert event.event == "ml.updates"
        logger.debug(f"Received ML update event: {event.id}, data size: {len(event.data)} bytes")
        if event.data:
            data = base64.b64decode(event.data)
            self.update_models(data)
        self._last_event_id = event.id

    def close(self):
        """Close the store and cancel SSE connection."""
        if task := self._sse_task:
            task.cancel()
        self._mark_dead()

    def register(self, ml_category: str) -> None:
        """Register a category for receiving model updates."""
        if ml_category not in self._models:
            self._models[ml_category] = CategoryModels()

    def get_model(self, category, name) -> MLModel | None:
        """Get a model by category and name."""
        if cm := self._models.get(category):
            return cm.get_model(name)

    def update_models(self, data: bytes):
        """Process model updates from SSE message."""
        update = self._decoder.decode(data)
        for category, models in update.models.items():
            if cm := self._models.get(category):
                cm.update_models(models)


class CategoryModels:
    """
    Container for ML models within a category.

    Thread Safety:
    --------------
    Uses immutable replacement pattern for updates:
    - `get_model()` returns a reference to the current model (safe to read)
    - `update_models()` builds a new samples dict, then swaps atomically
    - Readers see either old or new state, never a partial update
    """

    __slots__ = ("models",)

    def __init__(self):
        self.models: dict[str, MLModel] = {}

    def get_model(self, name) -> MLModel | None:
        """Get model by name. Returns None if not found."""
        return self.models.get(name)

    def update_models(self, models: list[MLModel]):
        """
        Apply model updates using immutable replacement pattern.

        For each incoming model:
        1. New model: Add only if it has stable samples
        2. Existing model: Skip if update is stale (out-of-order)
        3. Updated model: Build new samples dict, then atomic swap

        Handles out-of-order delivery by comparing timestamps at both
        model and sample level.
        """
        for model in models:
            if not (prev_model := self.get_model(model.name)):
                # New model: only add if has stable samples
                samples = {s.hash_value: s for s in model.sample_updates if s.stable}
                if samples:
                    model.samples = samples
                    self.models[model.name] = model
                continue

            # Skip stale updates (out-of-order delivery protection)
            if prev_model.updated_at >= model.updated_at:
                continue

            # Build merged samples
            if prev_model.configuration != model.configuration:
                new_samples = {}  # Config changed: start fresh
            else:
                new_samples = dict(prev_model.samples)  # Copy existing

            # Apply sample updates
            for sample in model.sample_updates:
                existing = new_samples.get(sample.hash_value)
                if existing and existing.updated_at >= sample.updated_at:
                    continue  # Our copy is newer, skip this update
                if sample.stable:
                    new_samples[sample.hash_value] = sample
                else:
                    new_samples.pop(sample.hash_value, None)

            # Atomic swap: readers see old or new, never partial
            if not new_samples:
                self.models.pop(model.name, None)
            else:
                model.samples = new_samples
                self.models[model.name] = model
