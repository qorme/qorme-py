# Installation

## Packages

Qorme is distributed as two packages:

| Package | What it provides |
|:---|:---|
| `qorme` | Core SDK — tracking engine, ingest pipeline, ML store, database driver instrumentation, Celery integration |
| `qorme-django` | Django integration — ORM query tracking, request lifecycle, template profiling, column/relation tracking, auto-optimization |

## Install

=== "pip"

    ```bash
    # Core SDK only
    pip install qorme

    # With Django integration
    pip install qorme qorme-django
    ```

=== "uv"

    ```bash
    # Core SDK only
    uv add qorme

    # With Django integration
    uv add qorme qorme-django
    ```

## Requirements

- **Python**: 3.10 or later
- **Django**: 4.2 or later (for `qorme-django`)

### Core dependencies

These are installed automatically:

| Dependency | Purpose |
|:---|:---|
| `wrapt` | Transparent function/method patching |
| `msgspec` | High-performance serialization for telemetry payloads |
| `xxhash` | Fast hashing for query result fingerprinting |
| `httpx[http2]` | HTTP/2 client for telemetry delivery and SSE |
| `httpx-retries` | Retry logic with backoff for network resilience |
| `httpx-sse` | Server-Sent Events client for ML model updates |
| `typing-extensions` | Extended type hints for Python 3.10 compatibility |
| `isal` | Hardware-accelerated compression (x86_64/aarch64 only) |

### C extensions

Qorme ships pre-compiled C extensions for critical hot paths:

- **`qorme.utils.bitset`** — Bit-level column access tracking with minimal memory
- **`qorme.utils.traceback`** — Optimized stack frame extraction and caching
- **`qorme.utils.lru_cache`** — High-performance LRU cache for repeated lookups

These are compiled from C sources (generated from Cython `.pyx` files) and distributed as platform-specific `.so` files. Cython is only needed if you modify the `.pyx` sources.

## Install from source

```bash
git clone https://github.com/qorme/qorme-py.git
cd qorme-py
uv sync
```

This installs the core SDK and all development dependencies. The `qorme-django` integration is part of the same workspace:

```bash
# Run tests for the core SDK
uv run pytest tests/

# Run tests for the Django integration
uv run pytest integrations/qorme-django/tests/
```

## Verify installation

```python
>>> import qorme
>>> qorme.__version__
'0.1.0a1'
```

## What's next

After installing, follow the [Quickstart](quickstart.md) to configure Qorme for your project.
