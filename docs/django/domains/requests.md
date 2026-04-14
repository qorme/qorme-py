# Django Requests Domain: View Performance

The **Django Requests Domain** instruments the HTTP lifecycle of your application, providing the foundational context for all other tracking domains.

## 📝 Key Functions

- **Request Context**: Every incoming HTTP request is wrapped in a dedicated `QueryContext`. This allows Qorme to attribute all database queries and template rendering events to a specific request.
- **Timing & Status**: Measures the full latency of the view and records the resulting HTTP status code.
- **Middleware Integration**: Automatically injects a lightweight middleware into the Django stack to handle the start and end of the tracking lifecycle.

## ⚙️ Configuration

Enabled via: `"django.requests"` in the `domains` list.

## 📐 Implementation Details

This domain uses Django's `request_started` and `request_finished` signals, alongside a custom middleware class. It captures:
- Request Path & Method
- View Func / Class
- Resolving app/url_name

## 🚀 Performance Impact: **Negligible**

- **Signal Driven**: Minimal logic executed during the core request cycle.
- **Non-blocking**: Telemetry is handed off to the `Ingest` queue without stalling the response.
