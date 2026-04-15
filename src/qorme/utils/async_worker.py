import asyncio
import logging
import threading
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from concurrent.futures import Future

    from qorme.utils.config import Config

logger = logging.getLogger(__name__)


class AsyncWorker:
    """
    An asyncio event loop running in a dedicated background thread.
    This utility starts a private event loop in a daemon thread and exposes two
    convenience operations:

    - `submit(coro)`: schedule a coroutine to run on the background loop and
      return a concurrent.futures.Future that can be waited on from other
      threads.
    - `close()`: stop the background loop and wait for the thread to finish.

    The worker will lazily start the thread when the `loop` property is first
    accessed or when `submit` is called.

    This should be used for I/O, mainly HTTP requests.
    """

    __slots__ = "config", "_loop", "_thread", "_lock", "_running"

    thread_name = "Qorme-AsyncWorker-EventLoopThread"

    def __init__(self, config: "Config") -> None:
        self.config = config
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._running = threading.Event()

    def submit(self, coro: "Coroutine") -> "Future":
        """
        Schedule `coro` to run on the background event loop.

        This is a thin wrapper around `asyncio.run_coroutine_threadsafe` which
        will start the loop thread if it is not already running.

        Args:
            coro: an awaitable/coroutine object.

        Returns:
            concurrent.futures.Future: a future that can be waited on from any
            thread to obtain the coroutine's result or exception.
        """
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop, starting it if necessary."""
        self._ensure_running()
        assert self._loop is not None
        return self._loop

    def is_running(self) -> bool:
        """Return True when the event loop is active and running."""
        return self._running.is_set()

    def _ensure_running(self) -> None:
        """Start the event loop if it's not already running."""
        if self.is_running():
            return

        with self._lock:
            if self.is_running():
                return

            t = threading.Thread(target=self._run, daemon=True, name=self.thread_name)
            try:
                t.start()
            except RuntimeError:
                return
            else:
                self._thread = t

            # Block until the background thread signals readiness or timeout.
            if not self._running.wait(timeout=self.config.startup_timeout):
                logger.warning(
                    "event loop thread still not ready after %d s", self.config.startup_timeout
                )

    def _run(self) -> None:
        """
        Thread target that creates and runs the event loop which runs
        until `loop.close()` is called from another thread via `close()`.
        """
        try:
            # Prefer uvloop where available for improved performance.
            import uvloop
        except ImportError:
            loop = asyncio.new_event_loop()
        else:
            loop = uvloop.new_event_loop()

        # Make the created loop the current loop for this thread.
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._running.set()

        try:
            # Run until close() is called from another thread.
            loop.run_forever()
        except Exception:
            logger.exception("Error running loop in async worker thread", exc_info=True)
        finally:
            self._running.clear()
            # Ensure we attempt an orderly shutdown of the loop and all tasks.
            self._close()
            self._loop = None

    def _close(self) -> None:
        """
        Attempt to cancel pending tasks and shutdown the event loop cleanly.
        This method should be called from the background thread when the loop exits.
        """
        if not (loop := self._loop):
            return

        try:
            _cancel_all_tasks(loop)
            # Shut down async generators and default executor to avoid leaks.
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            logger.exception("Error closing loop", exc_info=True)
        finally:
            loop.close()

    def close(self) -> None:
        """Stop the event loop and wait for the thread to finish."""
        if not self.is_running():
            return

        with self._lock:
            if not self.is_running():
                return
            if loop := self._loop:
                loop.call_soon_threadsafe(loop.stop)
                # Reference will be cleared in _run after loop stops.
            if t := self._thread:
                t.join(timeout=self.config.shutdown_timeout)
                self._thread = None


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """
    Cancel all pending tasks attached to `loop` and wait for them.

    This function will iterate over all tasks returned by
    `asyncio.all_tasks(loop)`, cancel them, and then run until the
    cancellations complete. If any task raised while being awaited, the
    exception is logged for debugging purposes.
    """
    if not (to_cancel := asyncio.all_tasks(loop)):
        return

    # Request cancellation for every task. They should cooperate by handling
    # asyncio.CancelledError and exiting.
    for task in to_cancel:
        task.cancel()

    # Wait for all tasks to finish. We don't reraise exceptions here; instead
    # they are returned in the gather result and examined below.
    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

    # Log any task exceptions that were not cancelled cleanly.
    for task in to_cancel:
        if not task.cancelled() and (exc := task.exception()):
            logger.exception(
                "unhandled exception in task %s during loop shutdown: %s",
                task,
                exc,
            )
