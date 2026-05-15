# Taggit Integration

**Domain ID:** `taggit.relations`  
**Handler:** `qorme_django.contrib.taggit.relations.RelationTracking`  
**Package:** `qorme-django`

## What it does

Extends Qorme's relationship tracking to work with `django-taggit`'s custom tag manager. Without this domain, tag relationship queries (e.g., `post.tags.all()`) would not be correctly attributed to the originating model and field.

## Setup

Add the domain to your config:

```python title="settings.py"
QORME = {
    "domains": [
        "ingest",
        "db.psycopg",
        "django.queries",
        "django.relations",     # Required — taggit.relations extends this
        "taggit.relations",     # ← Add this
    ],
}
```

!!! info "`django.relations` is required"
    The `taggit.relations` domain works by adding the correct query hints so that `django.relations` can attribute tag queries correctly. Enable both.

## How it works

The domain wraps `_TaggableManager.get_queryset()` to inject Django-style query hints:

```python
def _get_queryset_wrapper(self, wrapped, instance, args, kwargs):
    ret = wrapped(*args, **kwargs)
    field = instance.name or instance.prefetch_cache_name
    ret._hints.update(instance=instance.instance, _field=field)
    return ret
```

This makes taggit's custom manager produce querysets with the same `_hints` that Django's built-in relationship managers use, allowing the `Relations` domain to treat tag queries like any other relationship traversal.

## Why it's needed

`django-taggit` uses a custom `_TaggableManager` that doesn't follow Django's standard `ReverseManyToOneDescriptor` pattern. Without this integration:

- Tag queries would show up as orphaned queries in the dashboard
- N+1 patterns involving tags (e.g., iterating posts and accessing `post.tags.all()`) wouldn't be detected
- The `prefetch-relations` ML model wouldn't learn to auto-prefetch tags

## Requirements

- `django-taggit` must be installed
