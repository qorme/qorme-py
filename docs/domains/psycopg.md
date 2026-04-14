# Psycopg 3 Domain

The **Psycopg Domain** instruments the `psycopg` (v3) driver to provide deep observability into PostgreSQL queries.

## 📝 Key Functions

- **Connection Tracking**: Monitors connection lifecycle and pool usage.
- **SQL Profiling**: Capture SQL statements, execution durations, and server-side cursor usage.
- **Error Capture**: Correlates database errors with application tracebacks.
- **Performance Analysis**: Helps identify N+1 query patterns and redundant fetching.

## ⚙️ Configuration

Enabled via: `"db.psycopg"` in the `domains` list.

Settings:
- **`handler`**: `qorme.db.integrations.psycopg.PsycopgTracking`

## 🚀 Performance Impact: **Low**

Optimized for high-concurrency environments:
- **Minimal Overhead**: Direct integration with psycopg's internal wrapping mechanisms where possible.
- **Safe Capture**: Sensitive data truncation ensured by default core logic.
