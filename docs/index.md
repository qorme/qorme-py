---
hide:
  - navigation
  - toc
---

# Qorme

**Observability and automatic optimization for Python ORMs.**

---

Qorme is an SDK that instruments your ORM layer to collect high-fidelity performance data, then uses that data to **automatically fix** common database bottlenecks — at runtime, without code changes.

<div class="grid cards" markdown>

-   :material-magnify:{ .lg .middle } **Observe**

    ---

    Track ORM queries, column access, relationship traversals, and template renders across your application — with full traceback attribution.

    [:octicons-arrow-right-24: How it works](getting-started/how-it-works.md)

-   :material-auto-fix:{ .lg .middle } **Auto-Optimize**

    ---

    ML models trained on your actual usage patterns automatically apply `.defer()` and `.prefetch_related()` before queries hit the database.

    [:octicons-arrow-right-24: Auto-Optimization guide](guides/django/optimization.md)

-   :material-puzzle:{ .lg .middle } **Modular**

    ---

    Enable only the tracking you need. Each capability is a standalone domain — mix and match to control overhead and precision.

    [:octicons-arrow-right-24: Domain registry](reference/domains.md)

-   :material-speedometer:{ .lg .middle } **Performance-First**

    ---

    C extensions for hot paths (bitsets, traceback, LRU cache), async background I/O, and zero-copy serialization via `msgspec`.

    [:octicons-arrow-right-24: Performance design](understanding/performance.md)

</div>

## Get Started

The fastest way to try Qorme is with Django:

```bash
pip install qorme qorme-django
```

```python title="settings.py"
INSTALLED_APPS = [
    ...,
    "qorme_django",
]

QORME = {
    "domains": [
        "ingest",
        "db.psycopg",
        "django.queries",
        "django.requests",
    ],
    "deps": {
        "http_client": {
            "dsn": "https://<API_KEY>@your-qorme-server/sdk",
        },
    },
}
```

That's it. Qorme auto-instruments your Django ORM, captures query telemetry, and streams it to the Qorme server for analysis.

[:octicons-arrow-right-24: Full quickstart guide](getting-started/quickstart.md){ .md-button .md-button--primary }
[:octicons-arrow-right-24: Installation options](getting-started/installation.md){ .md-button }

## How It Fits Together

Qorme has two components:

| Component | Description | License |
|:---|:---|:---|
| **Python SDK** (`qorme` + integrations) | Instruments your ORM, collects telemetry, applies optimizations | Apache 2.0 |
| **Qorme Server** (Go backend) | Stores telemetry, trains ML models, serves predictions via SSE | [FSL-1.1-ALv2](https://fsl.software/) |

The SDK sends telemetry to the server. The server trains ML models on your app's actual behavior and pushes predictions back to the SDK via Server-Sent Events. The SDK then modifies queries in-flight — adding `.defer()` for unused columns, `.prefetch_related()` for N+1 patterns.

You can use the **Qorme Cloud** (managed hosting) or **self-host** the server with Docker Compose.

[:octicons-arrow-right-24: Server setup guide](guides/server-setup.md){ .md-button }

## Current Integrations

| Integration | Package | Status |
|:---|:---|:---|
| **Django** | `qorme-django` | ✅ Available |
| **Celery** | built into `qorme` | ✅ Available |
| **Wagtail** | built into `qorme-django` | ✅ Available |
| **Taggit** | built into `qorme-django` | ✅ Available |
| **SQLite** | built into `qorme` | ✅ Available |
| **Psycopg 3** | built into `qorme` | ✅ Available |
| **Psycopg 2** | built into `qorme` | ✅ Available |
| **SQLAlchemy** | `qorme-sqlalchemy` | 🚧 In progress |
