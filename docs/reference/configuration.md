# Configuration Reference

Complete configuration reference for the Qorme SDK. All keys, defaults, and valid values verified against the source code.

## Top-level settings

```python title="settings.py"
QORME = {
    "active": True,        # Kill switch — set False to disable all tracking
    "domains": [],         # List of domain IDs to enable
    "deps": { ... },       # Shared dependencies configuration
    "ingest": { ... },     # Ingest domain configuration
    "db": { ... },         # Database driver configurations
    "celery": { ... },     # Celery integration configuration
    "django": { ... },     # Django integration configuration (qorme-django only)
    "taggit": { ... },     # Taggit integration configuration (qorme-django only)
    "wagtail": { ... },    # Wagtail integration configuration (qorme-django only)
}
```

## `deps` — Shared dependencies

### `deps.async_worker`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `startup_timeout` | `float` | `3.0` | Seconds to wait for the background event loop to start |
| `shutdown_timeout` | `float` | `60.0` | Seconds to wait for pending background tasks on shutdown |

### `deps.http_client`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `dsn` | `str` | `""` | Server endpoint URL (e.g., `https://dsn@api.qorme.com/`) |
| `request_timeout` | `float` | `60.0` | HTTP request timeout in seconds |
| `shutdown_timeout` | `float` | `60.0` | Seconds to wait for HTTP client to flush on shutdown |
| `http2` | `bool` | `True` | Use HTTP/2 (recommended for multiplexed telemetry) |
| `verify_ssl` | `bool` | `True` | Verify TLS certificates (disable only for self-signed dev certs) |

### `deps.http_client.retry`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `attempts` | `int` | `5` | Maximum retry attempts for failed requests |
| `backoff_factor` | `float` | `0.5` | Base for exponential backoff (seconds) |
| `backoff_jitter` | `float` | `1.0` | Random jitter range added to backoff |

### `deps.traceback`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `num_entries` | `int` | `10` | Number of stack frames to capture per query |
| `entries_cache_size` | `int` | `1024` | LRU cache size for frame lookups (C extension) |
| `file_info_cache_size` | `int` | `256` | LRU cache size for file info lookups |
| `default_ignored_modules` | `list[str]` | `["qorme", "wsgiref", "gunicorn", ...]` | Modules excluded from tracebacks |
| `extra_ignored_modules` | `list[str]` | `[]` | Additional modules to exclude |

Default `default_ignored_modules`:
```python
["qorme", "wsgiref", "gunicorn", "unittest", "threading", "socketserver"]
```

The Django integration appends additional Django-internal modules to this list.

### `deps.ml_store.sse`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `url_path` | `str` | `"ml/updates/"` | SSE endpoint path (appended to DSN base) |
| `max_retries` | `int` | `5` | Maximum SSE reconnection attempts |
| `retry_interval` | `float` | `30.0` | Seconds between reconnection attempts |
| `startup_timeout` | `float` | `3.0` | Seconds to wait for initial SSE connection |
| `read_timeout` | `float` | `90.0` | Seconds before considering SSE connection stale |

## `ingest` — Telemetry pipeline

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.ingest.ingest.Ingest"` | Ingest domain handler class |
| `rows_wait_time` | `int` | `20` | Seconds to delay row data enqueue (allows column access tracking to complete) |

### `ingest.queue`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `join_timeout` | `float` | `60.0` | Seconds to wait for queue drain on shutdown |
| `queue_max_size` | `int` | `25000` | Maximum events in the queue before dropping |
| `pqueue_max_size` | `int` | `50000` | Maximum events in the priority queue |
| `batch_min_size` | `int` | `1000` | Minimum events per batch before flushing |
| `batch_max_size` | `int` | `5000` | Maximum events per batch |
| `flush_max_interval` | `float` | `30.0` | Maximum seconds between flushes |

### `ingest.queue.flusher`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `url_path` | `str` | `"ingest/"` | Ingest endpoint path (appended to DSN base) |
| `enc_buffer_size` | `int` | `65536` | Encoding buffer size in bytes (64 KB) |
| `compress_level` | `int` | `1` | Compression level 0-3 (isal levels, scaled for gzip fallback) |
| `request_timeout` | `float` | `60.0` | HTTP request timeout for batch delivery |

## `db` — Database drivers

### `db.sqlite`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.db.integrations.sqlite.SQLiteTracking"` | Handler class |

### `db.psycopg`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.db.integrations.psycopg.PsycopgTracking"` | Handler class |

### `db.psycopg2`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.db.integrations.psycopg2.Psycopg2Tracking"` | Handler class |

### `db.params_hash`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.db.domains.params_hash.ParamsHash"` | Handler class |

### `db.result_hash`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.db.domains.result_hash.ResultHash"` | Handler class |

## `celery` — Celery integration

### `celery.tracking`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme.contrib.celery.tracking.CeleryTracking"` | Handler class |
| `ignore_tasks` | `list[str]` | `[]` | Task names to skip tracking |

## `django` — Django integration

These settings are only available when `qorme-django` is installed.

### `django.queries`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.queries.QueryTracking"` | Handler class |
| `apps_to_include` | `list[str]` | `[]` | Only track these Django apps (empty = all) |
| `apps_to_exclude` | `list[str]` | `[]` | Exclude these Django apps |
| `models_to_include` | `list[str]` | `[]` | Only track these models (`"app.Model"`) |
| `models_to_exclude` | `list[str]` | `[]` | Exclude these models |

!!! warning "Mutually exclusive"
    Setting both `apps_to_include` and `apps_to_exclude` raises `ConfigurationError`.

### `django.columns`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.columns.ColumnsTracking"` | Handler class |
| `known_descriptors` | `set[str]` | `set()` | Fully-qualified names of custom field descriptors |

### `django.requests`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.requests.RequestTracking"` | Handler class |
| `ignore_paths` | `list[str]` | `[]` | URL paths/view names to skip |

### `django.template`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.template.TemplateTracking"` | Handler class |

### `django.relations`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.relations.RelationTracking"` | Handler class |

### `django.cli`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.cli.CLITracking"` | Handler class |

### `django.defer_columns`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.ml.defer_columns.DeferColumns"` | Handler class |

### `django.prefetch_relations`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.domains.ml.prefetch_relations.PrefetchRelations"` | Handler class |

## `taggit` — Taggit integration

### `taggit.relations`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.contrib.taggit.relations.RelationTracking"` | Handler class |

## `wagtail` — Wagtail integration

### `wagtail.page_render`

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `handler` | `str` | `"qorme_django.contrib.wagtail.page_render.PageRender"` | Handler class |
