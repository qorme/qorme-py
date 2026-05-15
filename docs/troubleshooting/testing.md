# Testing with Qorme

How to handle Qorme in your test suite.

## Disabling Qorme in tests

The simplest approach — disable Qorme entirely during testing:

```python title="settings/test.py"
QORME = {
    "active": False,
}
```

Or via environment variable:

```bash
QORME_ACTIVE=false pytest
```

When inactive, `TrackingManager.install()` returns immediately. No domains, no wrappers, no overhead.

## Running tests with Qorme enabled

If you want to test Qorme's behavior (e.g., verifying that optimizations are applied), keep it active but configure it for testing:

```python title="settings/test.py"
QORME = {
    "active": True,
    "domains": [
        "django.queries",
        "django.requests",
        "django.columns",
        "django.relations",
        # Don't include "ingest" — no server to send to
        # Don't include "db.*" — avoid wrapping test DB connections
    ],
    "deps": {
        "http_client": {
            "dsn": "",  # No server connection
        },
    },
}
```

!!! warning "Don't include `ingest` without a server"
    Without a reachable server, the ingest domain's queue will fill up and eventually start dropping events. While this is harmless, it generates warning logs.

## Testing optimization domains

To test `defer_columns` or `prefetch_relations`, you need to mock the `MLStore`:

```python
from unittest.mock import patch, MagicMock

def test_defer_columns_applies():
    """Verify that defer_columns modifies the queryset."""
    mock_model = MagicMock()
    mock_model.predict.return_value = MagicMock(
        predicted=...,  # encoded target
        data={},
    )

    with patch.object(ml_store, 'get_model', return_value=mock_model):
        with patch.object(ml_store, 'connected', return_value=True):
            posts = list(BlogPost.objects.all())
            # Assert that deferred loading was applied
```

## Test isolation

Qorme uses `ContextVar` for tracking state, which means:

- Each test gets its own context (if using Django's `TestCase` or `TransactionTestCase`)
- No cross-test contamination from `QueryContext` state
- The `TrackingManager` singleton persists across tests (it's process-level)

If you need to reset Qorme between tests:

```python
from qorme.manager import TrackingManager

class MyTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        TrackingManager.uninstall()
        super().tearDownClass()
```

## Asserting query behavior

Qorme doesn't replace Django's `assertNumQueries`. Use them together:

```python
class PostViewTest(TestCase):
    def test_post_list_queries(self):
        # Django's built-in assertion still works
        with self.assertNumQueries(2):  # 1 for posts + 1 for prefetch
            response = self.client.get("/posts/")
```

Qorme's tracking is additive — it wraps Django's internals but doesn't change query behavior (unless optimization domains modify the queryset).
