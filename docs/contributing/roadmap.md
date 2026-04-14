# Qorme Integration Roadmap

This document lists the most valuable new integrations to pursue after Django, Tortoise, Peewee and Celery.  Items are ranked by:

1. Potential user-base reach  
2. Implementation effort (re-using existing Qorme plumbing)  
3. Strategic coverage (sync vs async, web vs batch, Python vs other runtimes)

---

## 1 · SQLAlchemy / SQLModel  →  `qorme-sqlalchemy`

* Widest adoption in the Python ecosystem (Flask, FastAPI, Pyramid, Click scripts, etc.).  
* Straightforward to implement via SQLAlchemy Core event hooks (`before_cursor_execute`, `after_cursor_execute`).  
* Immediately unlocks SQLModel support almost for free.

---

## 2 · FastAPI & Flask request middleware  →  `qorme-fastapi` / `qorme-flask`

* Adds "request-ID → query-batch" correlation for modern web APIs.  
* Implementation: small ASGI / WSGI middleware layers that call `TrackingManager.install()` early and attach request metadata to Qorme's context.

---

## 3 · Async-native ORMs  →  `qorme-gino`, `qorme-ormar`

* Covers popular async stacks (PostgreSQL/asyncpg, Pydantic-based Ormar).  
* Can reuse most of the SQLAlchemy logic or thin wrappers around their own event systems.

---

## 4 · Generic DB-API 2.0 wrapper  →  `qorme-dbapi`

* "Safety-net" for projects using raw SQL through libraries like `psycopg2`, `mysql-connector`, or standard `sqlite3`.  
* Monkey-patch cursor `execute` / `executemany` to emit Qorme query events.

---

## 5 · Pandas / Jupyter helper  →  `qorme-pandas`

* Analysts often call `pd.read_sql()` in notebooks and production pipelines (Airflow, Prefect).  
* Patch `pandas.io.sql.execute_sql` to measure query cost and annotate with notebook metadata.

---

## 6 · Alembic migration hooks  →  `qorme-alembic`

* Surfaces long-running migrations or locking issues.  
* Hook into Alembic's `before_revision_execute` / `after_revision_execute` events.

---

## 7 · GraphQL layers  →  `qorme-graphene` / `qorme-strawberry`

* Maps GraphQL resolver paths to SQL queries, helping diagnose N+1 problems.  
* Thin wrapper around execution context to push resolver information into Qorme.

---

## 8 · Cross-language seeds

Longer-term, mirror a subset of Qorme core in other runtimes so polyglot stacks can still feed the central dashboard.

* **Go** – hook the `database/sql` `Connector` interface.  
* **Node.js** – patch popular drivers (`pg`, `mysql2`) via their instrumentation hooks.

---

### Suggested Order of Execution

| Phase | Deliverable                         | Notes                                    |
|-------|-------------------------------------|------------------------------------------|
| 1     | `qorme-sqlalchemy`                  | Highest impact, moderate effort          |
| 2     | `qorme-fastapi` and/or `qorme-flask`| ~50 lines of middleware                  |
| 3     | `qorme-gino`, `qorme-ormar`         | Reuse async event logic                  |
| 4     | `qorme-dbapi`                       | Minimal patch, broad coverage            |
| 5-6   | pandas, Alembic                     | Niche but high-value observability       |
| 7     | GraphQL extensions                  | Targets teams suffering from N+1 queries |
| 8     | Cross-language prototypes           | Starts widening moat beyond Python       | 