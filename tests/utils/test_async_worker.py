import asyncio
import threading
import unittest

from qorme.utils.async_worker import AsyncWorker
from qorme.utils.config import Config


class Task:
    """
    Small helper for tests: an async task that sets events on success/cleanup.

    The `.run()` coroutine sleeps for `duration` seconds, sets `_ok` on
    successful completion, and always sets `_cleanup` in a finally block so
    tests can verify the coroutine was given a chance to clean up after
    cancellation.
    """

    def __init__(self, duration):
        self.duration = duration
        self._ok = threading.Event()
        self._cleanup = threading.Event()

    async def run(self):
        try:
            await asyncio.sleep(self.duration)
            self._ok.set()
        finally:
            # Always mark cleanup so tests can detect cancelled tasks ran
            # their finally blocks.
            self._cleanup.set()

    def wait(self, timeout=None):
        """Wait for the task to signal completion; return True if signalled."""
        return self._ok.wait(timeout or self.duration * 2)

    def ok(self):
        return self._ok.is_set()

    def cleaned_up(self):
        return self._cleanup.is_set()


class TestAsyncWorker(unittest.TestCase):
    def setUp(self):
        self.worker = AsyncWorker(
            config=Config(
                "test-async-worker",
                data={"startup_timeout": 0.1, "shutdown_timeout": 1.0},
                defaults={},
            )
        )

    def tearDown(self):
        # Ensure worker is stopped even if a test fails/hangs.
        self.worker.close()

    def test_fast_and_slow_task_shutdown(self):
        """Fast task completes; slow task is cancelled but cleaned up."""
        slow_task = Task(1.0)
        fast_task = Task(0.005)

        self.assertFalse(self.worker.is_running())

        fut_slow = self.worker.submit(slow_task.run())
        fut_fast = self.worker.submit(fast_task.run())

        self.assertTrue(self.worker.is_running())

        # Wait for fast task to finish
        self.assertTrue(fast_task.wait())

        # Stop the worker and ensure it's no longer running.
        self.worker.close()
        self.assertFalse(self.worker.is_running())

        self.assertTrue(fut_fast.done())
        self.assertFalse(fut_fast.cancelled())
        self.assertIsNone(fut_fast.exception())

        # Slow future should be cancelled
        self.assertTrue(fut_slow.done())
        self.assertTrue(fut_slow.cancelled())

        # The fast task should have completed, the slow task should not.
        self.assertTrue(fast_task.ok())
        self.assertFalse(slow_task.ok())

        # Both tasks should have run their cleanup/finally blocks.
        self.assertTrue(fast_task.cleaned_up())
        self.assertTrue(slow_task.cleaned_up())

    def test_concurrent(self):
        runs = 50
        tasks = [Task(0.01) for _ in range(runs)]
        barrier = threading.Barrier(runs)

        # Submit tasks concurrently from multiple threads.
        def submit_task(t):
            task = t.run()
            barrier.wait()
            return self.worker.submit(task)

        threads = []
        results = []

        for t in tasks:
            th = threading.Thread(
                target=lambda q, arg: q.append(submit_task(arg)), args=(results, t)
            )
            threads.append(th)
            th.start()

        for th in threads:
            th.join()

        # All futures are in results; wait for tasks to finish.
        for fut in results:
            fut.result(timeout=1.0)

        # All task cleanup should have run.
        for t in tasks:
            self.assertTrue(t.cleaned_up())

        # Count threads matching the worker's name pattern to detect if
        # multiple background threads were created due to a race condition.
        worker_threads = [
            t for t in threading.enumerate() if t.name.startswith("Qorme-AsyncWorker-")
        ]
        self.assertEqual(
            len(worker_threads), 1, f"Expected exactly 1 worker thread, found {len(worker_threads)}"
        )
