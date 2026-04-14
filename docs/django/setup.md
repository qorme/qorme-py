# Django Integration Setup

The Qorme Django integration provides deep, automated observability and self-healing optimizations for Django applications.

## 📦 Installation

```bash
pip install qorme-django
```

## 🛠️ Configuration

Qorme is configured via the `QORME` dictionary in your `settings.py`.

### 1. Enable the Application
Add `qorme_django` to your `INSTALLED_APPS`:

```python
# settings.py

INSTALLED_APPS = [
    ...
    "qorme_django",
]
```

### 2. Configure Tracking
Specify your DSN and the active tracking domains:

```python
# settings.py

QORME = {
    "domains": [
        "ingest",                       # Required for data delivery
        "db.sqlite",                    # Record SQL queries executed with SQlite driver
        "db.psycopg",                   # Record SQL queries executed with psycopg driver
        "django.requests",              # Monitor view performance
        "django.queries",               # Deep ORM observability
        "django.template",              # Trace template rendering
        "django.cli",                   # Monitor management commands
        "django.columns",               # Track columns accesses
        "django.relations",             # Track relations accessed
        "taggit.relations",             # For taggit integration
        "wagtail.page_render",          # For wagtail integration
        "django.defer_columns",         # Automated columns deferring
        "django.prefetch_relations",    # Automated N+1 resolution
    ],
    "deps": {
        "http_client": {
            "dsn": "your-dsn-here",
        },
    },
}
```

## 🏗️ Architecture Note

The Django integration uses an `AppConfig.ready()` hook to initialize the core `TrackingManager`.

- **Auto-Instrumentation**: Qorme automatically patches Django's database backend, template signals, and request lifecycles.
- **QueryContext Isolation**: Each HTTP request is wrapped in a dedicated `QueryContext` to ensure telemetry is cross-correlated within the request.

## 🚀 Deployment

- Ensure your production environment has the `QORME_ACTIVE` environment variable available as a kill-switch.
- For high-traffic applications, consider tuning the `ingest.queue` size settings in your configuration.
