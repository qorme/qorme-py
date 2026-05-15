# select_related vs prefetch_related

A deep dive into Django's two strategies for loading related objects, when to use each, and how Qorme automates the choice.

## The problem

By default, Django uses lazy loading for related objects. Accessing `post.author` on a queryset result triggers a separate database query:

```python
posts = BlogPost.objects.all()  # 1 query
for post in posts:
    print(post.author.name)     # N additional queries (one per post)
```

This is the **N+1 problem**: 1 query for the posts + N queries for the authors.

## Two solutions

### `select_related` — SQL JOIN

```python
posts = BlogPost.objects.select_related("author").all()
```

Generates a single SQL query with a `JOIN`:

```sql
SELECT blog_post.*, auth_user.*
FROM blog_post
INNER JOIN auth_user ON blog_post.author_id = auth_user.id
```

**Pros:**
- Single database round-trip
- No Python-side joining

**Cons:**
- Duplicates related data when multiple rows share the same related object
- Only works for forward `ForeignKey` and `OneToOneField`
- Can produce very wide result sets with many joins

### `prefetch_related` — Separate query + Python join

```python
posts = BlogPost.objects.prefetch_related("author").all()
```

Generates two queries:

```sql
SELECT * FROM blog_post;
SELECT * FROM auth_user WHERE id IN (1, 2, 3, ...);
```

Django joins them in Python using a dictionary lookup.

**Pros:**
- Works with `ManyToManyField`, reverse `ForeignKey`, and `GenericRelation`
- No data duplication — each related object is loaded once
- More memory efficient when many rows share the same related objects

**Cons:**
- Two database round-trips instead of one
- Python-side joining has overhead

## When each strategy wins

### Benchmark data

| Scenario | `select_related` | `prefetch_related` | Winner |
|:---|:---|:---|:---|
| 1,000 rows, same related object | 0.037s, 1.27 MB | 0.032s, 0.84 MB | `prefetch_related` |
| 10,000 rows, same related object | 0.422s, 13.67 MB | 0.300s, 8.78 MB | `prefetch_related` |
| 10,000 rows, unique related objects | 0.418s, 13.63 MB | 0.635s, 15.98 MB | `select_related` |

### Decision rules

| Condition | Best strategy |
|:---|:---|
| Forward FK/O2O, low duplication ratio (<1.5×) | `select_related` |
| Forward FK/O2O, high duplication ratio (>10×) | `prefetch_related` |
| Reverse FK, M2M, GenericRelation | `prefetch_related` (only option) |
| Need to filter/annotate related objects | `prefetch_related` with `Prefetch()` |

The **duplication ratio** is `total instances / unique instances`. If 1,000 posts are written by 10 authors, the duplication ratio for `author` is 100× — `prefetch_related` wins decisively.

## How Qorme automates this

### Detection

The `django.relations` domain tracks every relationship traversal:

1. Which field was accessed (`post.author`, `author.posts`)
2. From which parent query
3. At what depth
4. Whether it was a deferred field reload or a genuine relationship traversal

When multiple queries hit the same model and field from the same parent query at depth ≥ 1, this is flagged as an N+1 pattern.

### Optimization

The `django.prefetch_relations` domain (an `MLDomain`) uses trained models to predict which relationships will be traversed:

```python
def optimize(self, query_tracker):
    for path, model in queue:
        prediction = ml_model.predict(MLInstance(path, query_tracker))
        if prediction:
            for field in ml_model.decode_target(prediction.predicted):
                prefetch.add(build_rel_path(path, field))
```

When the prediction is stable, it injects `prefetch_related()` into the queryset before the SQL is generated.

### Why Qorme uses `prefetch_related` (not `select_related`)

Qorme's auto-optimization uses `prefetch_related` exclusively because:

1. **Universality** — Works for all relationship types (forward FK, reverse FK, M2M, generic)
2. **Safety** — Adding an unnecessary `prefetch_related` wastes one extra query; adding an unnecessary `select_related` bloats every row in the result set
3. **No schema knowledge needed** — `prefetch_related` doesn't require knowing the JOIN structure
4. **Composability** — Multiple `prefetch_related` calls are merged cleanly; multiple `select_related` calls interact with each other

!!! tip "Manual `select_related` is still better sometimes"
    If you know your data has low duplication ratios, manually adding `select_related` will outperform Qorme's auto-prefetch. Qorme respects existing `select_related` and `prefetch_related` on your querysets — it only adds to them, never replaces.

## Key takeaway

| Strategy | Use when | Qorme's role |
|:---|:---|:---|
| `select_related` | You know the relationship type and data distribution | Detected but not auto-applied |
| `prefetch_related` | Universal fallback, high duplication, M2M/reverse | Auto-applied by ML predictions |
| Neither (lazy loading) | You don't access the related object | Qorme detects and reports this as a potential optimization |
