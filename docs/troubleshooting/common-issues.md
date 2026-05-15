# Common Issues

Solutions to frequently encountered problems when using Qorme.

## Installation

### `UnknownDescriptorError` on startup

```
qorme_django.domains.columns.UnknownDescriptorError: ['field_name', 'myapp.fields.CustomDescriptor']
```

**Cause:** The `django.columns` domain encountered a field descriptor it doesn't recognize. This is a safety measure — Qorme refuses to silently ignore unknown descriptors because it could lead to incorrect "unused column" predictions.

**Fix:** Register the descriptor in your config:

```python title="settings.py"
QORME = {
    "django": {
        "columns": {
            "known_descriptors": {
                "myapp.fields.CustomDescriptor",
            },
        },
    },
}
```

### `ConfigurationError: apps_to_include and apps_to_exclude are mutually exclusive`

**Cause:** You set both `apps_to_include` and `apps_to_exclude` in `django.queries` config.

**Fix:** Use only one. To track a subset of apps, use `apps_to_include`. To track everything except a few, use `apps_to_exclude`.

### Domain fails to enable on startup

If a domain fails during `enable()`, Qorme logs the error and continues with the remaining domains. Check your logs:

```bash
# Look for domain initialization errors
python manage.py runserver 2>&1 | grep -i "qorme"
```

Common causes:
- Missing dependency (e.g., `wagtail.page_render` without wagtail installed)
- Invalid handler class path in config
- Conflicting wrappers from another library patching the same function

## Connection issues

### No telemetry reaching the server

1. **Check the DSN** — Ensure `deps.http_client.dsn` is set correctly
2. **Check connectivity** — The SDK must be able to reach the server over HTTPS
3. **Check SSL** — For self-signed certs, set `verify_ssl: False` (dev only)
4. **Check logs** — Enable DEBUG logging:

```python
LOGGING = {
    "loggers": {
        "qorme": {"level": "DEBUG", "handlers": ["console"]},
    },
}
```

5. **Check `active`** — Ensure `QORME["active"]` is `True` (or unset)

### SSE connection not establishing (ML predictions not working)

The `MLStore` connects via SSE only when an optimization domain is enabled. Check:

1. Is `django.defer_columns` or `django.prefetch_relations` in your `domains` list?
2. Is the server's ML server running?
3. Check SSE-specific logs: `grep "ml_store\|sse" logs`

The SSE connection retries up to `max_retries` times (default 5) with `retry_interval` second intervals (default 30s).

## Runtime issues

### Queries not being tracked

Possible causes:

1. **No active `QueryContext`** — Queries outside a request/task/CLI context are silently skipped. This is by design — migrations, shell queries, and startup queries are not tracked.
2. **Model filtered out** — Check `apps_to_exclude` / `models_to_exclude` in `django.queries` config
3. **Path ignored** — Check `ignore_paths` in `django.requests` config
4. **`active: False`** — Qorme is disabled

### High memory usage

1. **Reduce queue size** — Lower `ingest.queue.queue_max_size` (default 25,000)
2. **Disable column tracking** — Remove `django.columns` to avoid per-instance BitSet allocation
3. **Reduce traceback depth** — Lower `deps.traceback.num_entries` (default 10)

### Optimization not being applied

For `defer_columns` and `prefetch_relations` to work:

1. The Qorme server must be running with the ML pipeline
2. SSE connection must be established (`ml_store.connected()` returns True)
3. Predictions must be marked as `stable` (trained on sufficient data)
4. The query must return model instances (`RowType.MODEL`)
5. No existing `.defer()` or `.only()` must be applied (for `defer_columns`)
6. `select_related()` without arguments blocks defer optimization

## Compatibility

### Django signals ordering

Qorme's `RequestTracking` connects to `request_finished` with `weak=False`. If other signal handlers run after Qorme closes the context, their queries won't be tracked. This is expected behavior.

### Third-party libraries patching Django internals

If another library (e.g., django-debug-toolbar, Sentry) also patches `QuerySet` methods or iterables, Qorme detects this via `wrapt.ObjectProxy` and raises `AlreadyWrappedError` if the same function is wrapped by the same wrapper twice, or wraps on top of the existing wrapper if it's a different one.

### Pickle/serialization

Qorme attaches `__columns_accessed__` (a `BitSet`) and `__rel_info__` (a tuple) to model instances. The `Model.__getstate__` wrapper strips these before serialization. If you bypass `__getstate__` (rare), these attributes will appear in serialized output.
