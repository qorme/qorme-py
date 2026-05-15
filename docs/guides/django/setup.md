# Django Setup

Detailed configuration for integrating Qorme with your Django project.

## Requirements

- Python 3.10+
- Django 4.2+
- A running Qorme server ([cloud or self-hosted](../server-setup.md))

## Installation

=== "pip"

    ```bash
    pip install qorme qorme-django
    ```

=== "uv"

    ```bash
    uv add qorme qorme-django
    ```

## Configuration

### 1. Add the app

```python title="settings.py"
INSTALLED_APPS = [
    ...,
    "qorme_django",
]
```

When Django loads `qorme_django`, its `AppConfig.ready()` method calls:

```python
TrackingManager.install(
    settings=getattr(settings, "QORME", {}),
    defaults=QORME_DJANGO_SETTINGS,
)
```

This merges your `QORME` settings over the defaults, initializes the `Deps` container, and enables all configured domains.

### 2. Add the QORME dictionary

```python title="settings.py"
QORME = {
    "domains": [
        # Infrastructure (required)
        "ingest",                       # Telemetry batching and delivery

        # Database driver (pick one)
        "db.psycopg",                   # Psycopg v3
        # "db.psycopg2",                # Psycopg v2 (legacy)
        # "db.sqlite",                  # SQLite

        # Django observability
        "django.cli",                   # Management command tracking
        "django.queries",               # ORM query tracking
        "django.requests",              # HTTP request lifecycle
        "django.columns",               # Column access tracking
        "django.relations",             # Relationship traversal tracking
        "django.template",              # Template rendering profiling

        # Django auto-optimization (requires ML connection)
        "django.defer_columns",         # Auto-defer unused columns
        "django.prefetch_relations",    # Auto-prefetch N+1 relations

        # Optional integrations
        # "celery.tracking",            # Celery task tracking
        # "wagtail.page_render",        # Wagtail page serve tracking
        # "taggit.relations",           # Taggit relation tracking
    ],
    "deps": {
        "http_client": {
            "dsn": "https://<API_KEY>@your-qorme-server/sdk",
        },
    },
}
```

### Domain selection guide

Not every project needs every domain. Here's a practical guide:

| Goal | Domains to enable |
|:---|:---|
| **Basic observability** | `ingest` + `db.*` + `django.queries` + `django.requests` |
| **+ Column waste detection** | Add `django.columns` |
| **+ N+1 detection** | Add `django.relations` |
| **+ Template attribution** | Add `django.template` |
| **+ Auto-optimization** | Add `django.defer_columns` + `django.prefetch_relations` |

!!! warning "Optimization domains require a server connection"
    `django.defer_columns` and `django.prefetch_relations` depend on ML models from the Qorme server. Without a server connection, they enable cleanly but do nothing — they check `ml_store.connected()` before every optimization attempt.

## Configuration reference

### Django Queries (`django.queries`)

Controls which models are tracked.

```python
QORME = {
    "django": {
        "queries": {
            "apps_to_include": [],      # Track only these apps (empty = all)
            "apps_to_exclude": [],      # Exclude these apps (empty = none)
            "models_to_include": [],    # Track only these models ("app.Model")
            "models_to_exclude": [],    # Exclude these models
        },
    },
}
```

!!! info "`include` and `exclude` are mutually exclusive"
    Setting both `apps_to_include` and `apps_to_exclude` raises `ConfigurationError`. Same for models.

### Django Requests (`django.requests`)

```python
QORME = {
    "django": {
        "requests": {
            "ignore_paths": ["/health/", "/readiness/"],
        },
    },
}
```

Paths matching `ignore_paths` won't create a `QueryContext`, so no queries from those requests are tracked.

### Django Columns (`django.columns`)

```python
QORME = {
    "django": {
        "columns": {
            "known_descriptors": set(),  # FQN of custom descriptors to track
        },
    },
}
```

If your models use custom field descriptors (beyond Django's built-in `DeferredAttribute` and `ForeignKeyDeferredAttribute`), add their fully-qualified class names here. Otherwise Qorme raises `UnknownDescriptorError` to avoid silently missing field accesses.

### Celery (`celery.tracking`)

```python
QORME = {
    "celery": {
        "tracking": {
            "ignore_tasks": ["myapp.tasks.noisy_task"],
        },
    },
}
```

## Kill switch

Disable Qorme entirely without removing configuration:

```python title="settings.py"
QORME = {
    "active": False,  # Qorme will not install any tracking
    ...
}
```

Or via environment variable:

```bash
QORME_ACTIVE=false python manage.py runserver
```

When inactive, `TrackingManager.install()` returns immediately without creating any domains or patching any functions.

## What's next

- [Observability](observability.md) — what you get out of the box
- [Auto-Optimization](optimization.md) — how ML-driven fixes work
- [Columns & Relations](columns-and-relations.md) — field-level tracking details
