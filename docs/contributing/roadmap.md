# Roadmap

Current integration roadmap for the Qorme SDK. Items are ranked by potential user-base reach, implementation effort, and strategic coverage.

## Active development

### SQLAlchemy / SQLModel → `qorme-sqlalchemy`

- Widest adoption in the Python ecosystem (Flask, FastAPI, Pyramid, CLI scripts)
- Column tracking via SQLAlchemy's `InstanceState` and descriptor wrapping
- Immediately unlocks SQLModel support

**Status:** 🚧 In progress

## Planned integrations

### FastAPI & Flask request middleware → `qorme-fastapi` / `qorme-flask`

- Adds request-level `QueryContext` correlation for modern web APIs
- Implementation: small ASGI/WSGI middleware that creates `QueryContext` on request start
- ~50 lines of middleware each

### Async-native ORMs → `qorme-gino`, `qorme-ormar`

- Covers popular async stacks (PostgreSQL/asyncpg, Pydantic-based Ormar)
- Can reuse most of the SQLAlchemy logic or thin wrappers around their event systems

### Generic DB-API 2.0 wrapper → `qorme-dbapi`

- Safety-net for projects using raw SQL through any DB-API 2.0 compliant driver
- Monkey-patch `cursor.execute` / `cursor.executemany` to emit Qorme query events

### Pandas / Jupyter → `qorme-pandas`

- Instruments `pd.read_sql()` in notebooks and production pipelines (Airflow, Prefect)
- Surfaces query cost and annotates with notebook metadata

### Alembic migration hooks → `qorme-alembic`

- Surfaces long-running migrations or locking issues
- Hook into Alembic's `before_revision_execute` / `after_revision_execute`

### GraphQL layers → `qorme-graphene` / `qorme-strawberry`

- Maps GraphQL resolver paths to SQL queries
- Helps diagnose resolver-level N+1 problems

## Future: Cross-language

Longer-term, mirror a subset of Qorme core in other runtimes:

- **Go** — Hook the `database/sql` `Connector` interface
- **Node.js** — Patch popular drivers (`pg`, `mysql2`) via instrumentation hooks

## Suggested execution order

| Phase | Deliverable | Effort | Impact |
|:---|:---|:---|:---|
| 1 | `qorme-sqlalchemy` | Moderate | Highest |
| 2 | `qorme-fastapi` / `qorme-flask` | Low | High |
| 3 | `qorme-gino` / `qorme-ormar` | Low-Moderate | Medium |
| 4 | `qorme-dbapi` | Low | Broad |
| 5 | `qorme-pandas` / `qorme-alembic` | Low | Niche |
| 6 | `qorme-graphene` / `qorme-strawberry` | Moderate | Targeted |
| 7 | Cross-language prototypes | High | Strategic |
