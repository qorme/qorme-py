# Automatic Relationship Prefetching

The **Prefetch Relations Domain** is a self-healing module that automatically identifies and resolves potential N+1 query patterns before they happen.

## 📝 Key Functions

- **Pattern Prediction**: As a QuerySet is prepared, Qorme predicts which related models (Many-to-One and Many-to-Many) will be accessed during this request lifecycle.
- **Dynamic Prefetching**: Automatically injects relationship paths into the QuerySet's `prefetch_related` list.
- **Conflict Resolution**: Merges predicted prefetch paths with any paths manually specified by the developer to ensure no loss of intentional logic.

## ⚙️ Configuration

Enabled via: `"prefetch_relations"` in the `domains` list. Requires the `"ml"` domain to be enabled.

### Optimization Logic (Code Audit)

- **Model Only**: Only applies to queries returning model instances (`RowType.MODEL`).
- **Recursive Expansion**: The engine can predict deep relationship trees (e.g., `author -> posts -> tags`) in a single pass.
- **Safety**: Uses `qs._prefetch_related_lookups` to ensure it only adds to existing user-defined prefetches without overriding complex `Prefetch()` objects.

## 📐 Internal Implementation

This domain uses a `while queue` pattern to traverse the model structure and fetch predictions for every related field. It stops when the ML model predicts no further relations are needed or when the relationship depth limit is reached.

## 🚀 Performance Impact: **Optimization**

- **Runtime Overhead**: Adds a minor latency to QuerySet creation for prediction lookups.
- **Database Benefit**: Drastically reduces the total number of database roundtrips by consolidating multiple individual fetches into a single `IN` query.
