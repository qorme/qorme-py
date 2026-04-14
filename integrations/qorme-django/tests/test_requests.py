from django.test import Client
from django.urls import reverse

from qorme.context.tracking import get_query_context
from qorme.context.types import ContextType
from tests.test_app.factories import FilmFactory

from .utils import TrackingTestUtils, capture_context_trackers, capture_query_trackers


class TestRequestTracking(TrackingTestUtils):
    domains = {
        "requests": {
            "handler": "qorme_django.domains.requests.RequestTracking",
            "ignore_paths": ["/ignored/"],
        }
    }

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_request_tracking(self):
        """Test that requests are properly tracked."""
        FilmFactory.create_batch(3)

        with capture_context_trackers() as ctx_trackers, capture_query_trackers():
            response = self.client.get(reverse("films"))

        self.assertEqual(response.status_code, 200)

        # Verify context was created
        self.assertEqual(len(ctx_trackers), 1)
        context = ctx_trackers[0]

        self.assertEqual(context.data.type, ContextType.HTTP)
        self.assertEqual(context.data.name, "films")
        self.assertEqual(context.data.data["method"], "GET")
        self.assertEqual(context.data.data["query_string"], "")
        self.assertEqual(context.data.data["path"], "/films/")
        self.assertEqual(context.data.data["url_name"], "films")
        self.assertEqual(len(self.queries), 1)

    def test_request_with_exception(self):
        """Test that requests with exceptions are tracked."""
        with (
            capture_context_trackers() as ctx_trackers,
            self.assertRaises(ValueError),
        ):
            self.client.get("/error/")

        # Ensure request isn't the current context
        self.assertIsNone(get_query_context(None))

        # Verify context was created
        self.assertEqual(len(ctx_trackers), 1)
        context = ctx_trackers[0]
        self.assertEqual(context.data.type, ContextType.HTTP)
        self.assertEqual(context.data.name, "error")
        self.assertEqual(context.data.data["method"], "GET")
        self.assertEqual(context.data.data["query_string"], "")
        self.assertEqual(context.data.data["path"], "/error/")
        self.assertEqual(context.data.data["url_name"], "error")
        self.assertEqual(len(self.queries), 1)

    def test_ignored_path(self):
        """Test that ignored paths are not tracked."""
        with capture_context_trackers() as ctx_trackers:
            response = self.client.get("/ignored/")

        # Path doesn't exist but that's ok
        self.assertEqual(response.status_code, 404)

        # Verify no context was created
        self.assertEqual(len(ctx_trackers), 0)
