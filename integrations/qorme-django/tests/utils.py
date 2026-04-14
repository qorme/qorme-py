from contextlib import contextmanager

from django.test import TestCase

from qorme.context.tracking import QueryContext
from qorme.manager import TrackingManager
from qorme.orm.tracking import ORMQuery
from qorme.utils.wrapper import Wrapper


@contextmanager
def capture_context_trackers():
    """
    Context manager that captures all `QueryContext`
    rows created within its scope.

    Usage:
        with capture_context_trackers() as ctx_trackers:
            # Do something that creates context trackers
            assert len(ctx_trackers) == 1
    """
    ctx_trackers = []

    def init_wrapper(wrapped, instance, args, kwargs):
        wrapped(*args, **kwargs)
        ctx_trackers.append(instance)

    with Wrapper().wrap_temp(QueryContext, "__init__", init_wrapper):
        yield ctx_trackers


@contextmanager
def capture_query_trackers():
    trackers = []

    def init_wrapper(wrapped, instance, args, kwargs):
        wrapped(*args, **kwargs)
        trackers.append(instance)

    with Wrapper().wrap_temp(ORMQuery, "__init__", init_wrapper):
        yield trackers


class TrackingTestUtils(TestCase):
    domains = {}
    deps_settings = {}

    def setUp(self):
        all_domains = ["queries"] + list(self.domains)
        settings = {
            "active": True,
            "domains": set([f"django.{domain}" for domain in all_domains]),
            "deps": {
                "traceback": {
                    "num_entries": 3,
                    "entries_cache_size": 32,
                    "file_info_cache_size": 32,
                    "default_ignored_modules": ["qorme", "unittest", "threading"],
                    "extra_ignored_modules": [],
                },
                **self.deps_settings,
            },
            "django": {
                "queries": {
                    "handler": "qorme_django.domains.queries.QueryTracking",
                    "apps_to_include": ["test_app"],
                    "apps_to_exclude": [],
                    "models_to_include": [],
                    "models_to_exclude": [],
                },
                **self.domains,
            },
        }
        self.manager = TrackingManager(settings=settings, defaults={})
        self.assertTrue(self.manager.start())

        deps = self.manager.deps
        assert deps is not None

        self.queries = []
        self.context = QueryContext(name="qorme-django", deps=deps)
        deps.events.register_query_started_handler(self._query_started_handler)
        super().setUp()

    def tearDown(self):
        self.manager.stop()
        super().tearDown()

    def _query_started_handler(self, tracker):
        self.queries.append(tracker)
