"""Tests for the ingest Queue and Flusher."""

import gzip
import time
import unittest
from unittest.mock import Mock

import httpx
import msgspec

from qorme.client.client import Client
from qorme.ingest.payload import Payload
from qorme.ingest.queue import Flusher, Queue
from qorme.utils.async_worker import AsyncWorker
from qorme.utils.config import Config

from ..mock import MockServer

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def make_queue_config(overrides=None):
    """Create test configuration with fast defaults for Queue + Flusher."""
    data = {}
    if overrides:
        data.update(overrides)

    defaults = {
        "join_timeout": 1.0,
        "request_timeout": 10.0,
        "queue_max_size": 100,
        "pqueue_max_size": 50,
        "batch_min_size": 3,
        "batch_max_size": 10,
        "flush_max_interval": 0.5,
        "flusher": {
            "url_path": "ingest/",
            "enc_buffer_size": 64 * 1024,
            "compress_level": 1,
            "request_timeout": 60.0,
        },
    }
    return Config(name="queue", data=data, defaults=defaults)


def make_deps_config():
    """Create Deps-level config for integration tests."""
    return Config(
        name="deps",
        data={"dsn": "https://key@test.com"},
        defaults={
            "dsn": "",
            "http2": False,
            "verify_ssl": False,
            "request_timeout": 60.0,
            "shutdown_timeout": 5.0,
            "retry": {"attempts": 1, "backoff_jitter": 0, "backoff_factor": 0},
        },
    )


WORKER_CONFIG = Config(
    "async_worker", data={}, defaults={"startup_timeout": 3.0, "shutdown_timeout": 5.0}
)


# ---------------------------------------------------------------------------
# Queue unit tests — mock the Flusher so we only test queue mechanics
# ---------------------------------------------------------------------------


class TestQueue(unittest.TestCase):
    """Test Queue public API: enqueue, backpressure, lifecycle."""

    def setUp(self):
        self.config = make_queue_config()
        # We need a minimal deps for Queue init (Queue passes it to Flusher)
        # but we'll patch flusher.flush so deps is never actually used.
        self.deps = Mock(spec_set=["events", "http_client"])

    def _make_queue(self, config=None):
        q = Queue(config or self.config, self.deps)
        q.flusher = Mock(spec_set=["flush"])
        return q

    def test_enqueue_starts_background_thread(self):
        """First enqueue starts the background processing thread."""
        q = self._make_queue()
        self.assertFalse(q.is_running)

        q.enqueue("contexts", {"uid": "1"})
        # Thread should be started now
        self.assertTrue(q.is_running)

        q.close()
        self.assertFalse(q.is_running)

    def test_enqueue_triggers_flush_at_batch_min_size(self):
        """Enqueuing batch_min_size items triggers a flush."""
        q = self._make_queue()

        for i in range(q.batch_min_size + 1):
            q.enqueue("contexts", {"uid": str(i)})

        q.close()

        # Flusher should have been called with a Payload
        self.assertTrue(q.flusher.flush.called)
        payload = q.flusher.flush.call_args[0][0]
        self.assertIsInstance(payload, Payload)
        self.assertGreater(len(payload.contexts), 0)

    def test_close_flushes_remaining_items(self):
        """Closing the queue flushes any remaining items."""
        q = self._make_queue()

        # Enqueue fewer than batch_min_size — won't trigger auto flush
        q.enqueue("contexts", {"uid": "1"})

        # Close triggers final flush_all
        q.close()

        self.assertTrue(q.flusher.flush.called)
        payload = q.flusher.flush.call_args[0][0]
        self.assertEqual(len(payload.contexts), 1)

    def test_enqueue_returns_false_when_full(self):
        """Enqueue returns False when queue is at capacity."""
        small_config = make_queue_config(
            {
                "queue_max_size": 2,
                "pqueue_max_size": 2,
                # Large batch_min so nothing auto-flushes during the test
                "batch_min_size": 100,
                "batch_max_size": 200,
            }
        )
        q = self._make_queue(small_config)

        self.assertTrue(q.enqueue("contexts", {"uid": "1"}))
        self.assertTrue(q.enqueue("contexts", {"uid": "2"}))

        with self.assertLogs(level="WARNING"):
            self.assertFalse(q.enqueue("contexts", {"uid": "3"}))

        q.close()

    def test_enqueue_after_delays_items(self):
        """enqueue_after items with zero delay are flushed on close."""
        q = self._make_queue()

        # Zero delay — ready immediately but sits in pqueue until next flush cycle
        q.enqueue_after("contexts", {"uid": "delayed"}, delay=0)

        # Also enqueue an immediate item
        q.enqueue("sql_queries", {"uid": "imm"})

        q.close()

        # Both should appear across flush calls
        all_contexts = []
        all_sql = []
        for call in q.flusher.flush.call_args_list:
            payload = call[0][0]
            all_contexts.extend(payload.contexts)
            all_sql.extend(payload.sql_queries)

        self.assertTrue(any(c.get("uid") == "delayed" for c in all_contexts if isinstance(c, dict)))
        self.assertTrue(any(c.get("uid") == "imm" for c in all_sql if isinstance(c, dict)))

    def test_multiple_data_types_in_single_payload(self):
        """Items of different types enqueued together appear in the same Payload."""
        q = self._make_queue()

        q.enqueue("contexts", {"uid": "ctx1"})
        q.enqueue("sql_queries", {"uid": "q1"})
        q.enqueue("connections", {"uid": "c1"})

        q.close()

        self.assertTrue(q.flusher.flush.called)
        payload = q.flusher.flush.call_args[0][0]
        self.assertEqual(len(payload.contexts), 1)
        self.assertEqual(len(payload.sql_queries), 1)
        self.assertEqual(len(payload.connections), 1)

    def test_close_is_idempotent(self):
        """Calling close multiple times is safe."""
        q = self._make_queue()
        q.enqueue("contexts", {"uid": "1"})
        self.assertTrue(q.is_running)

        q.close()
        self.assertFalse(q.is_running)

        # Second close is a no-op
        q.close()
        self.assertFalse(q.is_running)

    def test_batch_max_size_limits_single_flush(self):
        """A single flush drains at most batch_max_size items."""
        config = make_queue_config(
            {
                "batch_min_size": 3,  # Flushing triggers only when we have 8 items
                "batch_max_size": 3,  #
                "flush_max_interval": 0.001,
            }
        )
        q = self._make_queue(config)

        # Enqueue 8 items to reach batch_min_size
        for i in range(5):
            q.enqueue("contexts", {"uid": str(i)})

        time.sleep(0.01)

        self.assertTrue(q.flusher.flush.called)

        # Flusher should have been called 2 times
        self.assertEqual(len(q.flusher.flush.call_args_list), 2)

        # First flush should contain exactly batch_max_size items
        payload = q.flusher.flush.mock_calls[0].args[0]
        self.assertEqual(len(payload.contexts), 3)

        # Second flush should contain remaining items
        payload = q.flusher.flush.mock_calls[1].args[0]
        self.assertEqual(len(payload.contexts), 2)

        q.close()


