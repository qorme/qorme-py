# Deployment

Production deployment guide for the Qorme SDK.

## Environment variables

### Kill switch

```bash
QORME_ACTIVE=false
```

Qorme's `Config` class automatically resolves settings from environment variables (uppercased, underscore-separated path). `QORME_ACTIVE` maps to the `active` key in the root config, so setting this env var disables all tracking without any code changes.

### DSN

The DSN can also be set via environment variable. Since `Config` resolves nested keys as `PARENT_CHILD_KEY`, the DSN env var is:

```bash
QORME_DEPS_HTTP_CLIENT_DSN=https://<API_KEY>@your-qorme-server/sdk
```

Alternatively, you can bridge it manually in settings:

```python title="settings.py"
import os

QORME = {
    "deps": {
        "http_client": {
            "dsn": os.environ.get("QORME_DSN", ""),
        },
    },
}
```

## Web server compatibility

### Gunicorn

Qorme works out of the box with Gunicorn's `sync`, `gthread`, and `gevent` workers.

```bash
gunicorn myproject.wsgi:application --workers 4
```

Each worker process runs its own `TrackingManager` instance with independent domains, ingest queue, and SSE connection. This is by design — no shared state between workers.

!!! info "Worker count and server load"
    Each worker maintains its own SSE connection to the Qorme server for ML model updates. With many workers, this means many SSE connections. The server handles this efficiently, but be aware of it when scaling.

### Uvicorn / ASGI

Qorme's tracking uses `ContextVar` for thread and async safety. It works with ASGI servers, but the current Django integration domains are designed for synchronous Django views. Async Django view support is on the [roadmap](../contributing/roadmap.md).

```bash
uvicorn myproject.asgi:application --workers 4
```

### uWSGI

Works with uWSGI in prefork mode. Each worker gets its own `TrackingManager`.

```ini title="uwsgi.ini"
[uwsgi]
module = myproject.wsgi:application
master = true
processes = 4
```

## Docker

Qorme doesn't require any special Docker configuration. Ensure the container can reach the Qorme server:

```dockerfile
ENV QORME_DEPS_HTTP_CLIENT_DSN=https://<API_KEY>@your-qorme-server/sdk
```

## Shutdown behavior

Qorme registers an `atexit` handler that:

1. Disables all domains (removing all wrappers)
2. Flushes the ingest queue (waits up to `queue.join_timeout` seconds, default 60s)
3. Closes the HTTP client and SSE connection
4. Shuts down the async worker event loop

This ensures telemetry collected during the last requests is delivered before the process exits.

### Tuning shutdown timeouts

```python title="settings.py"
QORME = {
    "deps": {
        "async_worker": {
            "shutdown_timeout": 60.0,  # Max wait for background tasks (seconds)
        },
        "http_client": {
            "shutdown_timeout": 60.0,  # Max wait for HTTP client to flush
        },
    },
    "ingest": {
        "queue": {
            "join_timeout": 60.0,      # Max wait for queue to drain
        },
    },
}
```

## Performance tuning

### Ingest queue sizing

The ingest queue batches telemetry events before sending them to the server. Default settings work for most applications:

```python
QORME = {
    "ingest": {
        "queue": {
            "queue_max_size": 25000,      # Max events in queue before dropping
            "batch_min_size": 1000,       # Min events per batch
            "batch_max_size": 5000,       # Max events per batch
            "flush_max_interval": 30.0,   # Max seconds between flushes
        },
    },
}
```

For high-traffic applications, increase `queue_max_size` and `batch_max_size`. For low-traffic applications where you want faster feedback, decrease `flush_max_interval`.

### Traceback depth

Stack traces are captured for every query. The default depth is 10 frames:

```python
QORME = {
    "deps": {
        "traceback": {
            "num_entries": 10,              # Frames to capture
            "entries_cache_size": 1024,     # LRU cache for frame lookups
        },
    },
}
```

Reducing `num_entries` reduces per-query overhead. The traceback extractor uses a C extension with an LRU cache, so repeated call patterns (same view, same code path) are near-free after the first capture.

### HTTP client

```python
QORME = {
    "deps": {
        "http_client": {
            "http2": True,              # Use HTTP/2 (recommended)
            "verify_ssl": True,         # SSL verification
            "request_timeout": 60.0,    # Request timeout in seconds
            "retry": {
                "attempts": 5,          # Max retry attempts
                "backoff_factor": 0.5,  # Exponential backoff base
                "backoff_jitter": 1.0,  # Jitter range for backoff
            },
        },
    },
}
```

## Monitoring Qorme itself

Qorme logs to the `qorme` logger namespace. To see what it's doing:

```python title="settings.py"
LOGGING = {
    "loggers": {
        "qorme": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "qorme_django": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}
```

Key log messages:

- `DEBUG` — Domain enable/disable, wrapper installation, ML predictions applied
- `WARNING` — SSE connection failures, queue overflow, retry attempts
- `ERROR` — Domain initialization failures, unrecognized descriptors

## What's next

- [Server Setup](server-setup.md) — getting the Qorme server running
- [Testing](../troubleshooting/testing.md) — using Qorme in tests
