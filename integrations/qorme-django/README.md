# Qorme Django Integration

The official integration between Qorme and the Django web framework. This package enables deep, **self-healing observability** for Django applications.

## 🚀 The Self-Healing ORM

Qorme is the first ORM observability tool that automatically fixes performance issues for you. By using the Django integration, you can enable:

- **Automatic Deferring**: Resolve high memory usage by only fetching the columns your view actually needs.
- **Automatic Prefetching**: Resolve N+1s by dynamically pre-populating relationships before they are accessed.

## 📦 Quick Setup

1. **Install**:
   ```bash
   pip install qorme-django
   ```

2. **Configure**:
   Add `"qorme_django"` to your `INSTALLED_APPS` and define your `QORME` settings:

   ```python
   QORME = {
       "domains": [
           "ingest", 
           "ml", 
           "django.queries", 
           "defer_columns", 
           "prefetch_relations"
       ],
       "deps": {"http_client": {"dsn": "https://your-dsn-here@api.qorme.com/"}},
   }
   ```

## 📖 High-Fidelity documentation

Browse our granular guides for كل part of the Django ecosystem:

- **[Installation & Setup Guide](../../docs/django/setup.md)**: Detailed configuration logic.
* **[Automatic Optimization Guide](../../docs/django/optimization/index.md)**: How the "Self-Healing" logic works.
* **Tracking Domain Deep-Dives**:
    - [ORM & Query Intelligence](../../docs/django/domains/queries.md)
    - [HTTP Request Lifecycle](../../docs/django/domains/requests.md)
    - [Template Rendering](../../docs/django/domains/template.md)
    - [Unused Column Profiling](../../docs/django/domains/columns.md)
    - [Relationship Dependency Mapping](../../docs/django/domains/relations.md)
* **Framework Extensions**:
    - [Wagtail CMS Profiling](../../docs/django/contrib/wagtail.md)
    - [Taggit Relationship Optimization](../../docs/django/contrib/taggit.md)

---

For architecture details, the ML Store, and core SDK configuration, see the [main Qorme documentation](../../docs/).
