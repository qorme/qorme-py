# Wagtail Integration

**Domain ID:** `wagtail.page_render`  
**Handler:** `qorme_django.contrib.wagtail.page_render.PageRender`  
**Package:** `qorme-django`

## What it does

Adds specialized tracking for Wagtail CMS page rendering. Creates a dedicated `QueryContext` for each Wagtail page serve, so you can see exactly which queries are triggered by each page type.

## Setup

Add the domain to your config:

```python title="settings.py"
QORME = {
    "domains": [
        "ingest",
        "db.psycopg",
        "django.queries",
        "django.requests",
        "wagtail.page_render",  # ← Add this
    ],
}
```

## How it works

The domain wraps `wagtail.models.Page.serve()`:

1. When a Wagtail page is served, the domain intercepts the `serve()` call
2. It attaches the page instance to the `TemplateResponse` returned
3. When the response is rendered, it creates a `QueryContext` named after the page's `verbose_name`
4. All queries executed during template rendering are attributed to this page-specific context

This gives you page-type-level visibility — you can see that "Blog Post pages trigger 15 queries on average" separately from "Landing pages trigger 3 queries."

## When to use

Enable this alongside the standard Django domains for any project using Wagtail as its CMS. It provides more granular context attribution than `django.requests` alone, because it separates the page rendering phase from the rest of the request lifecycle.

## Requirements

- `wagtail` must be installed
- If Wagtail is not installed, the domain will fail to import cleanly during domain initialization
