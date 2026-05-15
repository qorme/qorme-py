# Events Reference

Complete reference for the event system that powers communication between Qorme domains.

## Overview

The `Events` class (`qorme.events.Events`) is a typed pub/sub event bus. Handlers are stored in a `dict[EventType, set[EventHandler]]` — meaning handlers execute in **arbitrary order** and errors in one handler don't prevent others from running.

## Event types

All events are defined in `qorme.events.EventType`:

### `CONTEXT_CREATED`

Fired when a new `QueryContext` is created (HTTP request starts, Celery task begins, management command runs).

| Parameter | Type | Description |
|:---|:---|:---|
| `context` | `QueryContext` | The newly created context |

**Producers:** `RequestTracking`, `CeleryTracking`, `CLITracking`  
**Consumers:** `Ingest` (enqueues context data)

---

### `TRACK_MODEL`

Fired the first time a Django model is seen in a tracked query.

| Parameter | Type | Description |
|:---|:---|:---|
| `model` | `type[Model]` | The Django model class |

**Producers:** `QueryTracking`  
**Consumers:** `ColumnsTracking` (patches field descriptors), `RelationTracking` (wraps `refresh_from_db`)

---

### `QUERY_STARTED`

Fired when an `ORMQuery` tracker enters its context (before SQL generation).

| Parameter | Type | Description |
|:---|:---|:---|
| `query_tracker` | `ORMQuery` | The active ORM query tracker |

**Producers:** `QueryTracking`  
**Consumers:** `TemplateTracking` (attaches template info), `RelationTracking` (attaches relation metadata)

---

### `OPTIMIZATION_REQUEST`

Fired immediately after `QUERY_STARTED`, giving ML domains a chance to modify the query.

| Parameter | Type | Description |
|:---|:---|:---|
| `query_tracker` | `ORMQuery` | The active ORM query tracker |

**Producers:** `QueryTracking`  
**Consumers:** `DeferColumns` (adds `.defer()`), `PrefetchRelations` (adds `.prefetch_related()`)

---

### `QUERY_DONE`

Fired when an `ORMQuery` tracker exits its context (iteration complete, duration recorded).

| Parameter | Type | Description |
|:---|:---|:---|
| `query_tracker` | `ORMQuery` | The completed ORM query tracker |

**Producers:** `QueryTracking`  
**Consumers:** `Ingest` (enqueues query data and rows)

---

### `NEW_INSTANCE`

Fired for each model instance yielded during QuerySet iteration.

| Parameter | Type | Description |
|:---|:---|:---|
| `instance` | `Model` | The Django model instance |
| `path` | `str` | The model label (e.g., `blog.BlogPost`) |
| `query_tracker` | `ORMQuery` | The parent query tracker |
| `select_related` | `dict \| None` | The `select_related` structure for this query |

**Producers:** `QueryTracking`  
**Consumers:** `ColumnsTracking` (attaches `__columns_accessed__` BitSet), `RelationTracking` (attaches `__rel_info__` tuple)

---

### `CONNECTION_CREATED`

Fired when a database connection is established through a tracked driver.

| Parameter | Type | Description |
|:---|:---|:---|
| `connection` | `ConnectionProxy` | The wrapped database connection |

**Producers:** `SQLiteTracking`, `PsycopgTracking`, `Psycopg2Tracking`  
**Consumers:** `Ingest` (enqueues connection metadata)

---

### `SQL_QUERY_STARTED`

Fired when a SQL query begins execution through a tracked cursor.

| Parameter | Type | Description |
|:---|:---|:---|
| `sql_query` | `SQLQueryData` | SQL text, timing, traceback, connection UID |

**Producers:** `CursorProxy` (via database driver domains)  
**Consumers:** Currently unused (reserved for timing)

---

### `SQL_QUERY_DONE`

Fired when a SQL query completes execution through a tracked cursor.

| Parameter | Type | Description |
|:---|:---|:---|
| `sql_query` | `SQLQueryData` | SQL text, timing, traceback, connection UID |

**Producers:** `CursorProxy` (via database driver domains)  
**Consumers:** `Ingest` (enqueues SQL query data)

---

### `FETCH_STARTED`

Fired when the first `fetchone()` / `fetchmany()` / `fetchall()` call is made on a tracked cursor.

| Parameter | Type | Description |
|:---|:---|:---|
| `cursor` | `CursorProxy` | The tracked cursor |

**Producers:** `CursorProxy`  
**Consumers:** Currently unused (reserved for fetch timing)

---

### `FETCH_DONE`

Fired when all rows have been fetched from a tracked cursor (or the cursor is closed).

| Parameter | Type | Description |
|:---|:---|:---|
| `cursor` | `CursorProxy` | The tracked cursor |

**Producers:** `CursorProxy`  
**Consumers:** Currently unused (reserved for fetch timing)

---

### `SQL_RESULT_HASH_COMPUTED`

Fired when a result set hash is computed for a SQL query.

| Parameter | Type | Description |
|:---|:---|:---|
| `result_hash` | `SQLResultHash` | Hash of the query result set |

**Producers:** `ResultHash` domain  
**Consumers:** `Ingest` (enqueues result hash data)

---

### `QUEUE_FLUSH`

Fired when the ingest queue flushes a batch of events to the server.

| Parameter | Type | Description |
|:---|:---|:---|
| — | — | No parameters |

**Producers:** `Queue`  
**Consumers:** Internal ingest pipeline

---

### `PROCESS_PAYLOAD`

Fired before a telemetry payload is serialized and sent, allowing domains to attach additional data.

| Parameter | Type | Description |
|:---|:---|:---|
| `payload` | `Payload` | The payload being prepared for delivery |

**Producers:** `Queue`  
**Consumers:** `ColumnsTracking` (attaches `idx_to_columns` mapping)

## Error handling

When a handler raises an exception, it's logged at `ERROR` level with full stack trace, but other handlers for the same event continue executing:

```python
def fire(self, event: EventType, *args) -> None:
    for handler in self._handlers[event]:
        try:
            handler(*args)
        except Exception:
            logger.exception(
                "Error in %s handler during %s, args=%s",
                handler, event, args, exc_info=True,
            )
```

## Execution order

Handlers are stored in a `set`, so **execution order is not guaranteed**. Do not rely on one handler running before another for the same event.
