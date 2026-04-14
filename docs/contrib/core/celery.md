# Celery Domain: Background Task Observability

The **Celery Domain** provides automated tracking for background tasks. It is a "core contrib" module because it is designed to work across multiple frameworks and database backends.

## ⚙️ How it works

Qorme hooks into Celery's signal system to monitor task lifecycles:

1. **`task_prerun`**: Qorme starts a new `QueryContext` linked to the `task_id`. This ensures that all database queries triggered by the task are correctly attributed.
2. **`task_postrun`**: Qorme closes the context and prepares the telemetry for ingestion.

## 🛠️ Configuration

Enable via: `"celery.tracking"` in the `domains` list.

### `celery` configuration keys

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ignore_tasks` | `list` | `[]` | List of task names (dotted paths) to exclude from tracking. |

## 📐 Implementation Details

The task tracker uses `qorme.context.tracking.QueryContext` to create a scoped execution block. This context allows Qorme to:
- Capture the total task execution time.
- Attribute SQL queries to the task.
- Detect if a background task is triggering N+1 patterns or redundant fetches.

## 🚀 Performance Impact: **Low**

- **Signal Driven**: Minimal overhead by using Celery's built-in hooks.
- **Context Injection**: Uses thread-local context management to avoid data leaks between task executions.
