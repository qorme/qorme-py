# Environment Variables

Qorme's `Config` class **automatically resolves settings from environment variables** before checking the configuration dictionary. The lookup order for any config key is:

1. Environment variable (uppercased, underscore-separated path)
2. User-provided config dictionary
3. Default values

This means you can override any setting via environment variable without changing code.

## Naming convention

Environment variable names are derived from the config path:

```
config key path              → env var name
─────────────────────────────────────────────
active                       → QORME_ACTIVE
deps.http_client.dsn         → QORME_DEPS_HTTP_CLIENT_DSN
deps.http_client.verify_ssl  → QORME_DEPS_HTTP_CLIENT_VERIFY_SSL
deps.traceback.num_entries   → QORME_DEPS_TRACEBACK_NUM_ENTRIES
ingest.queue.batch_max_size  → QORME_INGEST_QUEUE_BATCH_MAX_SIZE
```

The root prefix is always `QORME_`, followed by the nested key path uppercased with underscores.

## Type parsing

Values from environment variables are parsed based on the expected type from the defaults:

| Type | Parsing rule | Example |
|:---|:---|:---|
| `str` | Used as-is | `QORME_DEPS_HTTP_CLIENT_DSN=https://...` |
| `int` | `int(value)` | `QORME_DEPS_TRACEBACK_NUM_ENTRIES=20` |
| `float` | `float(value)` | `QORME_INGEST_QUEUE_FLUSH_MAX_INTERVAL=15.0` |
| `bool` | `true`, `t`, `yes`, `y`, `1` → True; anything else → False | `QORME_ACTIVE=false` |
| `list` | Comma-separated | `QORME_DJANGO_QUERIES_APPS_TO_EXCLUDE=django,admin` |

## Common variables

### Kill switch

```bash
QORME_ACTIVE=false
```

Disables all tracking. `TrackingManager.start()` returns immediately without creating domains or patching functions.

### DSN (server endpoint)

```bash
QORME_DEPS_HTTP_CLIENT_DSN=https://<API_KEY>@your-qorme-server/sdk
```

### SSL verification

```bash
QORME_DEPS_HTTP_CLIENT_VERIFY_SSL=false
```

Disable for development with self-signed certificates only.

### Traceback depth

```bash
QORME_DEPS_TRACEBACK_NUM_ENTRIES=5
```

Reduce stack frame capture depth for lower overhead.

## Docker / CI usage

```dockerfile
# Disable in CI
ENV QORME_ACTIVE=false

# Point to staging server
ENV QORME_DEPS_HTTP_CLIENT_DSN=https://<API_KEY>@staging.qorme.com/sdk
```

```bash
# One-off override
QORME_ACTIVE=false python manage.py test
QORME_DEPS_HTTP_CLIENT_DSN=https://<API_KEY>@staging/sdk python manage.py runserver
```

## Logging

Qorme uses Python's standard `logging` module. Configure via Django's `LOGGING` dict:

```python title="settings.py"
LOGGING = {
    "version": 1,
    "loggers": {
        "qorme": {"level": "DEBUG", "handlers": ["console"]},
        "qorme_django": {"level": "DEBUG", "handlers": ["console"]},
    },
}
```
