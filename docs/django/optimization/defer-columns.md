# Automatic Column Deferring

The **Defer Columns Domain** is a self-healing module that automatically optimizes Django QuerySets by deferring the loading of fields that are predicted to be unused.

## 📝 Key Functions

- **Query Interception**: The domain listens for queries being prepared by the Django ORM.
- **ML Prediction**: For every model in the query (including joined models via `select_related`), it consults the `MLStore` to predict which fields are unlikely to be accessed.
- **Dynamic Deferral**: If confident, it calls `query.add_deferred_loading()` on the Django query object before the SQL is generated.

## ⚙️ Configuration

Enabled via: `"defer_columns"` in the `domains` list. Requires the `"ml"` domain to be enabled.

### Optimization Logic (Code Audit)

- **Model Only**: Only applies to queries returning model instances (`RowType.MODEL`).
- **Safety**: Does not modify queries that already have explicit `.defer()` or `.only()` calls applied by the developer.
- **Recursive**: Can defer columns on related models that were fetched via `select_related`.

## 📐 Internal Implementation

The domain subclasses `MLDomain` and overrides `optimize(query_tracker)`. It iterates through all paths in the query (the primary model and its joined relations) and fetches a prediction for each.

## 🚀 Performance Impact: **Optimization**

- **Runtime Overhead**: Adds a negligible latency to query preparation (single-digit milliseconds) to fetch predictions from the in-memory store.
- **Database Benefit**: Reduction in SQL `SELECT` payload size, memory usage on the DB server, and Python object hydration time.
