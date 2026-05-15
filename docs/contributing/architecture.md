# Codebase Architecture

A contributor-focused guide to the Qorme codebase. Read this before submitting your first PR.

## Core abstractions

### `Domain` (`qorme/domain.py`)

Every tracking capability is a `Domain` subclass. The base class provides:

- `name` — Dotted identifier (e.g., `django.queries`)
- `config` — Resolved from the settings dict using `name` as path
- `deps` — Shared `Deps` container
- `wrapper` — A `Wrapper` instance scoped to this domain
- `enable()` / `disable()` — Lifecycle with rollback

Subclass hooks:
- `setup()` — Domain-specific initialization (called first)
- `install_wrappers()` — Patch functions using `self.wrapper.wrap()`
- `register_event_handlers()` — Subscribe to events using `self.deps.events.register_*()`

### `MLDomain` (`qorme/ml/domain.py`)

Extends `Domain` for optimization capabilities:

- `ml_category` — Category ID (e.g., `defer-columns`)
- `setup()` — Registers the category with `MLStore`
- `register_event_handlers()` — Subscribes to `OPTIMIZATION_REQUEST`
- `optimize(query_tracker)` — Abstract method to implement

### `Wrapper` (`qorme/utils/wrapper.py`)

All function patching goes through `Wrapper`, never raw `setattr`:

- `wrap(obj, member, wrapper_fn)` — Patch a function
- `unwrap(obj, member)` — Restore the original
- `clear()` — Remove all patches (used during `disable()`)
- Uses `weakref` to prevent memory leaks
- Raises `AlreadyWrappedError` / `DuplicateWrapperError` for safety

### `Events` (`qorme/events.py`)

Typed pub/sub bus. Key design decisions:

- `set[handler]` — no ordering guarantee
- Exception isolation — one failing handler doesn't block others
- Dedicated methods per event type — no string dispatch

### `ORMQuery` (`qorme/orm/tracking.py`)

Context manager that wraps a single ORM query execution:

- `__enter__` — fires `QUERY_STARTED` and `OPTIMIZATION_REQUEST`
- `__exit__` — fires `QUERY_DONE`, records duration
- `get_rows()` — lazily creates per-model-path row tracking structs

## Package boundaries

```
qorme (core)          ← Framework-agnostic
qorme-django          ← Django-specific, depends on qorme
qorme-sqlalchemy      ← SQLAlchemy-specific, depends on qorme (in progress)
```

The core package contains:
- All shared infrastructure (events, deps, ingest, ML store, wrapper, C extensions)
- Database driver domains (sqlite, psycopg, psycopg2)
- Celery integration (uses Celery signals, not Django)

Integration packages contain:
- Framework-specific domains
- Default configuration with handler class paths

## Data flow

```
User code → ORM (Django/SQLAlchemy)
                    ↓ (wrapt patches)
              QueryTracking domain
                    ↓ (events)
         ┌──────────┼──────────┐
     Columns    Relations   Template
         └──────────┼──────────┘
                    ↓ (events)
                 Ingest
                    ↓ (queue → batch → compress)
               HTTP/2 POST
                    ↓
              Qorme Server
```

## Adding new functionality

| Want to... | Start here |
|:---|:---|
| Add a new tracking domain | [Adding a Domain](adding-a-domain.md) |
| Add a new event type | Add to `EventType` enum, add methods to `Events` class |
| Support a new database driver | Subclass `Domain`, wrap the driver's `connect()` |
| Support a new ORM | Create a new integration package with ORM-specific domains |
| Add a new ML optimization | Subclass `MLDomain`, implement `optimize()` |
