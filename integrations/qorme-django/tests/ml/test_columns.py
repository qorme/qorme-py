from unittest.mock import Mock

from qorme.ml.store import _CONNECTED_STATE, CategoryModels

from ..test_app.factories import (
    FilmFactory,
    StaffMemberFactory,
    UserFactory,
)
from ..test_app.models import (
    Film,
    StaffMember,
)
from ..utils import TrackingTestUtils


class TestDeferColumns(TrackingTestUtils):
    domains = {
        "defer_columns": {
            "handler": "qorme_django.domains.ml.defer_columns.DeferColumns",
            "models_cache_size": 256,
            "refresh_interval": 600,
            "request_timeout": 30,
        },
    }
    deps_settings = {
        "async_worker": {
            "startup_timeout": 1.0,
            "shutdown_timeout": 1.0,
        },
        "http_client": {
            "dsn": "https://key@test.com",
            "request_timeout": 1.0,
            "shutdown_timeout": 1.0,
            "http2": False,
            "verify_ssl": False,
            "retry": {
                "attempts": 1,
                "backoff_jitter": 1.0,
                "backoff_factor": 0.5,
            },
        },
        "ml_store": {
            "sse": {
                "url_path": "ml/updates/",
                "max_retries": 3,
                "retry_interval": 0.1,
                "startup_timeout": 1.0,
                "read_timeout": 1.0,
            },
        },
    }

    def _inject_ml_models(self, model_mocks):
        """Inject mock ML models into the store and set store connected."""
        ml_store = self.manager.deps.ml_store
        if "defer-columns" not in ml_store._models:
            ml_store._models["defer-columns"] = CategoryModels()
        for model_label, mock in model_mocks.items():
            ml_store._models["defer-columns"].models[model_label] = mock
        ml_store._state = _CONNECTED_STATE

    def test_ml_deferring_applies_to_query(self):
        """Test that ML model predictions correctly apply deferred loading to queries."""
        # Create test film
        FilmFactory(title="Test Film", description="A test description")
        deferred = ["title", "description", "special_features"]

        # Setup mock ML model with correct interface (predict returns object with .predicted, .data)
        mock_ml_model = Mock()
        mock_prediction = Mock()
        mock_prediction.predicted = 0
        mock_prediction.data = {}
        mock_ml_model.predict.return_value = mock_prediction
        mock_ml_model.decode_target.return_value = deferred

        self._inject_ml_models({"test_app.Film": mock_ml_model})

        with self.context:
            # Execute a query that should trigger ML prediction
            queryset = Film.objects.filter(title="Test Film")
            # Force query evaluation
            list(queryset)

        # Verify the ML model's predict method was called
        mock_ml_model.predict.assert_called_once()

        for item in queryset:
            for field in deferred:
                self.assertNotIn(field, item.__dict__)

        # Verify deferred loading was applied to the query
        # Django's deferred_loading is a tuple of (set_of_fields, defer_flag)
        # where defer_flag is True if fields should be deferred,
        # False if only those should be loaded
        self.assertEqual(queryset.query.deferred_loading, (frozenset(deferred), True))

    def test_ml_defer_select_related(self):
        """Test that ML model predictions correctly apply deferred loading to
        select_related queries.
        """
        # Create test data - factories will automatically create all related objects
        user = UserFactory()
        StaffMemberFactory(user=user)

        # Setup mock ML models for all models in the select_related chain
        def make_mock(fields):
            mock_prediction = Mock()
            mock_prediction.predicted = 0
            mock_prediction.data = {}
            mock_ml = Mock()
            mock_ml.predict.return_value = mock_prediction
            mock_ml.decode_target.return_value = fields
            return mock_ml

        mock_staff_ml = make_mock(["last_updated_at"])
        mock_user_ml = make_mock(["email"])
        mock_address_ml = make_mock(["last_updated_at"])
        mock_city_ml = make_mock(["last_updated_at"])
        mock_store_ml = make_mock(["last_updated_at"])
        mock_country_ml = make_mock(["last_updated_at"])

        self._inject_ml_models(
            {
                "test_app.StaffMember": mock_staff_ml,
                "test_app.User": mock_user_ml,
                "test_app.Address": mock_address_ml,
                "test_app.City": mock_city_ml,
                "test_app.Store": mock_store_ml,
                "test_app.Country": mock_country_ml,
            }
        )

        with self.context:
            queryset = StaffMember.objects.select_related(
                "user", "address__city", "store__address__city__country"
            )
            list(queryset)

        # Verify all ML models were called
        mock_staff_ml.predict.assert_called_once()
        mock_user_ml.predict.assert_called_once()
        mock_address_ml.predict.assert_called()  # Called twice for "address" and "store__address"
        # Called twice for "address__city" and "store__address__city"
        mock_city_ml.predict.assert_called()
        mock_store_ml.predict.assert_called_once()
        mock_country_ml.predict.assert_called_once()

        # Verify deferred loading was applied with correct paths
        deferred_fields, defer_flag = queryset.query.deferred_loading

        # Assert defer flag is True
        self.assertTrue(defer_flag)

        # Expected deferred fields with their relationship paths
        expected_deferred = {
            "last_updated_at",  # StaffMember.last_updated_at
            "user__email",  # User.email
            "address__last_updated_at",  # Address (staff's).last_updated_at
            "address__city__last_updated_at",  # City (staff's address).last_updated_at
            "store__last_updated_at",  # Store.last_updated_at
            "store__address__last_updated_at",  # Address (store's).last_updated_at
            "store__address__city__last_updated_at",  # City (store's address).last_updated_at
            "store__address__city__country__last_updated_at",  # Country.last_updated_at
        }

        self.assertEqual(deferred_fields, frozenset(expected_deferred))

    def test_ml_no_prediction_no_deferring(self):
        """Test that when ML model returns no prediction, deferred loading is not applied."""
        # Create test film
        FilmFactory(title="Another Film")

        # Setup mock ML model that returns no prediction
        mock_ml_model = Mock()
        mock_ml_model.predict.return_value = None

        self._inject_ml_models({"test_app.Film": mock_ml_model})

        with self.context:
            queryset = Film.objects.filter(title="Another Film")
            list(queryset)

        # Verify the ML model's predict method was called
        mock_ml_model.predict.assert_called_once()

        # Verify deferred loading was NOT applied (should be default state)
        # Default is (frozenset(), True) for no deferred loading
        self.assertEqual(queryset.query.deferred_loading, (frozenset(), True))

    def test_ml_no_model_available(self):
        """Test that when no ML model is available, the query executes normally."""
        # Create test film
        FilmFactory(title="No ML Film")

        # No need to patch - cache is empty by default, so get_model returns None
        with self.context:
            queryset = Film.objects.filter(title="No ML Film")
            result = list(queryset)

        # Verify query executed successfully
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "No ML Film")

        # Verify deferred loading was NOT applied
        self.assertEqual(queryset.query.deferred_loading, (frozenset(), True))
