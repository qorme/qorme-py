from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import Future
from time import time as get_time
from typing import TYPE_CHECKING
from uuid import uuid4

from qorme.ingest.payload import Payload
from qorme.utils.gzip import GzipCompressor

if TYPE_CHECKING:
    import msgspec

    from qorme.deps import Deps
    from qorme.utils.config import Config


logger = logging.getLogger(__name__)


class Queue:
    """Thread-safe queue that flushes accumulated data based on queue size or time thresholds."""

    def __init__(self, config: Config, deps: Deps) -> None:
        self.deps = deps
        self.config = config
        self.join_timeout = config.join_timeout
        self.batch_min_size = config.batch_min_size
        self.batch_max_size = config.batch_max_size
        self.flush_max_interval = config.flush_max_interval
        self.flusher = Flusher(config.flusher, deps)

        self._queue = queue.Queue(maxsize=config.queue_max_size)
        self._pqueue = queue.PriorityQueue(maxsize=config.pqueue_max_size)
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._condition = threading.Condition()
        self._thread: threading.Thread | None = None
        self._stop_event: threading.Event | None = None

    def enqueue(self, *data) -> bool:
        try:
            self._queue.put_nowait(data)
        except queue.Full:
            logger.warning("Queue is full, dropping data. Size=%d", self._queue.qsize())
            return False

        self._ensure_running()
        self._maybe_flush()
        return True

    def enqueue_after(self, *data, delay) -> bool:
        try:
            self._pqueue.put_nowait((get_time() + delay, data))
        except queue.Full:
            logger.warning("Priority Queue is full, dropping data. Size=%d", self._pqueue.qsize())
            return False

        self._ensure_running()
        return True

    def _notify(self):
        with self._condition:
            self._condition.notify()

    def _should_flush(self):
        return self._queue.qsize() >= self.batch_min_size

    def _maybe_flush(self):
        if self._should_flush():
            self._notify()

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    def _ensure_running(self):
        if self.is_running:
            return

        with self._lock:
            if self.is_running:
                return

            self._stop_event = threading.Event()
            thread = threading.Thread(target=self._loop, daemon=True, name="Qorme-IngestQueue")
            try:
                thread.start()
            except RuntimeError:
                self._stop_event = None
            else:
                self._thread = thread
                self._running.wait()

    def _should_stop(self):
        return self._stop_event and self._stop_event.is_set()

    def close(self, timeout: float | None = None) -> None:
        if not self.is_running:
            return

        with self._lock:
            if not self.is_running:
                return

            if evt := self._stop_event:
                evt.set()

            self._notify()

            if t := self._thread:
                t.join(timeout=timeout or self.join_timeout)

            self._thread = None
            self._stop_event = None

    def _predicate(self):
        return self._should_flush() or self._should_stop()

    def _loop(self) -> None:
        cond = self._condition
        timeout = self.flush_max_interval
        self._running.set()

        try:
            while not self._should_stop():
                self._flush_pqueue()
                with cond:
                    cond.wait_for(self._predicate, timeout=timeout)

                try:
                    self._flush(self._should_stop())
                except Exception:
                    logger.exception("Error in ingest queue worker thread", exc_info=True)
        finally:
            self._running.clear()

    def _flush(self, flush_all: bool = False) -> None:
        n = 0
        q = self._queue
        payload = Payload()

        self._flush_pqueue(flush_all)

        while True:
            if not flush_all and n == self.batch_max_size:
                break

            try:
                dtype, data = q.get_nowait()
            except queue.Empty:
                break

            getattr(payload, dtype).append(data)
            q.task_done()
            n += 1

        if n:
            self.flusher.flush(payload)

    def _flush_pqueue(self, flush_all: bool = False) -> None:
        q = self._queue
        pq = self._pqueue
        now = get_time()

        while True:
            try:
                timestamp, data = pq.get_nowait()
            except queue.Empty:
                break

            done = False
            if not flush_all and timestamp > now:
                pq.put_nowait((timestamp, data))
                done = True
            else:
                try:
                    q.put_nowait(data)
                except queue.Full:
                    pq.put_nowait((timestamp, data))
                    done = True

            pq.task_done()
            if done:
                break

    def __del__(self):
        if hasattr(self, "_thread") and self.is_running:
            logger.warning("Ingest queue garbage collected without proper shutdown")
            self.close()


class Flusher:
    """
    Helper class responsible for encoding, compressing,
    and sending payloads to the Qorme server.
    """

    def __init__(self, config: Config, deps: Deps) -> None:
        self.deps = deps
        self.config = config
        self._encoder: msgspec.msgpack.Encoder | None = None
        self._enc_buffer = bytearray(config.enc_buffer_size)
        self._compressor = GzipCompressor(config.compress_level)

    @property
    def encoder(self) -> msgspec.msgpack.Encoder:
        if not self._encoder:
            from qorme.utils.encoder import new_encoder

            self._encoder = new_encoder()
        return self._encoder

    def flush(self, payload: Payload) -> None:
        start_time = time.perf_counter_ns()
        self.deps.events.on_process_payload(payload)
        self.encoder.encode_into(payload, self._enc_buffer)
        data = self._compressor.compress(self._enc_buffer)
        request_id = uuid4().hex
        try:
            fut = self.deps.http_client.post(
                url=self.config.url_path,
                content=data,
                headers={
                    "Content-Encoding": "gzip",
                    "X-Request-ID": request_id,
                },
                timeout=self.config.request_timeout,
            )
        except Exception as e:
            fut = Future()
            fut.set_exception(e)

        size = len(self._enc_buffer)
        compressed_size = len(data)
        processing_time = (time.perf_counter_ns() - start_time) / 1e6
        fut.add_done_callback(
            lambda fut: self._request_sent(
                fut, request_id, size, compressed_size, start_time, processing_time
            )
        )

    def _request_sent(
        self,
        fut: Future,
        request_id: str,
        size: int,
        compressed_size: int,
        start_time: float,
        processing_time: float,
    ) -> None:
        error = None
        try:
            fut.result()
        except Exception as e:
            error = e

        logger.info(
            "ingest payload send result: id=%s size=%d compressed_size=%d "
            "processing_time=%fms total_time=%fms error=%s",
            request_id,
            size,
            compressed_size,
            processing_time,
            (time.perf_counter_ns() - start_time) / 1e6,
            error,
        )
