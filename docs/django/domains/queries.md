# Django Queries Domain: ORM Intelligence

The **Django Queries Domain** provides deep observability into how your application interacts with the database via the Django ORM. It goes beyond simple SQL logging to identify high-level ORM patterns.

## 📝 Key Functions

- **QuerySet Methodology**: Uses Django's `connection.execute_wrapper` and patches `QuerySet` methods (`exists`, `count`, `__iter__`) to capture query intent.
- **N+1 Identification**: Automatically detects loop-driven query surges by cross-correlating tracebacks with repeated SQL patterns.
- **Result Fingerprinting**: Employs `xxhash` to hash the results of queries, allowing Qorme to detect redundant fetches (queries returning identical data within the same request).

## ⚙️ Configuration

Enabled via: `"django.queries"` in the `domains` list.

### Configuration Keys (`django.queries`)

| Key | Type | Description |
| :--- | :--- | :--- |
| `apps_to_include` | `list` | Only track models belonging to these app labels. |
| `apps_to_exclude` | `list` | Explicitly ignore these apps. |
| `models_to_include` | `list` | Specific model labels to track. |
| `models_to_exclude` | `list` | Specific model labels to ignore. |

> [!IMPORTANT]
> `include` and `exclude` keys are mutually exclusive. Attempting to provide both for the same scope will raise a `ConfigurationError`.

## 📐 Implementation Details

- **Instrumentation**: Uses `wrapt` for transparent patching of `ModelIterable` and its variants (`ValuesIterable`, etc.).
- **Query Attribution**: Every query is associated with a `RowType` (Model, Dict, Scalar) to help differentiate between full object fetches and efficient value lookups.

## 🚀 Performance Impact: **Low**

- **Wait-Free Capture**: Telemetry collection is designed to be constant-time.
- **Optimized Hashing**: Fingerprinting is performed using system-level hashing primitives.
