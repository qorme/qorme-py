# Taggit Domain

The **Taggit Domain** optimizes and tracks interactions with the `django-taggit` library.

## 📝 Key Functions

- **Tag Relation Tracking**: Monitors how tags are queried and associated with models.
- **Performance Optimization**: Identifies N+1 query patterns specifically related to tag fetching.
- **Usage Analysis**: Helps determine the most frequently accessed tags and their impact on database performance.

## ⚙️ Configuration

Enabled via: `"taggit.relations"` in the `domains` list.

## 🚀 Performance Impact: **Low**

- Specifically instruments `django-taggit` managers and signals.
