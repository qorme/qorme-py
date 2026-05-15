# Ideas & Future Optimizations

Potential new features and optimization strategies being explored for future Qorme releases.

## Automatic caching + invalidation

**Category:** Database driver layer

For each SQL query executed, predict a TTL before the results are likely to change. On writes, check if they invalidate any cached entry.

This would operate at the SQL layer (below the ORM) and could dramatically reduce database load for read-heavy applications.

**Challenges:** Cache invalidation is famously hard. Requires understanding write patterns, table relationships, and application-level consistency requirements.

## Automatic index management

**Category:** Database driver layer

Analyze query patterns to recommend, create, or remove database indexes for optimal performance.

**Challenges:** Index management interacts with write performance. Requires long-term query pattern analysis and careful cost/benefit modeling.

## Zero Field Access optimization

**Category:** ORM optimization

**Status:** Design complete, implementation pending

### Problem

Production data shows ~4.5% of tracked queries load model instances where no fields are ever accessed. Common causes:

- Existence checks via `.get()` (just confirming the object exists)
- Prefetched relations that are never iterated
- ForeignKey loaded but only the ID was needed (already available from the FK column)
- Template conditionals that evaluate to false

### Proposed solution

A new prediction category (`zero-field-access`) that can skip the database query entirely and return a stub object with only the primary key:

```python
# Instead of:
SELECT id FROM table WHERE id = 1  # Network round-trip

# SDK returns directly:
StubRow(id=1)  # No query executed
```

This works because Django's deferred loading will lazy-load any field if it's actually accessed later. If no fields are ever accessed (as the pattern shows), no additional queries occur.

### Safety model

- Only flag when `columns_accessed = 0` across multiple observations
- Only for `SELECT` queries
- **Requires explicit user opt-in** via the dashboard issues interface
- Conservative: user reviews each affected query/sample before enabling

!!! warning "Trade-off"
    Enabling skip-query removes the database validity check (`DoesNotExist`). Only safe when you're certain the record exists (e.g., IDs from foreign keys).

### Expected impact

- ~4.5% query reduction based on production telemetry
- Zero code changes required
- Safe opt-in model with per-sample granularity

## `select_related` auto-optimization

**Category:** ORM optimization

Currently Qorme auto-applies `prefetch_related` for N+1 patterns. A future optimization could auto-apply `select_related` when the data distribution favors JOINs (low duplication ratio, forward FK/O2O relationships).

This requires tracking:
- Instance duplication ratios per relationship
- Memory usage patterns per strategy
- Query count vs data transfer trade-offs

See [select_related vs prefetch_related](../understanding/select-vs-prefetch.md) for the analysis.

## Async Django support

**Category:** Framework integration

The current Django domains are designed for synchronous views. Full support for Django's async views, async ORM, and async middleware would require:

- Async-aware `QueryContext` management (already using `ContextVar`, which is async-safe)
- Async wrapper patterns for async QuerySet methods
- Testing with async web servers (uvicorn, daphne)

## Query plan analysis

**Category:** Database driver layer

Capture and analyze `EXPLAIN` output for tracked queries to correlate query plans with performance data. This could surface:

- Sequential scans on large tables
- Missing indexes
- Suboptimal join strategies
- Estimated vs actual row counts

**Challenge:** Running `EXPLAIN` adds overhead. Would need to be sampled or limited to slow queries.
