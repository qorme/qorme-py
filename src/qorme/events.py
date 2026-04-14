"""A centralized event handling system that manages event handlers for different event types."""

import enum
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    EventHandler = Callable[..., Any]
    EventItem = Any


logger = logging.getLogger(__name__)


class EventType(enum.Enum):
    """Type of events."""

    CONTEXT_CREATED = "CONTEXT_CREATED"
    TRACK_MODEL = "TRACK_MODEL"
    QUERY_STARTED = "QUERY_STARTED"
    OPTIMIZATION_REQUEST = "OPTIMIZATION_REQUEST"
    QUERY_DONE = "QUERY_DONE"
    NEW_INSTANCE = "NEW_INSTANCE"
    CONNECTION_CREATED = "CONNECTION_CREATED"
    QUERY_EXECUTED = "QUERY_EXECUTED"
    FETCH_STARTED = "FETCH_STARTED"
    FETCH_DONE = "FETCH_DONE"
    QUEUE_FLUSH = "QUEUE_FLUSH"
    PROCESS_PAYLOAD = "PROCESS_PAYLOAD"


class Events:
    """
    This class provides methods to register, unregister, and execute event handlers for
    predefined event types.
    Event handlers are executed in a random order when an event is triggered.
    """

    __slots__ = "_handlers"

    def __init__(self) -> None:
        self._handlers: dict[EventType, set[EventHandler]] = defaultdict(set)

    def _register_event_handler(self, event: EventType, handler: "EventHandler") -> None:
        """
        Register a handler function for a specific event type.

        Args:
            event: The event type to register the handler for
            handler: The handler function to be called when the event occurs
        """
        self._handlers[event].add(handler)

    def _unregister_event_handler(self, event: EventType, handler: "EventHandler") -> None:
        """
        Unregister a handler function from a specific event type.

        Args:
            event: The event type to unregister the handler from
            handler: The handler function to be removed
        """
        self._handlers[event].discard(handler)

    def fire(self, event: EventType, *args) -> None:
        """
        Execute all registered handlers for a specific event.
        Handlers aren't guaranteed to be executed in the order they were registered.
        If a handler raises an exception, it is logged but doesn't stop
        other handlers from executing.

        Args:
            event: The event that occurred
            args: Relevant args to pass to the handlers
        """
        for handler in self._handlers[event]:
            try:
                handler(*args)
            except Exception:
                logger.exception(
                    "Error in %s handler during %s, args=%s", handler, event, args, exc_info=True
                )

    # Context Created
    def register_context_created_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.CONTEXT_CREATED, handler)

    def unregister_context_created_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.CONTEXT_CREATED, handler)

    def on_context_created(self, *item: "EventItem") -> None:
        self.fire(EventType.CONTEXT_CREATED, *item)

    # Track Model
    def register_track_model_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.TRACK_MODEL, handler)

    def unregister_track_model_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.TRACK_MODEL, handler)

    def on_track_model(self, *item: "EventItem") -> None:
        self.fire(EventType.TRACK_MODEL, *item)

    # Query Started
    def register_query_started_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.QUERY_STARTED, handler)

    def unregister_query_started_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.QUERY_STARTED, handler)

    def on_query_started(self, *item: "EventItem") -> None:
        self.fire(EventType.QUERY_STARTED, *item)

    # Optimization Request
    def register_optimization_request_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.OPTIMIZATION_REQUEST, handler)

    def unregister_optimization_request_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.OPTIMIZATION_REQUEST, handler)

    def on_optimization_request(self, *item: "EventItem") -> None:
        self.fire(EventType.OPTIMIZATION_REQUEST, *item)

    # Query Done
    def register_query_done_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.QUERY_DONE, handler)

    def unregister_query_done_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.QUERY_DONE, handler)

    def on_query_done(self, *item: "EventItem") -> None:
        self.fire(EventType.QUERY_DONE, *item)

    # New Instance
    def register_new_instance_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.NEW_INSTANCE, handler)

    def unregister_new_instance_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.NEW_INSTANCE, handler)

    def on_new_instance(self, *item: "EventItem") -> None:
        self.fire(EventType.NEW_INSTANCE, *item)

    # Connection Created
    def register_connection_created_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.CONNECTION_CREATED, handler)

    def unregister_connection_created_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.CONNECTION_CREATED, handler)

    def on_connection_created(self, *item: "EventItem") -> None:
        self.fire(EventType.CONNECTION_CREATED, *item)

    # Query Executed
    def register_query_executed_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.QUERY_EXECUTED, handler)

    def unregister_query_executed_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.QUERY_EXECUTED, handler)

    def on_query_executed(self, *item: "EventItem") -> None:
        self.fire(EventType.QUERY_EXECUTED, *item)

    # Fetch Started
    def register_fetch_started_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.FETCH_STARTED, handler)

    def unregister_fetch_started_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.FETCH_STARTED, handler)

    def on_fetch_started(self, *item: "EventItem") -> None:
        self.fire(EventType.FETCH_STARTED, *item)

    # Fetch Done
    def register_fetch_done_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.FETCH_DONE, handler)

    def unregister_fetch_done_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.FETCH_DONE, handler)

    def on_fetch_done(self, *item: "EventItem") -> None:
        self.fire(EventType.FETCH_DONE, *item)

    # Queue Flush
    def register_queue_flush_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.QUEUE_FLUSH, handler)

    def unregister_queue_flush_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.QUEUE_FLUSH, handler)

    def on_queue_flush(self, *item: "EventItem") -> None:
        self.fire(EventType.QUEUE_FLUSH, *item)

    # Process Payload
    def register_process_payload_handler(self, handler: "EventHandler") -> None:
        self._register_event_handler(EventType.PROCESS_PAYLOAD, handler)

    def unregister_process_payload_handler(self, handler: "EventHandler") -> None:
        self._unregister_event_handler(EventType.PROCESS_PAYLOAD, handler)

    def on_process_payload(self, *item: "EventItem") -> None:
        self.fire(EventType.PROCESS_PAYLOAD, *item)
