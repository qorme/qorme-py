# Quickstart

Get Qorme running in a Django project in 5 minutes.

## Prerequisites

- Python 3.10+
- A Django 4.2+ project
- A running Qorme server ([cloud](../guides/server-setup.md) or [self-hosted](../guides/server-setup.md))
- A project DSN (obtained from the Qorme dashboard after creating a project)

## 1. Install the packages

=== "pip"

    ```bash
    pip install qorme qorme-django
    ```

=== "uv"

    ```bash
    uv add qorme qorme-django
    ```

`qorme` is the core SDK. `qorme-django` is the Django integration that provides ORM-level tracking and auto-optimization.

## 2. Add to INSTALLED_APPS

```python title="settings.py"
INSTALLED_APPS = [
    ...,
    "qorme_django",
]
```

When Django loads the `qorme_django` app, its `AppConfig.ready()` hook calls `TrackingManager.install()` — which initializes all configured domains and starts instrumentation automatically.

## 3. Configure tracking

Add the `QORME` dictionary to your `settings.py`:

```python title="settings.py"
QORME = {
    "domains": [
        "ingest",                   # Required — batches and sends telemetry
        "db.psycopg",               # Track PostgreSQL queries (1)
        "django.cli",               # Management command tracking
        "django.queries",           # ORM query tracking with N+1 detection
        "django.requests",          # HTTP request lifecycle tracking
        "django.columns",           # Track which columns are actually accessed
        "django.relations",         # Track relationship traversals
    ],
    "deps": {
        "http_client": {
            "dsn": "https://<API_KEY>@your-qorme-server/sdk",
        },
    },
}
```

1.  Use `"db.sqlite"` instead if you're running SQLite, or `"db.psycopg2"` for the legacy psycopg2 driver.

!!! info "Domain selection"
    You don't need all domains. Start with `ingest` + `db.*` + `django.queries` + `django.requests` for basic observability. Add `django.columns` and `django.relations` when you want field-level tracking (medium overhead).

## 4. Run your project

```bash
python manage.py runserver
```

Open your application and browse a few pages. Qorme is now:

- Capturing ORM queries with their SQL, duration, traceback, and result fingerprint
- Tracking which HTTP request triggered each query
- Recording which model fields your code actually accesses
- Monitoring relationship traversals for N+1 patterns
- Batching all telemetry and streaming it to the server in the background

## 5. See results

Open the Qorme dashboard to see:

- **Query timeline** — every query across every request, with timing and SQL
- **N+1 detection** — automatically flagged repeated query patterns
- **Unused columns** — fields your queries fetch but your code never reads
- **Relationship depth** — how deep your code traverses model relationships

## Next steps

| Want to... | Go to... |
|:---|:---|
| Enable automatic optimization (defer + prefetch) | [Auto-Optimization guide](../guides/django/optimization.md) |
| Understand every configuration option | [Configuration reference](../reference/configuration.md) |
| Track Celery background tasks | [Celery integration](../guides/integrations/celery.md) |
| Add Wagtail CMS profiling | [Wagtail integration](../guides/integrations/wagtail.md) |
| Deploy to production | [Deployment guide](../guides/deployment.md) |
| Understand the architecture | [How It Works](how-it-works.md) |
