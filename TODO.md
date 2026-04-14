# To-Do

Create Github issues for these.

## Pre-MVP
- Update ingest test file

### Integrations
- Add unittest integration
- Add Peewee, Tortoise and SQLalchemy ORM integrations
- Add integration for some web frameworks
- Mention that using 2 ORMs on the same project isn't supported.
- Benchmark time taken to match one row from 0, 10, 100, 1000 and 10k objects using no index, a single index, a composite index. Analyze benchmarks results to see which thresold a query duration should exceed before retrieving the query plan. Write article on it.
- Validate domain configuration
- Detect database used and enable relevant connection tracking class

### Code quality/tidy-ups
- TODOs in codebase
- Type checking
- Add docs
- Client implementation
- Handle errors gracefully
- Check how TrackingManager works in a multiprocess environment
- Integration tests
- Test and document that tracking can be disabled by setting the `QORME_ACTIVE` env var to False.
- Cache results of get_model_string (weak_lru_cache)

## Post-MVP
- Add pytest integration
- Capture all internal exceptions and send them to server
- Look at limiting query tracking to specified models (by only patching their QuerySet object - see https://github.com/django/django/blob/main/django/db/models/manager.py#L87)
- Add tests to ensure patches are properly disabled and no side effects expected (example check wrapping of cached attribute `related_manager_cls`)t
- Distributed tracking (distributed tracing)
- Sampling
- Add an overhead estimation for each tracking module for end users (low, medium, high)
- We only want to track attributes when we're inside a tracking context. Look at wrapping models for attributes tracking lazily i.e when a query is made for a model. Patch models incréentally and remove patch at context exit
- Write article about pg_pool and indicate how qorme helps. Handle pools in connection tracking.

# Done
- Check usage of assert
- Add all instance related data under the `instances` key in query tracker data. Info should be added by instance id. e.g. `instances[id(instance)] = {"model": model, "field": field, "instance_tracker": instance_tracker, "memory": memory}`
- Patch **getattribute** instead of creating TrackedInstance objects (check performance)
- Update wrapping methodology to avoid invoking a new get_wrapper function, let tracking domains handle necessary context ( except for relations )
- Fix relation tracking
- Implement traceback tracking
- Implement template info filtering in tracebacks (See template tracking domain)
- Filter traceback to only include relevant frames - Cython
- Add a register_query_started_handler helper in hooks
- Add database details fir each query (name, url etc ..)
- Add ConnectionTracking domain (https://www.psycopg.org/psycopg3/docs/advanced/pool.html)
- Add result hash domain tracking to ensure duplicate queries actually returned same result set. This can also help detect caching patterns.
- Detect queries from only, defer
- Detect prefetch related relations
- Add query execution time
- Add specific NewQueryHandler, NewInstanceHandler... event handler types (1hr)
- Remove result cache
- Use msgspec for schema and serialization
- Rename to qorme
- Add __slots__ to tracking domains
- Add query paramater hash and result hash via row_factory ?
- Patch drivers direvtly for connection tracking
- Add query params hash domain
- Lazy model patching