class TestFlusher(unittest.TestCase):
    """Test Flusher: encoding, compression, HTTP transport, error handling."""

    def setUp(self):
        self.mock_server = MockServer()
        self.worker = AsyncWorker(WORKER_CONFIG)
        self.client = Client(
            make_deps_config(),
            self.worker,
            httpx.MockTransport(self.mock_server),
        )
        flusher_config = Config(
            "flusher",
            data={},
            defaults={
                "url_path": "ingest/",
                "enc_buffer_size": 64 * 1024,
                "compress_level": 1,
                "request_timeout": 60.0,
            },
        )
        # Build a minimal deps-like object for the flusher
        self.deps = Mock()
        self.deps.events = Mock()
        self.deps.http_client = self.client
        self.flusher = Flusher(flusher_config, self.deps)

    def tearDown(self):
        self.client.close()
        self.worker.close()

    def test_flush_encodes_compresses_and_sends(self):
        """Flush serializes a Payload, gzip-compresses it, and POSTs it."""
        payload = Payload(
            contexts=[{"uid": "123", "ts": 456}],
            sql_queries=[{"sql": "SELECT 1"}],
        )

        self.flusher.flush(payload)

        # Wait for async HTTP to complete
        start = time.time()
        while not self.mock_server.requests and time.time() - start < 1.0:
            time.sleep(0.01)

        # Teardown closes client/worker which waits for pending requests
        self.client.close()
        self.worker.close()

        # Find the ingest request
        ingest_requests = [r for r in self.mock_server.requests if r.url.path == "/ingest/"]
        self.assertEqual(len(ingest_requests), 1)

        req = ingest_requests[0]
        self.assertEqual(req.headers["Content-Encoding"], "gzip")
        self.assertIn("X-Request-ID", req.headers)

        # Verify the payload is valid gzipped msgpack
        decompressed = gzip.decompress(req.content)
        decoded = msgspec.msgpack.decode(decompressed)
        self.assertIn("contexts", decoded)
        self.assertIn("sql_queries", decoded)

    def test_flush_handles_post_exception_gracefully(self):
        """If http_client.post() raises, flush logs and doesn't crash."""
        self.deps.http_client = Mock()
        self.deps.http_client.post = Mock(side_effect=Exception("Connection refused"))
        flusher = Flusher(self.flusher.config, self.deps)

        payload = Payload(contexts=[{"uid": "error-test"}])

        with self.assertLogs(level="INFO") as cm:
            flusher.flush(payload)

        # Should have logged the error
        self.assertTrue(any("ingest payload send result" in msg for msg in cm.output))

    def test_flush_handles_future_error_gracefully(self):
        """If the Future from post() resolves with an error, it's logged."""
        payload = Payload(contexts=[{"uid": "future-err"}])

        # Use a mock that returns a Future that fails
        import concurrent.futures

        failing_future = concurrent.futures.Future()
        failing_future.set_exception(Exception("Server error"))

        self.deps.http_client = Mock()
        self.deps.http_client.post = Mock(return_value=failing_future)
        flusher = Flusher(self.flusher.config, self.deps)

        with self.assertLogs(level="INFO") as cm:
            flusher.flush(payload)

        self.assertTrue(any("ingest payload send result" in msg for msg in cm.output))

    def test_flush_events_hook_called(self):
        """on_process_payload event is fired before sending."""
        payload = Payload(contexts=[{"uid": "hook-test"}])
        self.flusher.flush(payload)

        self.deps.events.on_process_payload.assert_called_once_with(payload)
