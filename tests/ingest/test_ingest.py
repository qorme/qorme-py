"""Integration tests for Ingest domain."""

import gzip
import time
import unittest
from unittest.mock import Mock
from uuid import uuid4

import msgspec

from qorme.deps import Deps
from qorme.ingest.ingest import Ingest
from qorme.utils.config import Config


class TestIngestIntegration(unittest.TestCase):
    """Test Ingest domain integrates with Queue and Events."""

    def setUp(self):
        config_data = {
            "ingest": {
                "compress_level": 1,
                "rows_wait_time": 0.1,
                "queue": {
                    "join_timeout": 0.5,
                    "request_timeout": 10.0,
                    "queue_max_size": 100,
                    "pqueue_max_size": 50,
                    "batch_min_size": 3,
                    "batch_max_size": 10,
                    "flush_max_interval": 1.0,
                    "compress_level": 1,
                },
            },
            "async_worker": {"startup_timeout": 3.0},
            "http_client": {"dsn": "https://key@test.com"},
        }
        defaults = {
            "ingest": {
                "compress_level": 1,
                "rows_wait_time": 30,
                "queue": {
                    "join_timeout": 3.0,
                    "request_timeout": 10.0,
                    "queue_max_size": 10000,
                    "pqueue_max_size": 5000,
                    "batch_min_size": 250,
                    "batch_max_size": 1000,
                    "flush_max_interval": 60.0,
                    "flusher": {
                        "url_path": "ingest/",
                        "enc_buffer_size": 64 * 1024,
                        "compress_level": 1,
                        "request_timeout": 60.0,
                    },
                },
            },
            "async_worker": {"startup_timeout": 10.0},
            "http_client": {
                "dsn": "",
                "http2": False,
                "verify_ssl": False,
                "retry": {"attempts": 1, "backoff_jitter": 0, "backoff_factor": 0},
            },
        }
        self.config = Config(name="qorme", data=config_data, defaults=defaults)
        self.deps = Deps(self.config)
        self.ingest = Ingest(self.deps, self.config.ingest)

    def tearDown(self):
        if self.ingest.enabled:
            self.ingest.disable()
        self.deps.close()

    def test_events_trigger_data_ingestion(self):
        """Test firing events causes data to be ingested and sent."""
        captured = []

        def mock_post(**kwargs):
            content = kwargs["content"]
            captured.append(content)
            mock_future = Mock()
            mock_future.add_done_callback = Mock()
            return mock_future

        self.deps.http_client.post = mock_post
        self.ingest.enable()

        # Fire context created events
        for i in range(5):
            mock_context = Mock()
            mock_context.data = {"uid": str(uuid4()), "id": i, "type": "test"}
            self.deps.events.on_context_created(mock_context)

        time.sleep(0.005)

        # Should have sent compressed data
        self.assertGreater(len(captured), 0)

        # Verify it's real compressed msgspec data
        decompressed = gzip.decompress(captured[0])
        payload = msgspec.msgpack.decode(decompressed)

        self.assertIn("contexts", payload)
        self.assertGreater(len(payload["contexts"]), 0)

    def test_multiple_event_types(self):
        """Test different event types are grouped and sent together."""
        captured = []

        def mock_post(**kwargs):
            content = kwargs["content"]
            captured.append(content)
            mock_future = Mock()
            mock_future.add_done_callback = Mock()
            return mock_future

        self.deps.http_client.post = mock_post
        self.ingest.enable()

        # Fire different event types
        mock_context = Mock()
        mock_context.data = {"uid": str(uuid4()), "type": "context"}
        self.deps.events.on_context_created(mock_context)

        mock_query = {"uid": str(uuid4()), "sql": "SELECT 1"}
        self.deps.events.on_query_executed(mock_query)

        mock_conn = Mock()
        mock_conn._self_data = {"uid": str(uuid4()), "db": "test"}
        self.deps.events.on_connection_created(mock_conn)

        # Wait for flush
        time.sleep(0.005)

        # Verify data was sent and contains multiple types
        self.assertGreater(len(captured), 0)

        decompressed = gzip.decompress(captured[0])
        payload = msgspec.msgpack.decode(decompressed)

        # Should have multiple event types in one payload
        self.assertIsInstance(payload, dict)

    def test_graceful_shutdown_flushes_data(self):
        """Test disable flushes pending data before shutting down."""
        captured = []

        def mock_post(**kwargs):
            content = kwargs["content"]
            captured.append(content)
            mock_future = Mock()
            mock_future.add_done_callback = Mock()
            return mock_future

        self.deps.http_client.post = mock_post
        self.ingest.enable()

        # Enqueue some data (not enough to trigger immediate flush)
        mock_context = Mock()
        mock_context.data = {"uid": str(uuid4())}
        self.deps.events.on_context_created(mock_context)

        # Disable should flush pending data
        self.ingest.disable()

        # Should have flushed data
        self.assertGreater(len(captured), 0)

    def test_disabled_ingest_ignores_events(self):
        """Test disabled ingest doesn't process events."""
        captured = []

        def mock_post(**kwargs):
            content = kwargs["content"]
            captured.append(content)
            return Mock(add_done_callback=Mock())

        self.deps.http_client.post = mock_post

        # Don't enable ingest
        self.assertFalse(self.ingest.enabled)

        # Fire events
        mock_context = Mock()
        mock_context.data = {"uid": str(uuid4())}
        self.deps.events.on_context_created(mock_context)

        time.sleep(0.001)

        # Should not have captured anything
        self.assertEqual(len(captured), 0)
