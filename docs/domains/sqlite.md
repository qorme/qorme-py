# SQLite Domain

The **SQLite Domain** provides automated instrumentation for the Python built-in `sqlite3` driver. It captures query metrics and performance data without requiring changes to your database initialization code.

## 📝 Key Functions

- **Query Capture**: Intercepts `execute()` and `executemany()` calls.
- **Timing**: Measures the exact execution time of every query.
- **Traceback Extraction**: Captures the application call stack to identify where queries originate.
- **Parameter Hashing**: Hashes query parameters to detect patterns without storing sensitive data.

## ⚙️ Configuration

Enabled via: `"db.sqlite"` in the `domains` list.

Settings are inherited from the core DB handler:
- **`handler`**: `qorme.db.integrations.sqlite.SQLiteTracking`

## 🚀 Performance Impact: **Low**

- **Patching**: Uses `wrapt` for transparent, high-performance function wrapping.
- **Overhead**: Minimum impact on query execution time. Traceback capture is optimized using system-level caching.
