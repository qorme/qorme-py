# Ingest Domain: Data Delivery Engine

The **Ingest Domain** is the high-bandwidth backbone of the Qorme SDK. It orchestrates the process of collecting telemetry from all active domains and delivering it to the server with zero impact on application request/response cycles.

## ⚙️ How it Works

1. **Wait-Free Queueing**: Other domains push events into a high-capacity `msgspec`-serialized queue.
2. **Batching Logic**: The flusher background thread monitors the queue and batches events based on size or time thresholds.
3. **HTTP/2 Streaming**: Batches are streamed to the server using HTTP/2, reducing handshake overhead and latency.
4. **Resilience**: Implements a dedicated retry mechanism with backoff and jitter.

## 🛠️ Configuration

Enable via: `"ingest"` in the `domains` list.

### `ingest` settings

| Key | Default | Description |
| :--- | :--- | :--- |
| `rows_wait_time` | `20` | Internal polling interval for the flusher. |
| `queue.queue_max_size` | `25000` | Max normal priority events. |
| `queue.pqueue_max_size` | `50000` | Max high priority events. |
| `queue.batch_min_size` | `1000` | Threshold to trigger an immediate flush. |
| `queue.batch_max_size` | `5000` | Hard cap on events per HTTP request. |
| `queue.flush_max_interval` | `30.0` | Max seconds between flushes (even for small batches). |

### `flusher` settings

| Key | Default | Description |
| :--- | :--- | :--- |
| `enc_buffer_size` | `65536` | Buffer size for `msgpack` serialization (64 KB). |
| `compress_level` | `1` | Compression level (scaled for speed). |

## 🚀 Performance characteristics

- **Memory**: The ingest queue uses a fix-size buffer to prevent OOM errors.
- **CPU**: All serialization and hashing occur in a background `AsyncWorker` thread.
- **Latency**: The capture phase (pushing to the queue) is a constant-time operation (<1ms per event).
