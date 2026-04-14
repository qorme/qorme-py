# Automated Optimization (Self-Healing)

The core selling point of Qorme is its ability to not just detect issues, but **automatically resolve them** at runtime using machine learning.

## 🧠 The Optimization Engine

When you enable optimization domains, Qorme creates a real-time feedback loop:
1. **Telemetry**: Domains like `django.queries` and `django.columns` collect data on your actual ORM usage patterns.
2. **Analysis**: The Qorme server analyzes this data and trains models specific to your project.
3. **Synchronization**: These models are synced back to your SDK's local `MLStore` in real-time.
4. **Interception**: When a QuerySet is executed, Qorme intercepts the query and applies the optimized parameters (e.g., adding `defer()` or `prefetch_related()`) based on the ML predictions.

## 🚀 Available Optimizers

Qorme currently supports two primary types of automatic optimization:

### 1. [Automatic Column Deferring](defer-columns.md)
**Resolves**: High memory usage and slow data transfer caused by fetching large or unused columns.
**Action**: Dynamically applies `.defer()` to fields that are predicted to be unused in the current context.

### 2. [Automatic Relationship Prefetching](prefetch-relations.md)
**Resolves**: N+1 query patterns.
**Action**: Dynamically applies `.prefetch_related()` to relationships that are predicted to be accessed later in the request lifecycle.

---

## ⚙️ How to Enable

To use these features, ensure the `ml` core domain is active and then add the individual optimizers to your `domains` list:

```python
QORME = {
    "domains": [
        "ingest",
        "ml",
        "defer_columns",
        "prefetch_relations",
    ],
    ...
}
```
