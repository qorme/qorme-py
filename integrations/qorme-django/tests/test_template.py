from django.test import Client
from django.urls import reverse

from qorme.utils.traceback import TracebackEntry

from .test_app.factories import FilmFactory, StaffMemberFactory, StoreFactory
from .utils import TrackingTestUtils


class TestTemplateTracking(TrackingTestUtils):
    domains = {
        "requests": {
            "handler": "qorme_django.domains.requests.RequestTracking",
            "ignore_paths": [],
        },
        "template": {
            "handler": "qorme_django.domains.template.TemplateTracking",
        },
    }

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_template_tracking(self):
        """Test that template rendering is properly tracked."""
        FilmFactory.create_batch(3)

        with self.context:
            self.client.get(reverse("films"))

        self.assertEqual(len(self.queries), 1)
        query_tracker = self.queries[0]

        template_info = query_tracker.data.template
        self.assertEqual(template_info.filename, "test_app/films.html")
        self.assertEqual(template_info.lineno, 2)
        self.assertIn("{% for film in films %}", template_info.line)

    def test_nested_template_render(self):
        stores = StoreFactory.create_batch(1)
        stores[0].manager = StaffMemberFactory(store=stores[0])

        with self.context:
            self.client.get(reverse("stores"))

        expected = [
            TracebackEntry(
                filename="test_app/stores.html",
                lineno=1,
                func_name="",
                line="{% for store in stores %}\n",
            ),
            TracebackEntry(
                filename="test_app/includes/store.html",
                lineno=5,
                func_name="",
                line="    {% address store.address %}\n",
            ),
            TracebackEntry(
                filename="test_app/includes/address.html",
                lineno=7,
                func_name="",
                line="    <p>{{ address.city.name }}</p>\n",
            ),
        ]

        for query_tracker, tb in zip(self.queries, expected, strict=False):
            self.assertEqual(tb, query_tracker.data.template)
