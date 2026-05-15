# Performance Characteristics

How Qorme is designed to minimize overhead in production applications.

## Design philosophy

Qorme's instrumentation runs **on the critical path** — inside Django's queryset iteration, field descriptor access, and cursor execution. Every microsecond of overhead is multiplied by every query in every request. The codebase is engineered accordingly.

## Hot path optimizations

### C extensions

Three Cython-compiled modules handle the highest-frequency operations:

| Module | Operation | Why C? |
|:---|:---|:---|
| `qorme.utils.bitset` | Column access tracking (`.set(index)`) | Called once per field access per instance. Python `set.add()` has ~200ns overhead; C bitset is ~5ns. |
| `qorme.utils.traceback` | Stack frame extraction | Extracts 10 frames per query. C avoids creating intermediate Python frame objects. |
| `qorme.utils.lru_cache` | Frame/file info caching | Repeated views hit the same code paths. C LRU avoids `dict` hash overhead. |

### Lazy initialization

All `Deps` properties are lazily initialized:

- `ml_store` is never created if you only use monitoring domains
- `async_worker` is never started if the ingest queue is empty
- `traceback` caches are allocated on first query, not on startup

### Weak references

The `Wrapper` class uses `WeakKeyDictionary` and `weakref.ref` to store wrapping state. This means:

- Wrapped objects can be garbage collected normally
- No retention of references to model classes, descriptors, or iterators
- Memory usage stays proportional to the number of active wrappers, not the number of tracked objects

### Zero-copy serialization

Telemetry is serialized using `msgspec.msgpack`:

- No intermediate Python dict creation
- Structs are compiled at import time
- Binary encoding is 3-10x smaller than JSON
- `isal` compression (hardware-accelerated on x86_64/aarch64) runs at compression level 1 for speed over ratio

## Per-domain overhead

### Monitoring domains

| Domain | Per-query | Per-instance | Notes |
|:---|:---|:---|:---|
| `django.queries` | ~2µs wrapper call | ~1µs event fire per instance | Wraps 5 iterable classes + 2 methods |
| `django.requests` | N/A | N/A | One wrapper call per request (negligible) |
| `django.columns` | None directly | ~5ns per field access (C bitset) | Descriptor replacement is one-time per model |
| `django.relations` | ~1µs event handler | ~100ns tuple assignment | Assigns `__rel_info__` per instance |
| `django.template` | ~5-50µs stack walk | N/A | Most expensive — walks frames to find template node |
| `db.*` | ~2µs proxy call | N/A | `ObjectProxy` is transparent |

### Optimization domains

| Domain | Per-query | Notes |
|:---|:---|:---|
| `django.defer_columns` | ~10µs prediction lookup | Only runs when `ml_store.connected()` is True |
| `django.prefetch_relations` | ~10µs prediction lookup | Only runs when `ml_store.connected()` is True |

### Infrastructure

| Domain | Background | Notes |
|:---|:---|:---|
| `ingest` | Thread-safe queue + background flush | Queue operations are ~100ns. Flushing is async on a background thread. |

## Memory usage

### Per-request overhead

Each `QueryContext` allocates:
- A `ContextData` struct (~200 bytes)
- A list of `ORMQuery` references

Each `ORMQuery` allocates:
- An `ORMQueryData` struct (~300 bytes)
- A `Row` tracking struct per model path per query (if columns tracking is enabled)

### Steady-state overhead

- **Event handlers** — `defaultdict(set)` with ~15 handlers total — negligible
- **Wrapper state** — `WeakKeyDictionary` with one entry per wrapped class/module — negligible
- **MLStore models** — In-memory dict of trained decision trees. Typically <1MB for most projects.
- **Ingest queue** — Configurable, default max 25,000 events × ~500 bytes ≈ 12.5 MB max
- **Traceback caches** — Fixed-size LRU caches: 1024 entries + 256 file info entries

## Benchmarks

!!! tip "Run your own benchmarks"
    Overhead depends heavily on your query volume, model complexity, and domain selection. Profile with and without Qorme in your staging environment to measure actual impact:

    ```python
    # Disable Qorme for comparison
    QORME = {"active": False}
    ```

## Recommendations

| Scenario | Recommended domains | Expected overhead |
|:---|:---|:---|
| **Development** | All domains | Not critical |
| **Staging / QA** | All domains | <5% overhead typical |
| **Production (observability only)** | `ingest` + `db.*` + `django.queries` + `django.requests` | <1% overhead |
| **Production (+ field tracking)** | Above + `django.columns` + `django.relations` | <2% overhead |
| **Production (+ optimization)** | Above + `django.defer_columns` + `django.prefetch_relations` | <2% overhead (net negative if optimizations save more than they cost) |
| **Production (minimal)** | `ingest` + `db.*` + `django.queries` | <0.5% overhead |
