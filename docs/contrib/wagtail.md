# Wagtail Domain

The **Wagtail Domain** provides specialized instrumentation for applications built with the Wagtail CMS.

## 📝 Key Functions

- **Page Render Tracking**: Measures the performance of the full page rendering cycle.
- **Block Profiling**: Deep-dives into StreamField rendering to identify slow blocks.
- **Query Context**: Correlates database queries triggered during a Wagtail request with specific page components.

## ⚙️ Configuration

Enabled via: `"wagtail.page_render"` in the `domains` list.

## 🚀 Performance Impact: **Low**

- Hooks into Wagtail's rendering signals and logic.
- Minimal impact on total page load time.
