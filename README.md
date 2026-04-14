# Qorme

**Observability and Automatic Optimization for ORMs.**

Qorme is a production-grade SDK that doesn't just monitor your database performance—it actively optimizes it. By combining deep framework instrumentation with real-time ML predictions, Qorme detects and automatically resolves common ORM bottlenecks like N+1 queries and redundant column fetching.

## 🚀 Key Value Prop: Automatic Fixes

Unlike traditional APM tools that only alert you to problems, Qorme can be configured to **automatically optimize** your application logic at runtime:

- **🔄 Automatic Prefetching**: Resolves N+1 query patterns by dynamically adjusting `prefetch_related` lookups based on actual usage predictions.
- **📉 Intelligent Deferring**: Automatically applies `defer()` to database columns that your code fetches but never accesses, drastically reducing data transfer and memory usage.

## 🔌 Integration Ecosystem

Qorme is designed to scale across multiple frameworks, starting with a deep, native integration for Django:

- **[Django Integration](docs/django/setup.md)**: Full-spectrum observability and auto-optimization for Django QuerySets and Templates.
- **[Future] Core Integrations**: Roadmap support for SQLAlchemy, Peewee, and Tortoise ORM.

## ✨ Feature Domains

We organize observability into modular **Domains**. You can enable or disable these modules to fit your precision requirements:

- **Database Drivers**: Low-level tracking for SQLite and Psycopg (v2 & v3).
- **Background Workers**: Automated monitoring for **[Celery](docs/contrib/core/celery.md)** tasks.
- **CMS Optimization**: Specialized rendering profiling for **[Wagtail](docs/django/contrib/wagtail.md)**.
- **Relational Integrity**: Tag-access optimization for **[Taggit](docs/django/contrib/taggit.md)**.

## 📖 documentation

- **[Core Architecture](docs/architecture.md)**: How the ML Store and Ingest Pipeline work.
- **[Optimization Guide](docs/django/optimization/index.md)**: Deep dive into ML-driven automatic fixes.
- **[Configuration Reference](docs/configuration.md)**: Every knob and tuning parameter.

## ⚖️ License

Apache 2.0. See [LICENSE](LICENSE) for details.
