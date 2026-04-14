# Celery Domain

The **Celery Domain** provides automated tracking for background tasks. It allows you to see exactly what happens inside a Celery worker, including the database queries it triggers.

## 📝 Key Functions

- **Task Monitoring**: Captures the start and end of every Celery task.
- **Query Attribution**: Automatically links all database queries triggered within a task to that specific `task_id`.
- **Performance Profiling**: Measures task execution time and overhead.
- **Failures Capture**: Tracks task errors and correlates them with the task context and database state.

## ⚙️ Configuration

Enabled via: `"celery.tracking"` in the `domains` list.

### `celery` Settings

| Setting | Default | Description |
| :--- | :--- | :--- |
| `ignore_tasks` | `[]` | List of task names to exclude from tracking. |

## 🚀 Performance Impact: **Low**

- Hooks into Celery's built-in signals (`task_prerun`, `task_postrun`).
- Minimal overhead per task execution.
