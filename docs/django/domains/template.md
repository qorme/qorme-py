# Django Template Domain: Rendering Insight

The **Django Template Domain** provides visibility into the rendering lifecycle of your application's frontend, helping you identify complex blocks and query-heavy templates.

## 📝 Key Functions

- **Template Timing**: Measures the total time spent rendering each template in the response.
- **Block Profiling**: Granular timing for individual `{% block %}` and `{% include %}` tags.
- **Context Analysis**: Monitors the size and complexity of the context data passed to the renderer.
- **Query Attribution**: Correlates any database queries triggered *during* the render (e.g., via lazy-loaded relationships) with the specific template file and line number.

## ⚙️ Configuration

Enabled via: `"django.template"` in the `domains` list.

## 📐 Implementation Details

This domain hooks into Django's template rendering signals:
- `django.test.signals.template_rendered` (used for broad capture)
- `qorme` specific patches for the rendering backend to ensure sub-block accuracy.

## 🚀 Performance Impact: **Low**

- **Optimized Capture**: Uses system-level timers and efficient string identifiers for template paths.
- **Safe Profiling**: Minimal overhead while tracking nested rendering structures.
