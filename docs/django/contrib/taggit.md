# Taggit: Tagging optimization

The **Taggit Domain** provides specialized tracking for the popular `django-taggit` library, helping you optimize complex many-to-many relationship fetches.

## 📝 Key Functions

- **Tag-to-Model Profiling**: Monitors how tags are associated with your models and identifies redundant relationship fetches.
- **Relational Integrity**: Specifically monitors `TaggableManager` usage to detect if tag-related queries can be optimized via prefetching.

## ⚙️ How to Enable

Add `"taggit.relations"` to your `domains` list.

## 📐 Implementation Details

This domain specifically instruments the `TaggableManager` and its related many-to-many manager to ensure that tag lookups are correctly attributed to the parent model and request.

## 🚀 Performance Impact: **Low**

Minimal overhead for common tag operations.
