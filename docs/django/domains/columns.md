# Django Columns Domain: Efficiency Profiling

The **Django Columns Domain** provides precise detection of "Unused Columns"—fields that your application fetches from the database but never accesses in code. This is the foundational data used for **Automatic Deferring**.

## 📝 Key Functions

- **Access Tracking**: Automatically patches Django field descriptors to track which attributes are read on every model instance.
- **Bitset-Based Capture**: Uses high-performance bitsets (C-optimized) to record access maps with minimal memory footprint.
- **Load Comparison**: Compares the data requested in the SQL query against the attributes actually accessed during the request lifecycle.

## ⚙️ Configuration

Enabled via: `"django.columns"` in the `domains` list.

### Configuration Keys (`django.columns`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `known_descriptors` | `set` | `(internal)` | A set of descriptor class paths to instrument. Users can add custom third-party descriptors here if they aren't being tracked. |

## 📐 Implementation Details

This domain uses a sophisticated descriptor wrapping technique:
- **`FieldDescriptor`**: Wraps standard fields.
- **`DeferredAttributeDescriptor`**: Wraps fields marked as `.defer()` to ensure they aren't doubly instrumented.
- **Bitset Lifecycle**: A bitset is attached to every model instance via `__columns_accessed__` upon instantiation.

## 🚀 Performance Impact: **Medium**

- **Overhead**: Patching every field access adds a small constant-time overhead.
- **Recommendation**: Highly effective in **Development** and **Staging** phases to optimize your ORM profile before production.
