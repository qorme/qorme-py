# Wagtail CMS: Specialized Profiling

The **Wagtail Domain** provides deep, specialized instrumentation for applications built with the Wagtail CMS. It offers insight into the complex rendering cycles of page-driven applications.

## 📝 Key Functions

- **Page Render Tracking**: Measures the performance of the `Page.serve()` and `Page.get_context()` cycles.
- **StreamField Block Profiling**: Automatically profiles individual blocks within a `StreamField`. It helps identify slow components (e.g., custom blocks that perform their own DB queries).
- **In-Place Instrumentation**: Uses signal-based hooks to capture telemetry without requiring changes to your Custom Page models.

## ⚙️ How to Enable

Add `"wagtail.page_render"` to your `domains` list.

## 📐 Implementation Details

This domain hooks into Wagtail's rendering pipeline via `TemplateTracking`. It specifically monitors the `wagtailcore` apps and tracks block rendering via the `Page.serve` context.

## 🚀 Performance Impact: **Low**

Optimized for high-depth rendering trees. Adds minimal overhead even for pages with dozens of nested StreamField blocks.
