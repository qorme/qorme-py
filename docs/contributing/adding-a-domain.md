# Adding a Domain

Step-by-step guide to creating a new tracking domain for Qorme.

## 1. Create the domain class

```python title="src/qorme/contrib/mylib/tracking.py"
from qorme.domain import Domain


class MyLibTracking(Domain):
    name = "mylib.tracking"

    __slots__ = ()

    def setup(self):
        """Initialize domain-specific state."""
        pass

    def install_wrappers(self):
        """Patch functions to intercept calls."""
        self.wrapper.wrap(some_module, "some_function", self._wrapper_fn)

    def register_event_handlers(self):
        """Subscribe to events from other domains."""
        self.deps.events.register_query_started_handler(self._on_query_started)

    def unregister_event_handlers(self):
        """Unsubscribe from events. Must mirror register_event_handlers."""
        self.deps.events.unregister_query_started_handler(self._on_query_started)

    def _wrapper_fn(self, wrapped, instance, args, kwargs):
        """wrapt-style wrapper: (wrapped, instance, args, kwargs)."""
        # Pre-processing
        result = wrapped(*args, **kwargs)
        # Post-processing
        return result

    def _on_query_started(self, query_tracker):
        """Event handler for QUERY_STARTED events."""
        pass
```

### Key rules

- **Always define `__slots__`** — domains are long-lived; avoid `__dict__` overhead
- **Always implement `unregister_event_handlers`** — must be the exact inverse of `register_event_handlers`
- **Use `self.wrapper.wrap()`** — never raw `setattr`. The `Wrapper` class handles cleanup.
- **The `name` must be unique** and follow dotted convention

## 2. Register the default configuration

Add an entry to the appropriate defaults file:

```python title="src/qorme/defaults.py"
QORME_SETTINGS = {
    ...
    "mylib": {
        "tracking": {
            "handler": "qorme.contrib.mylib.tracking.MyLibTracking",
            # Add any domain-specific config keys here
        },
    },
}
```

The `handler` key is required — it's the fully-qualified class path that `TrackingManager` uses to instantiate the domain.

## 3. Enable in configuration

Users enable the domain by adding its name to the `domains` list:

```python
QORME = {
    "domains": [
        "mylib.tracking",
    ],
}
```

The `TrackingManager` resolves `"mylib.tracking"` to `config.mylib.tracking`, reads the `handler` key, imports the class, and calls `enable()`.

## 4. Write tests

```python title="tests/contrib/mylib/test_tracking.py"
from qorme.contrib.mylib.tracking import MyLibTracking


def test_domain_enables_and_disables():
    domain = create_domain(MyLibTracking, config={})
    assert domain.enable()
    assert domain.disable()


def test_wrapper_intercepts_call():
    domain = create_domain(MyLibTracking, config={})
    domain.enable()

    # Call the wrapped function
    result = some_module.some_function()

    # Assert the wrapper modified behavior
    assert ...

    domain.disable()
```

## 5. Document

Add the domain to:
- [Domain Registry](../reference/domains.md) — with domain ID, handler, and purpose
- [Configuration Reference](../reference/configuration.md) — with all config keys
- A new guide page if the integration is substantial

## For ML optimization domains

Subclass `MLDomain` instead:

```python
from qorme.ml.domain import MLDomain
from qorme.ml.instance import MLInstance


class MyOptimization(MLDomain):
    name = "mylib.optimization"
    ml_category = "my-optimization"  # Must match server ML pipeline

    __slots__ = ()

    def optimize(self, query_tracker):
        """Called on OPTIMIZATION_REQUEST when MLStore is connected."""
        ml_model = self.get_model(query_tracker.data.model)
        if not ml_model:
            return

        prediction = ml_model.predict(MLInstance("", query_tracker))
        if not prediction:
            return

        # Modify the query based on prediction
        ...
```

The `MLDomain` base class handles:
- Registering the `ml_category` with `MLStore` during `setup()`
- Subscribing to `OPTIMIZATION_REQUEST` events
- Checking `ml_store.connected()` before calling `optimize()`
