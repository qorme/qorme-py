# Django Relations Domain: Dependency Mapping

The **Django Relations Domain** analyzes how your application traverses model relationships (ForeignKeys, Many-to-Many, etc.) and identifies inefficient patterns.

## 📝 Key Functions

- **Traversal Monitoring**: Tracks every access to a related object via the Django ORM.
- **N+1 Pattern Detection**: Flags cases where related objects are fetched one-by-one instead of using `select_related` or `prefetch_related`.
- **Depth Analysis**: Profiles the "depth" of relationship access (e.g., `person.company.address.city`) to suggest join optimizations.

## ⚙️ Configuration

Enabled via: `"django.relations"` in the `domains` list.

## 📐 Implementation Details

This domain attaches to the `on_new_instance` event from the `django.queries` domain. It recursively analyzes the `select_related` dictionary and comparing it against actual relationship access map.

## 🚀 Performance Impact: **Medium**

- **Pattern Analysis**: Requires tracking object-to-object relationships at runtime.
- **Optimized for Dev**: Primarily used to generate insights for the **Automatic Prefetching** engine.
