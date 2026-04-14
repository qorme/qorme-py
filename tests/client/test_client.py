import asyncio
import threading
import time
import unittest

import httpx

from qorme.client.client import Client
from qorme.utils.async_worker import AsyncWorker
from qorme.utils.config import Config

from ..mock import MockServer


# TODO: Test post and sse
class TestClient(unittest.TestCase):
    client_config = Config(
        "test-client",
        data={"dsn": "https://key@test.com"},
        defaults={
            "dsn": "",
            "request_timeout": 0.1,
            "shutdown_timeout": 1.0,
            "http2": True,
            "verify_ssl": True,
            "retry": {
                "attempts": 1,
                "backoff_jitter": 1.0,
                "backoff_factor": 0.5,
            },
        },
    )
    worker_config = Config(
        "test-async-worker",
        data={
            "startup_timeout": 1.0,
            "shutdown_timeout": 1.0,
        },
        defaults={},
    )

    def setUp(self):
        self.worker = AsyncWorker(self.worker_config)
        self.client = Client(
            self.client_config,
            self.worker,
            httpx.MockTransport(MockServer(event_stream=self.event_stream)),
        )

    def tearDown(self):
        self.client.close()
        self.worker.close()

    def event_stream(self):
        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b": test stream\n"
                yield b"\n"
                yield b"data: first event\n"
                yield b"id: 1\n"
                yield b"\n"
                yield b"data: second event\n"
                yield b"id: 2\n"
                yield b"\n"
                yield b"data:  third event\n"
                yield b"id: 3\n"
                yield b"\n"
                # Mimic long lived connection.
                await asyncio.sleep(100.0)

        return Body()

    def test_get(self):
        fut = self.client.get(url="/")
        response = fut.result(1.0)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"text": "Hello, world!"})

    def test_sse(self):
        class Handler:
            def __init__(self, expected_events_count):
                self.done = threading.Event()
                self.events = []
                self.exit_calls = 0
                self.on_connect_calls = 0
                self.on_disconnect_calls = 0
                self.expected_events_count = expected_events_count

            def get_last_event_id(self):
                return ""

            def on_sse_connect(self):
                self.on_connect_calls += 1

            def on_sse_disconnect(self):
                self.on_disconnect_calls += 1

            def on_sse_exit(self):
                self.exit_calls += 1

            async def on_event(self, event):
                self.events.append(event)
                if len(self.events) == self.expected_events_count:
                    self.done.set()

        handler = Handler(3)
        fut = self.client.sse("/sse/", handler)
        # Wait for all messages to come through
        handler.done.wait()

        # Cancel SSE task
        self.assertTrue(fut.cancel())

        # Wait for final cleanup
        time.sleep(0.005)

        self.assertEqual(handler.on_connect_calls, 1)
        self.assertEqual(handler.on_disconnect_calls, 1)
        self.assertEqual(handler.exit_calls, 1)
        self.assertEqual(len(handler.events), 3)
