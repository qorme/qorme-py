# Global Configuration Reference

The Qorme SDK is configured through a unified dictionary, typically provided via a framework integration (e.g., the `QORME` dictionary in Django's `settings.py`).

## 🧱 Core Settings (`QORME`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `active` | `bool` | `True` | Master kill-switch. If `False`, no instrumentation is applied. |
| `domains` | `list` | `[]` | **Essential.** List of domain identifiers to enable (e.g., `["ingest", "django.queries"]`). |
| `deps` | `dict` | `{}` | Configuration for internal dependencies (Networking, Workers). |

---

## 📦 Dependency Configuration (`deps`)

### `http_client`
Configures the outgoing telemetry and incoming SSE updates.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dsn` | `str` | `""` | **Required.** Your project's Data Source Name. |
| `request_timeout` | `float` | `60.0` | Timeout for the batch flusher requests. |
| `http2` | `bool` | `True` | Use HTTP/2 for better performance. |
| `verify_ssl` | `bool` | `True` | Set to `False` for local development. |
| `retry.attempts` | `int` | `5` | Number of retry attempts on network failure. |

### `ml_store`
Tuning for the real-time optimization client.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `sse.url_path` | `str` | `ml/updates/` | API endpoint for receiving model updates. |
| `sse.read_timeout` | `float` | `90.0` | Inactivity timeout for the SSE stream. |

---

## 🛠️ Environment Variables

Qorme supports overrides via environment variables. These variables take precedence over code-based configuration.

- **`QORME_ACTIVE`**: Set to `False` or `0` to force-disable the entire SDK.
- **`QORME_HTTP_CLIENT_DSN`**: Provide the DSN without modifying code.
- **`QORME_INGEST_QUEUE_MAX_SIZE`**: Override the default event queue capacity.

> [!NOTE]
> All configuration keys within the `QORME` dictionary can be overridden by transforming them to uppercase and prefixing with `QORME_`. For example, `deps.http_client.dsn` becomes `QORME_DEPS_HTTP_CLIENT_DSN`.
