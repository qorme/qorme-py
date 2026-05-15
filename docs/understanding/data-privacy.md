# Data Privacy

What data Qorme collects, how it's transmitted, and what stays in your infrastructure.

## What's collected

### Telemetry (SDK → Server)

| Data category | What's included | What's NOT included |
|:---|:---|:---|
| **Query metadata** | Model label, query type, row type, duration, result hash | Raw SQL parameters, user data, row contents |
| **SQL text** | Raw SQL statements (e.g., `SELECT id, title FROM blog_post WHERE ...`) | Bind parameter values |
| **Tracebacks** | File paths, function names, line numbers from your application code | Source code content |
| **Context metadata** | View name, URL path, HTTP method, Celery task name | Request body, headers, cookies, session data |
| **Column access** | Bitmaps indicating which columns were accessed | Column values |
| **Relation metadata** | Relationship field names, traversal depth | Related object data |
| **Template info** | Template filename, line number, tag content | Rendered template output |
| **Connection metadata** | Database vendor, version, database name | Connection credentials |

### ML predictions (Server → SDK)

| Data category | What's included |
|:---|:---|
| **Model updates** | Decision tree parameters, feature names, prediction thresholds |
| **Category** | `defer-columns`, `prefetch-relations` |
| **Model labels** | Django model names (e.g., `blog.BlogPost`) |

## What's NOT collected

Qorme explicitly does **not** collect:

- ❌ Row data (field values, user records, PII)
- ❌ SQL bind parameters (query values like `WHERE email = ?`)
- ❌ Request/response bodies
- ❌ Authentication tokens, cookies, or session data
- ❌ Source code content (only file paths and line numbers)
- ❌ Environment variables or secrets

## Data transmission

### Encryption

All telemetry is transmitted over **HTTPS (TLS 1.2+)** via HTTP/2. The SDK uses `httpx` with SSL verification enabled by default.

### Compression

Payloads are compressed using `isal` (hardware-accelerated) or `gzip` before transmission, reducing both bandwidth and exposure surface.

### Serialization

Data is serialized using `msgspec.msgpack` (binary format), not human-readable JSON. This is a performance optimization, not a security measure — the data is structured, not encrypted.

## Self-hosted deployment

For maximum data privacy, self-host the Qorme server. In this configuration:

- All telemetry stays within your infrastructure
- No data leaves your network
- You control the database, retention, and access

See the [Server Setup guide](../guides/server-setup.md) for self-hosting instructions.

## SQL text handling

!!! warning "SQL text is collected"
    Qorme collects raw SQL statements for query analysis and deduplication. While bind parameters are **not** included, the SQL structure itself may contain table and column names that reflect your data model.

    If this is a concern, consider self-hosting the server so SQL text never leaves your infrastructure.

## Retention

Data retention is controlled by the Qorme server:

- **Qorme Cloud** — Retention policies are documented in the service terms
- **Self-hosted** — You control retention via TimescaleDB's built-in data lifecycle policies
