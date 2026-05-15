# Domain Registry

Every tracking domain available in Qorme, with its identifier, handler class, package, and purpose.

## Core domains (`qorme`)

| Domain ID | Handler | Purpose |
|:---|:---|:---|
| `ingest` | `qorme.ingest.ingest.Ingest` | Batches and delivers telemetry to the server over HTTP/2 |
| `db.sqlite` | `qorme.db.integrations.sqlite.SQLiteTracking` | Instruments `sqlite3.connect()` for SQL tracking |
| `db.psycopg` | `qorme.db.integrations.psycopg.PsycopgTracking` | Instruments `psycopg.connect()` (v3) for SQL tracking |
| `db.psycopg2` | `qorme.db.integrations.psycopg2.Psycopg2Tracking` | Instruments `psycopg2.connect()` for SQL tracking |
| `db.params_hash` | `qorme.db.domains.params_hash.ParamsHash` | Hashes SQL query parameters for deduplication |
| `db.result_hash` | `qorme.db.domains.result_hash.ResultHash` | Hashes SQL query result sets for change detection |
| `celery.tracking` | `qorme.contrib.celery.tracking.CeleryTracking` | Creates `QueryContext` per Celery task via signals |

## Django domains (`qorme-django`)

| Domain ID | Handler | Purpose |
|:---|:---|:---|
| `django.queries` | `qorme_django.domains.queries.QueryTracking` | Wraps QuerySet iteration and methods to capture ORM queries |
| `django.requests` | `qorme_django.domains.requests.RequestTracking` | Creates `QueryContext` per HTTP request |
| `django.columns` | `qorme_django.domains.columns.ColumnsTracking` | Patches field descriptors to track column access per instance |
| `django.relations` | `qorme_django.domains.relations.RelationTracking` | Patches relationship descriptors to track traversal depth |
| `django.template` | `qorme_django.domains.template.TemplateTracking` | Attributes queries to template file and line number |
| `django.cli` | `qorme_django.domains.cli.CLITracking` | Creates `QueryContext` for management commands |
| `django.defer_columns` | `qorme_django.domains.ml.defer_columns.DeferColumns` | ML-driven automatic `.defer()` for unused columns |
| `django.prefetch_relations` | `qorme_django.domains.ml.prefetch_relations.PrefetchRelations` | ML-driven automatic `.prefetch_related()` for N+1 |

## Contrib domains (`qorme-django`)

| Domain ID | Handler | Purpose |
|:---|:---|:---|
| `taggit.relations` | `qorme_django.contrib.taggit.relations.RelationTracking` | Adds query hints to `_TaggableManager` for relation tracking |
| `wagtail.page_render` | `qorme_django.contrib.wagtail.page_render.PageRender` | Creates per-page-type `QueryContext` for Wagtail rendering |

## Domain types

| Base class | Type | Behavior |
|:---|:---|:---|
| `Domain` | Monitoring / Infrastructure | Observes and reports via events |
| `MLDomain` | Optimization | Listens for `OPTIMIZATION_REQUEST`, consults `MLStore`, modifies queries |

## Naming convention

Domain IDs use dotted notation that maps directly to the configuration dictionary:

```
"django.queries"  →  QORME["django"]["queries"]
"db.psycopg"      →  QORME["db"]["psycopg"]
"celery.tracking"  →  QORME["celery"]["tracking"]
```

Each configuration block must include a `handler` key pointing to the fully-qualified class name.

## Dependencies between domains

Some domains depend on others to function correctly:

| Domain | Requires | Reason |
|:---|:---|:---|
| `django.columns` | `django.queries` | Listens for `TRACK_MODEL` and `NEW_INSTANCE` events |
| `django.relations` | `django.queries` | Listens for `TRACK_MODEL`, `QUERY_STARTED`, and `NEW_INSTANCE` events |
| `django.template` | `django.queries` | Listens for `QUERY_STARTED` events |
| `django.defer_columns` | `django.queries` | Listens for `OPTIMIZATION_REQUEST` events |
| `django.prefetch_relations` | `django.queries` | Listens for `OPTIMIZATION_REQUEST` events |
| `taggit.relations` | `django.relations` | Adds hints consumed by the relations domain |
| All domains | `ingest` | Without ingest, telemetry is collected but never sent |
