# Celery Integration

**Domain ID:** `celery.tracking`  
**Handler:** `qorme.contrib.celery.tracking.CeleryTracking`  
**Package:** `qorme` (core)

## What it does

Tracks database queries executed inside Celery tasks by creating a `QueryContext` for each task execution. This gives you the same query attribution and optimization capabilities for background jobs that you get for HTTP requests.

## Setup

Add the domain to your config:

```python title="settings.py"
QORME = {
    "domains": [
        "ingest",
        "db.psycopg",
        "django.queries",
        "celery.tracking",  # ← Add this
    ],
}
```

No Celery-specific configuration is required. The domain connects to Celery's built-in signals — it doesn't wrap any Celery internals.

## How it works

The domain hooks into two Celery signals:

| Signal | Action |
|:---|:---|
| `task_prerun` | Creates a `QueryContext` with `type=ContextType.TASK` and the task name and ID |
| `task_postrun` | Closes the `QueryContext` by matching the task ID |

Any ORM query executed during the task is automatically attributed to this context.

```python
# Your Celery task — no changes needed
@app.task
def send_newsletter(campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)
    for subscriber in campaign.subscribers.all():
        send_email(subscriber.email, campaign.body)
```

Qorme will track:
- The `Campaign.objects.get()` query
- The `campaign.subscribers.all()` query
- Any N+1 patterns if `subscriber` has related objects accessed in `send_email`

All attributed to the `send_newsletter` task with the specific `task_id`.

## Ignoring noisy tasks

Some tasks run frequently and don't involve meaningful database queries:

```python title="settings.py"
QORME = {
    "celery": {
        "tracking": {
            "ignore_tasks": [
                "celery.backend_cleanup",
                "myapp.tasks.heartbeat",
            ],
        },
    },
}
```

Ignored tasks won't create a `QueryContext`, so their queries aren't tracked.

## Django integration

Since `celery.tracking` is in the core `qorme` package (not `qorme-django`), it works with any framework. When used alongside Django, you get the full observability and optimization stack for background tasks — including auto-deferring and auto-prefetching.

!!! tip "Celery workers share the same Django settings"
    If you start your Celery worker with `celery -A myproject worker`, Django settings (including `QORME`) are loaded automatically via the `QormeDjangoConfig.ready()` hook.
