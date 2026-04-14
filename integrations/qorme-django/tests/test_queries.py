from django.db import connection
from django.test.utils import CaptureQueriesContext

from qorme.orm.tracking import ORMQuery
from qorme.orm.types import QueryType, RowType
from tests.test_app.factories import FilmFactory, LanguageFactory
from tests.test_app.models import Film

from .utils import TrackingTestUtils, capture_query_trackers


class TestQueryTracking(TrackingTestUtils):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.language = LanguageFactory()
        cls.films = [FilmFactory(language=cls.language, title=f"Film {i}") for i in range(3)]

    def test_select_related_query_tracking(self):
        """Test tracking of SELECT queries"""
        with (
            self.context,
            CaptureQueriesContext(connection),
            capture_query_trackers() as trackers,
        ):
            qs = Film.objects.all()
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.MODEL)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_exists_query_tracking(self):
        """Test tracking of EXISTS queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.filter(title__contains="1")
            self.assertTrue(qs.exists())

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.EXISTS)
            self.assertEqual(tracker.data.row_type, RowType.SCALAR)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_count_query_tracking(self):
        """Test tracking of COUNT queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.all()
            self.assertEqual(qs.count(), 3)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.COUNT)
            self.assertEqual(tracker.data.row_type, RowType.SCALAR)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_join_query_tracking(self):
        """Test tracking of queries with related fields"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.select_related("language")
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.MODEL)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_filtered_query_tracking(self):
        """Test tracking of filtered queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.filter(language=self.language).order_by("-title")
            # films = list(qs)
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.MODEL)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_values_query_tracking(self):
        """Test tracking of values() queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.values("title")
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.DICT)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_values_list_query_tracking(self):
        """Test tracking of values_list() queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.values_list("title")
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.SEQUENCE)
            self.assertIsNotNone(tracker.data.timestamp)

    def test_flat_values_list_query_tracking(self):
        """Test tracking of values_list(flat=True) queries"""
        with self.context, capture_query_trackers() as trackers:
            qs = Film.objects.values_list("title", flat=True)
            list(qs)

            self.assertEqual(len(trackers), 1)
            tracker = trackers[0]
            self.assertIsInstance(tracker, ORMQuery)
            self.assertIs(tracker.query, qs)
            self.assertEqual(tracker.data.model, "test_app.Film")
            self.assertEqual(tracker.data.query_type, QueryType.SELECT)
            self.assertEqual(tracker.data.row_type, RowType.SCALAR)
            self.assertIsNotNone(tracker.data.timestamp)
