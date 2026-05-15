# Psycopg 2

**Domain ID:** `db.psycopg2`  
**Handler:** `qorme.db.integrations.psycopg2.Psycopg2Tracking`  
**Package:** `qorme` (core)

## What it does

Wraps `psycopg2.connect()` to track all PostgreSQL connections and queries made through the legacy psycopg2 driver.

## Configuration

```python
QORME = {
    "domains": ["ingest", "db.psycopg2"],
}
```

No additional configuration is needed.

## What's tracked

Same as [Psycopg 3](psycopg3.md):

- Connection creation with database name and server version
- Every SQL query with timing and traceback
- Fetch lifecycle
- Attribution to `QueryContext` and `ORMQuery`

## When to use

- Legacy Django projects using `psycopg2` or `psycopg2-binary`
- Projects that haven't migrated to psycopg v3

!!! tip "Consider migrating to psycopg v3"
    Psycopg v3 is the actively maintained PostgreSQL driver and the default for Django 4.2+. If you're starting a new project, use `db.psycopg` instead.
