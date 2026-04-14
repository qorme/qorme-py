"""Default configuration values."""

from typing import Any

QORME_SETTINGS: dict[str, Any] = {
    "active": True,
    "domains": [],
    "deps": {
        "async_worker": {
            "startup_timeout": 3.0,
            "shutdown_timeout": 60.0,
        },
        "http_client": {
            "dsn": "",
            "request_timeout": 60.0,
            "shutdown_timeout": 60.0,
            "http2": True,
            "verify_ssl": True,
            "retry": {
                "attempts": 5,
                "backoff_jitter": 1.0,
                "backoff_factor": 0.5,
            },
        },
        "traceback": {
            "num_entries": 10,
            "entries_cache_size": 1024,
            "file_info_cache_size": 256,
            "default_ignored_modules": [
                "qorme",
                "wsgiref",
                "gunicorn",
                "unittest",
                "threading",
                "socketserver",
            ],
            "extra_ignored_modules": [],
        },
        "ml_store": {
            "sse": {
                "url_path": "ml/updates/",
                "max_retries": 5,
                "retry_interval": 30.0,
                "startup_timeout": 3.0,
                "read_timeout": 90.0,
            },
        },
    },
    "ingest": {
        "handler": "qorme.ingest.ingest.Ingest",
        "rows_wait_time": 20,
        "queue": {
            "join_timeout": 60.0,
            "queue_max_size": 25000,
            "pqueue_max_size": 50000,
            "batch_min_size": 1000,
            "batch_max_size": 5000,
            "flush_max_interval": 30.0,  # In seconds
            "flusher": {
                "url_path": "ingest/",
                "enc_buffer_size": 64 * 1024,  # 64 KB
                "compress_level": 1,  # From 0 to 3 (using ical levels, will be scaled for gzip)
                "request_timeout": 60.0,
            },
        },
    },
    "db": {
        "sqlite": {"handler": "qorme.db.integrations.sqlite.SQLiteTracking"},
        "psycopg": {"handler": "qorme.db.integrations.psycopg.PsycopgTracking"},
        "psycopg2": {"handler": "qorme.db.integrations.psycopg2.Psycopg2Tracking"},
    },
    # Contrib
    "celery": {
        "tracking": {
            "handler": "qorme.contrib.celery.tracking.CeleryTracking",
            "ignore_tasks": [],
        }
    },
}
