# Available Domains Index

Qorme is built with a modular architecture where every piece of tracking is a **Domain**. Domains can be enabled individually in your configuration list (`domains: ["ingest", "db.sqlite", ...]`).

## 🧱 Core Domains
Foundational modules built into the core SDK.
- **[Ingest](ingest.md)**: Buffer, batch, and flush events. (Required)
- **[ML Store](ml.md)**: Real-time synchronization of models and logic via SSE.
- **[SQLite](sqlite.md)**: Automated tracking for the built-in SQLite driver.
- **[Psycopg 3](psycopg.md)**: Advanced PostgreSQL (v3) instrumentation.
- **[Psycopg 2](psycopg.md)**: Support for legacy PostgreSQL (v2) driver.

## 🎸 Django Domains
Part of the `qorme-django` integration.
- **[Queries](../django/domains/queries.md)**: Deep ORM and SQL profiling.
- **[Requests](../django/domains/requests.md)**: HTTP lifecycle and view timing.
- **[Templates](../django/domains/template.md)**: Rendering performance and query attribution.
- **[Columns](../django/domains/columns.md)**: Detection of unused DB columns for optimization.
- **[Relations](../django/domains/relations.md)**: Analysis of relationship depth and N+1 patterns.

## 📦 Contrib Domains
Third-party support and specialized tracking.
- **[Celery](../contrib/celery.md)**: Background worker and task monitoring.
- **[Wagtail](../contrib/wagtail.md)**: Streamfield rendering and page depth analytics.
- **[Taggit](../contrib/taggit.md)**: Optimized tracking for `django-taggit` relations.
