# Goals - Ideas

## ORM Layer

### Automatically defer fields not needed (.defer())

For each query, return fields that won't be used for each model included. By the way, no risk of deferring fields newly added to the model that the ML model doesn't know about.

### Automatically prevent N+1 (.prefetch_related)

For each query, return relations to prefetch ('author__books', 'address')

## Database driver/engine layer

### Automatic caching + invalidation

For each sql executed, return ttl before results change. If write, check if it invalidates any cached entry.

### Automatic index creation/removal/management for fined tuned perfomance.

## Zero Field Access Issue

## Problem Statement

When analyzing query patterns, we observe a significant number of queries where columns_accessed = 0 for all rows. This means the ORM loaded objects from the database, but the application code never accessed any fields on those objects.

Data Analysis (from production tracking)
Metric	Value
Total queries tracked	278,802
Queries with zero field access	12,691
Percentage skippable	4.55%
Top affected models:

blog.BlogPage — 4,891 queries
breads.BreadPage — 3,449 queries
locations.LocationPage — 1,647 queries
auth.User — 525 queries
Why This Happens
Common Django patterns that cause zero field access:

# Pattern 1: Existence check via get()
obj = Model.objects.get(pk=pk)  # Loads all columns
# Code never uses obj, just wanted to confirm it exists
# Pattern 2: Prefetch that's never iterated
queryset = Post.objects.prefetch_related('comments')
for post in queryset:
    print(post.title)  # Never accessed post.comments
# Pattern 3: ForeignKey loaded but only ID needed
user = request.user  # Loads User object
log_event(user_id=user.id)  # Only used the ID we already had
# Pattern 4: Template conditional that's never true
{% if obj.some_rare_condition %}  # Object loaded, condition false
{% endif %}
Current Behavior
With unused columns prediction, we optimize:

-- Before (original query)
SELECT id, title, body, author_id, created_at, updated_at, ...
FROM blog_post WHERE id = 1
-- After (unused columns applied)
SELECT id FROM blog_post WHERE id = 1
This is better, but still executes a query to fetch an id that was already known from the WHERE clause.

Proposed Solution
New Issue Type: zero-field-access
Flag queries where columns_accessed bitset = 0 across all row trackings for that query.

User Opt-In Flow
Detection: ML identifies queries with zero field access pattern
Dashboard Issues Interface: Reuse existing issues UI, adapted for this new issue type
Appears alongside other issue types (unused columns, N+1)
User can review affected queries/samples
Provides "Enable Skip Query" action
User Opts In: Developer confirms this query is safe to skip via issues interface
SDK Behavior: When opted in, SDK returns stub row with only id field instead of executing query
Implementation Details
1. What to Return (Stub Row)
When a query is marked as skippable:

Extract the id from the WHERE clause (already known)
Return a minimal row containing only the id field
ORM hydrates a "deferred" object with just the ID
# Instead of:
SELECT id FROM table WHERE id = 1  # Network round-trip
# SDK returns directly:
StubRow(id=1)  # No query executed
NOTE

This works because Django's deferred loading will lazy-load any field if it's accessed later. If no fields are ever accessed (as the pattern shows), no additional queries occur.

2. Granularity: Per ML Sample
The opt-in applies at the ML sample level — the same granularity as other predictions (unused columns, N+1).

Each unique combination of:

Model
Template (code location)
Query pattern
Gets its own sample hash, and user opts in per sample.

3. New Prediction Category
Add alongside existing categories:

defer-columns — defer specific columns
prefetch-relations — add prefetch to avoid N+1
zero-field-access — skip query entirely, return stub
Edge Cases & Risks
Edge Case	Mitigation
Object has __str__ that accesses fields	SDK tracking would catch field access, wouldn't flag
Signals fire on object load (post_init)	User must verify no critical signal logic
Object used in set() or dict (hash)	Usually uses pk, which stub provides
Conditional field access in templates	SDK may not track template access — caveat for user
get_or_create / update_or_create	These have side effects, shouldn't be flagged
Safety: Conservative Flagging
Only flag when:

columns_accessed = 0 for all rows across multiple observations
Query type is SELECT (not INSERT/UPDATE/DELETE)
Query returns exactly one row (pk lookup) OR all rows have zero access
User-Facing Message
Issue Title: Zero Field Access

Description:

This query loads an object but no fields are ever accessed. The query could potentially be eliminated entirely.

Suggested Fix:

Enable "Skip Query" optimization. Qorme will return a stub object with only the ID, avoiding the database round-trip.

Opt-In Button: [Enable Skip Query]

> [!WARNING]
> Enabling this optimization removes the database validity check (e.g. `DoesNotExist`). Only enable if you are certain the record exists (e.g. IDs from foreign keys) or if your logic handles missing records gracefully.

Benefits
~4.5% query reduction — meaningful performance improvement
Zero code changes — works at SDK level
Safe opt-in model — user explicitly approves
Educates developers — surfaces wasteful patterns even without opt-in
