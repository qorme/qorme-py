"""Tests for MLStore thread safety and state machine."""

import asyncio
import threading
import time
import unittest

import httpx

from qorme.client.client import Client
from qorme.ml.store import MLStore
from qorme.utils.async_worker import AsyncWorker
from qorme.utils.config import Config

from ..mock import MockServer

try:
    import msgspec
except ImportError:
    msgspec = None


# Real config matching defaults.py structure
ML_STORE_CONFIG = Config(
    "ml_store",
    data={},
    defaults={
        "sse": {
            "url_path": "/sse/",
            "max_retries": 3,
            "retry_interval": 0.01,  # Fast retry for tests
            "startup_timeout": 1.0,
            "read_timeout": 0.25,
        },
    },
)

CLIENT_CONFIG = Config(
    "client",
    data={"dsn": "https://key@test.com"},
    defaults={
        "dsn": "",
        "request_timeout": 60.0,
        "shutdown_timeout": 60.0,
        "http2": True,
        "verify_ssl": True,
        "retry": {
            "attempts": 1,
            "backoff_jitter": 0.0,
            "backoff_factor": 0.1,
        },
    },
)

WORKER_CONFIG = Config(
    "async_worker",
    data={
        "startup_timeout": 1.0,
        "shutdown_timeout": 1.0,
    },
    defaults={},
)


class TestMLStore(unittest.TestCase):
    def event_stream(self):
        """SSE stream that sends ml-updates events."""

        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"event: ml.updates\n"
                yield b"id: 1\n"
                yield b"\n"
                # If we return right away, sse will retry so let's just keep it open
                await asyncio.sleep(100.0)

        return Body()

    def _set_up_store(self, event_stream=None, max_retries=3):
        config_data = ML_STORE_CONFIG.defaults.copy()
        config_data["sse"]["max_retries"] = max_retries
        config = Config("ml_store", data={}, defaults=config_data)

        self.mock_server = MockServer(event_stream=event_stream or self.event_stream)
        self.worker = AsyncWorker(WORKER_CONFIG)
        self.client = Client(CLIENT_CONFIG, self.worker, httpx.MockTransport(self.mock_server))
        self.store = MLStore(config, self.client)

    def tearDown(self):
        self.store.close()
        self.client.close()
        self.worker.close()

    def wait_until(self, condition, timeout=1.0):
        start = time.time()
        while time.time() - start < timeout:
            if condition():
                return
            time.sleep(0.005)
        raise TimeoutError("Condition not met within timeout")

    def test_state(self):
        self._set_up_store()
        # State is initially empty
        self.assertEqual(len(self.store._state), 0)

        # ready() returns False before SSE connects.
        self.assertFalse(self.store.connected())

        # First ready() call triggers SSE connection
        self.assertIn("connecting", self.store._state)
        self.assertEqual(len(self.store._state), 1)
        self.assertIsNotNone(self.store._sse_task)

        # Wait for SSE to receive events
        self.wait_until(self.store.connected)
        self.assertEqual(len(self.store._state), 1)

        # Closing marks as dead
        self.store.close()
        self.assertTrue(self.store.dead())
        self.assertFalse(self.store.connected())
        self.assertEqual(len(self.store._state), 1)

    def test_concurrent_ready(self):
        """Multiple threads calling ready() should only start SSE once."""
        self._set_up_store()
        num_threads = 100

        def make_call_ready(b, s):
            def call_ready():
                b.wait()
                s.connected()

            return call_ready

        barrier = threading.Barrier(num_threads)
        threads = [
            threading.Thread(target=make_call_ready(barrier, self.store))
            for _ in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Wait for requests to be processed
        self.wait_until(lambda: len(self.mock_server.requests) > 1)

        # Only thread should perform request to connect to SSE
        # Account for auth request in total count.
        self.assertEqual(len(self.mock_server.requests), 2)

    def test_max_retries_exhausted_leads_to_dead(self):
        """Store should go to dead state after max retries exhausted."""

        def error_stream():
            class Body(httpx.AsyncByteStream):
                async def __aiter__(self):
                    yield b""
                    raise httpx.ReadError("Network error")

            return Body()

        self._set_up_store(error_stream, max_retries=3)

        self.store.connected()  # Trigger start

        self.wait_until(self.store.disconnected)

        # Should eventually die
        self.wait_until(self.store.dead)
        self.assertTrue(self.store.dead())
