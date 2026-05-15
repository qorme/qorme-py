# Qorme

**Observability and Automatic Optimization for ORMs.**

Qorme is a production-grade SDK that doesn't just monitor your database performance—it actively optimizes it. By combining deep framework instrumentation with real-time ML predictions, Qorme detects and automatically resolves common ORM bottlenecks like N+1 queries and redundant column fetching.

## 📦 Quick Install

```bash
pip install qorme qorme-django
```

> **Requires:** Python 3.10+, Django 4.2+ (for Django integration)

## 🚀 Key Value Prop: Automatic Fixes

Unlike traditional APM tools that only alert you to problems, Qorme can be configured to **automatically optimize** your application logic at runtime:

- **🔄 Automatic Prefetching**: Resolves N+1 query patterns by dynamically adjusting `prefetch_related` lookups based on actual usage predictions.
- **📉 Intelligent Deferring**: Automatically applies `defer()` to database columns that your code fetches but never accesses, drastically reducing data transfer and memory usage.

## 🔌 Integration Ecosystem

Qorme is designed to scale across multiple frameworks, starting with a deep, native integration for Django:

- **[Django Integration](https://docs.qorme.com/guides/django/setup/)**: Full-spectrum observability and auto-optimization for Django QuerySets and Templates.
- **[Future] Core Integrations**: Roadmap support for SQLAlchemy, Peewee, and Tortoise ORM.

## ✨ Feature Domains

We organize observability into modular **Domains**. You can enable or disable these modules to fit your precision requirements:

- **Database Drivers**: Low-level tracking for SQLite and Psycopg (v2 & v3).
- **Background Workers**: Automated monitoring for **[Celery](https://docs.qorme.com/guides/integrations/celery/)** tasks.
- **CMS Optimization**: Specialized rendering profiling for **[Wagtail](https://docs.qorme.com/guides/integrations/wagtail/)**.
- **Relational Integrity**: Tag-access optimization for **[Taggit](https://docs.qorme.com/guides/integrations/taggit/)**.

## 📖 Documentation

- **[Full Documentation](https://docs.qorme.com)**: Quickstart, guides, and API reference.
- **[Core Architecture](https://docs.qorme.com/understanding/architecture/)**: How the ML Store and Ingest Pipeline work.
- **[Optimization Guide](https://docs.qorme.com/guides/django/optimization/)**: Deep dive into ML-driven automatic fixes.
- **[Configuration Reference](https://docs.qorme.com/reference/configuration/)**: Every knob and tuning parameter.

## ⚖️ License

Apache 2.0. See [LICENSE](LICENSE) for details.

