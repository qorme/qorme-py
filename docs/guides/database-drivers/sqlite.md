# SQLite Driver

**Domain ID:** `db.sqlite`  
**Handler:** `qorme.db.integrations.sqlite.SQLiteTracking`  
**Package:** `qorme` (core)

## What it does

Wraps the Python standard library `sqlite3.connect()` function to track all SQLite connections and queries.

## Configuration

```python
QORME = {
    "domains": ["ingest", "db.sqlite"],
}
```

No additional configuration is needed.

## What's tracked

- **Connection creation** with database file path and SQLite version
- **Every SQL query** executed through `cursor.execute()` / `cursor.executemany()`
- **Fetch lifecycle** — when result rows are consumed
- **Attribution** — each SQL query is linked to the active `QueryContext` and `ORMQuery` if available

## How it works

The domain wraps `sqlite3.connect()`:

```python
def _connect_wrapper(self, wrapped, instance, args, kwargs):
    db_name = args[0] if args else kwargs["database"]
    db_info = DatabaseInfo(SQLITE_VENDOR, SQLITE_VERSION, db_name)
    return track_connection(wrapped, args, kwargs, self.deps.events, db_info)
```

The returned connection is a `ConnectionProxy` that intercepts cursor creation and tracks all SQL execution.

## When to use

- Development with Django's default SQLite backend
- Testing environments
- Small production deployments using SQLite
