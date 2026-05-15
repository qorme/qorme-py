# Database Drivers

Qorme instruments database drivers at the connection and cursor level to capture raw SQL queries, timing, and connection lifecycle events.

These domains operate independently of framework-level tracking (like `django.queries`) and provide SQL-level visibility regardless of which ORM — or no ORM — you're using.

## How driver tracking works

When you enable a database driver domain (e.g., `db.psycopg`), Qorme wraps the driver's `connect()` function. Every connection returned is a transparent `ConnectionProxy` that:

1. Fires a `CONNECTION_CREATED` event with database metadata (vendor, version, name)
2. Returns `CursorProxy` objects from `.cursor()` that track:
    - `execute()` / `executemany()` — records SQL text, execution time, traceback
    - `fetchone()` / `fetchmany()` / `fetchall()` — tracks fetch lifecycle
    - Links each SQL query to the active `ORMQuery` and `QueryContext` if available

The proxies are implemented with `wrapt.ObjectProxy`, making them fully transparent — your code sees a normal connection and cursor.

## Available drivers

| Domain | Driver | Minimum version |
|:---|:---|:---|
| [`db.sqlite`](sqlite.md) | `sqlite3` (stdlib) | Python 3.10+ |
| [`db.psycopg`](psycopg3.md) | `psycopg` (v3) | psycopg 3.0+ |
| [`db.psycopg2`](psycopg2.md) | `psycopg2` | psycopg2 2.9+ |

## Choosing a driver domain

Pick the domain that matches the driver your project uses. For Django, check your `DATABASES` setting:

```python title="settings.py"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # → db.psycopg or db.psycopg2
        # "ENGINE": "django.db.backends.sqlite3",   # → db.sqlite
    }
}
```

!!! tip "Django 4.2+ defaults to psycopg v3"
    If you installed `psycopg` (not `psycopg2`), use `db.psycopg`. If you're on the legacy `psycopg2-binary`, use `db.psycopg2`.
