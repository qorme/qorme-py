# Psycopg 3

**Domain ID:** `db.psycopg`  
**Handler:** `qorme.db.integrations.psycopg.PsycopgTracking`  
**Package:** `qorme` (core)

## What it does

Wraps `psycopg.connect()` to track all PostgreSQL connections and queries made through the modern psycopg v3 driver.

## Configuration

```python
QORME = {
    "domains": ["ingest", "db.psycopg"],
}
```

No additional configuration is needed.

## What's tracked

- **Connection creation** with database name and PostgreSQL server version
- **Every SQL query** executed through `cursor.execute()` / `cursor.executemany()`
- **Fetch lifecycle** — when result rows are consumed via `fetchone()`, `fetchmany()`, `fetchall()`
- **Attribution** — each SQL query is linked to the active `QueryContext` and `ORMQuery`

## How it works

The domain wraps `psycopg.connect()`:

```python
def _connect_wrapper(self, wrapped, instance, args, kwargs):
    db_info = DatabaseInfo(POSTGRESQL_VENDOR, "", extract_db_name(args, kwargs))
    proxy = track_connection(wrapped, args, kwargs, self.deps.events, db_info)
    proxy.set_db_version(get_db_version(proxy.__wrapped__))
    return proxy
```

Database name is extracted from either DSN strings (`dbname=...`), URLs (`postgresql://host/dbname`), or keyword arguments (`dbname=` / `database=`).

## When to use

- Django 4.2+ with the default PostgreSQL backend
- Any project using `psycopg` (v3) directly
- Recommended over `db.psycopg2` for new projects
