import unittest

from .test_app.factories import FilmFactory, InventoryFactory
from .test_app.models import Film, Language
from .utils import TrackingTestUtils


class TestSelectRelatedJoinFields(TrackingTestUtils):
    """Test that join fields are correctly marked as accessed for select_related relations."""

    domains = {
        "columns": {
            "handler": "qorme_django.domains.columns.ColumnsTracking",
            "known_descriptors": set(),
        },
    }

    def setUp(self):
        super().setUp()
        self.idx_to_columns = self.manager.get_domain_handler("django.columns").idx_to_columns

    def test_forward_fk_join_field_marked_as_accessed(self):
        """Test forward ForeignKey: Film.language -> Language."""
        from tests.test_app.factories import FilmFactory
        from tests.test_app.models import Film

        FilmFactory()

        with self.context:
            films = list(Film.objects.select_related("language"))
            # Access only the title, NOT the language_id
            _ = films[0].title

        # Check that language_id is marked as required (because it's a join field)
        tracker = self.queries[-1]
        film_rows = tracker.rows["test_app.Film"]
        required_fields = [
            self.idx_to_columns[Film._meta.label][idx] for idx in film_rows.columns_required.list()
        ]
        self.assertIn("language_id", required_fields)

    def test_forward_one_to_one_join_field_marked_as_accessed(self):
        """Test forward OneToOne: StaffMember.user -> User."""
        from tests.test_app.factories import StaffMemberFactory
        from tests.test_app.models import StaffMember

        StaffMemberFactory()

        with self.context:
            staff = list(StaffMember.objects.select_related("user"))
            # Access only a field, NOT user_id
            _ = staff[0].picture

        # Check that user_id is marked as required (join field for OneToOne)
        tracker = self.queries[-1]
        staff_rows = tracker.rows["test_app.StaffMember"]
        required_fields = [
            self.idx_to_columns[StaffMember._meta.label][idx]
            for idx in staff_rows.columns_required.list()
        ]
        self.assertIn("user_id", required_fields)

    def test_reverse_one_to_one_no_join_field_on_parent(self):
        """Test reverse OneToOne: User -> StaffMember (via staff_member).

        In reverse relations, the FK lives on the related model (StaffMember.user_id),
        not on the queried model (User). So there's no join field to mark on User.
        """
        from tests.test_app.factories import StaffMemberFactory
        from tests.test_app.models import User

        staff = StaffMemberFactory()

        with self.context:
            users = list(User.objects.filter(id=staff.user_id).select_related("staff_member"))
            # Access only username, not anything from staff_member
            _ = users[0].username

        # User should have no join field marked for reverse relation
        # (the FK is on StaffMember, not User)
        tracker = self.queries[-1]
        user_rows = tracker.rows["test_app.User"]
        accessed_fields = [
            self.idx_to_columns[User._meta.label][idx] for idx in user_rows.columns_accessed.list()
        ]
        # The only accessed field should be 'username' which we explicitly accessed
        # There should be no FK field like 'staff_member_id' because it doesn't exist on User
        self.assertNotIn("staff_member_id", accessed_fields)

    def test_multi_level_select_related(self):
        """Test multi-level: Address.city.country -> City -> Country."""
        from tests.test_app.factories import AddressFactory
        from tests.test_app.models import Address, City

        AddressFactory()

        with self.context:
            addresses = list(Address.objects.select_related("city__country"))
            # Access only the address field
            _ = addresses[0].address

        tracker = self.queries[-1]

        # Address should have city_id marked as required (join field)
        address_rows = tracker.rows["test_app.Address"]
        address_required = [
            self.idx_to_columns[Address._meta.label][idx]
            for idx in address_rows.columns_required.list()
        ]
        self.assertIn("city_id", address_required)

        # City should have country_id marked as required (join field)
        city_rows = tracker.rows["test_app.Address__city"]
        city_required = [
            self.idx_to_columns[City._meta.label][idx] for idx in city_rows.columns_required.list()
        ]
        self.assertIn("country_id", city_required)

    def test_multiple_forward_fks_select_related(self):
        """Test multiple forward FKs: Inventory.film, Inventory.store."""
        from tests.test_app.factories import InventoryFactory
        from tests.test_app.models import Inventory

        InventoryFactory()

        with self.context:
            inventories = list(Inventory.objects.select_related("film", "store"))
            # Access only a neutral field
            _ = inventories[0].last_updated_at

        tracker = self.queries[-1]
        inv_rows = tracker.rows["test_app.Inventory"]
        required_fields = [
            self.idx_to_columns[Inventory._meta.label][idx]
            for idx in inv_rows.columns_required.list()
        ]
        self.assertIn("film_id", required_fields)
        self.assertIn("store_id", required_fields)


class TestColumnsTracking(TrackingTestUtils):
    domains = {
        "columns": {
            "handler": "qorme_django.domains.columns.ColumnsTracking",
            "known_descriptors": set(),
        },
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.film = FilmFactory(title="Test Film")

    def setUp(self):
        super().setUp()
        self.idx_to_columns = self.manager.get_domain_handler("django.columns").idx_to_columns

    def test_model_instance_tracking(self):
        """Test tracking of model instance columns."""
        with self.context:
            qs = Film.objects.filter(id=self.film.id)
            len(qs)
            tracked_film = qs[0]

            _, _ = tracked_film.title, tracked_film.imdb_url

        accessed = tracked_film.__columns_accessed__
        fields = [self.idx_to_columns[Film._meta.label][idx] for idx in accessed.list()]
        self.assertEqual(fields, ["title", "imdb_url"])

        qs_tracker_data = self.queries[-1]
        self.assertIs(
            qs_tracker_data.rows["test_app.Film"].columns_accessed,
            accessed,
        )

    def test_joined_model_instance_tracking(self):
        """Test tracking of model instance columns."""
        FilmFactory()
        with self.context:
            qs = Film.objects.select_related("language")
            film = list(qs)[0]
            tracked_language = film.language

            _, _ = tracked_language.name, tracked_language.name
            self.assertEqual(film.language_id, tracked_language.pk)

        accessed = tracked_language.__columns_accessed__
        fields = [self.idx_to_columns[Language._meta.label][idx] for idx in accessed.list()]
        self.assertEqual(fields, ["id", "name"])

        qs_tracker_data = self.queries[-1]
        rows = qs_tracker_data.rows["test_app.Film__language"]
        self.assertEqual(rows.count, 2)
        self.assertEqual(rows.model, Language._meta.label)
        self.assertIs(rows.columns_accessed, accessed)

        rows = qs_tracker_data.rows["test_app.Film"]
        accessed = film.__columns_accessed__
        fields = [self.idx_to_columns[Film._meta.label][idx] for idx in accessed.list()]
        self.assertEqual(fields, ["language_id"])
        self.assertEqual(rows.count, 2)
        self.assertEqual(rows.model, Film._meta.label)
        self.assertIs(rows.columns_accessed, accessed)

    def test_prefetch_related(self):
        """Test tracking of model instance columns."""
        FilmFactory()
        with self.context:
            qs = Film.objects.prefetch_related("language")
            # film = list(qs)[0]
            list(qs)

    def test_cached_related_objects_not_included_in_row_tracking(self):
        """Test cached relations from reverse FK are not tracked."""
        inventory = InventoryFactory()
        store = inventory.store

        with self.context:
            # Query through reverse FK with select_related("film")
            # SQL only JOINs inventory and film, NOT store
            list(store.inventory_items.select_related("film"))

        tracker = self.queries[-1]

        # Only Inventory and Film should be tracked, not Store
        self.assertEqual(len(tracker.rows), 2)
        self.assertIn("test_app.Inventory", tracker.rows)
        self.assertIn("test_app.Inventory__film", tracker.rows)
        self.assertNotIn("test_app.Inventory__store", tracker.rows)

    @unittest.expectedFailure
    def test_select_related_without_args(self):
        """Test select_related() without args tracks all FK relations."""
        FilmFactory()

        with self.context:
            list(Film.objects.select_related())

        tracker = self.queries[-1]

        # Film and its FK relations should be tracked
        # Assertion below fails due to lazy model initialization
        # behaviour combined with select_related() without args
        self.assertEqual(len(tracker.rows), 2)
        self.assertIn("test_app.Film", tracker.rows)
        self.assertIn("test_app.Film__language", tracker.rows)


class TestColumnsRequiredTracking(TrackingTestUtils):
    """Test cases for columns_required tracking (non-deferrable fields)."""

    domains = {
        "columns": {
            "handler": "qorme_django.domains.columns.ColumnsTracking",
            "known_descriptors": set(),
        },
    }

    def setUp(self):
        super().setUp()
        self.idx_to_columns = self.manager.get_domain_handler("django.columns").idx_to_columns

    def test_pk_is_always_required(self):
        """Verify that the primary key (id) is always marked as required."""
        from tests.test_app.factories import FilmFactory
        from tests.test_app.models import Film

        FilmFactory()

        with self.context:
            films = list(Film.objects.all())
            _ = films[0].title  # Access only title, not id

        tracker = self.queries[-1]
        film_rows = tracker.rows["test_app.Film"]
        required_fields = [
            self.idx_to_columns[Film._meta.label][idx] for idx in film_rows.columns_required.list()
        ]
        # PK should always be in required
        self.assertIn("id", required_fields)

    def test_parent_pointer_is_always_required(self):
        """Verify that the parent pointer (task_ptr_id) is marked as required in MTI."""
        from tests.test_app.factories import GroupApprovalTaskFactory
        from tests.test_app.models import GroupApprovalTask

        GroupApprovalTaskFactory()

        with self.context:
            tasks = list(GroupApprovalTask.objects.all())
            _ = tasks[0].name  # Access inherited field

        tracker = self.queries[-1]
        task_rows = tracker.rows["test_app.GroupApprovalTask"]
        required_fields = [
            self.idx_to_columns[GroupApprovalTask._meta.label][idx]
            for idx in task_rows.columns_required.list()
        ]
        # Parent pointer should be in required
        self.assertIn("task_ptr_id", required_fields)

    def test_forward_fk_select_related_is_required(self):
        """Verify that the FK field (language_id) is required when select_related is used."""
        from tests.test_app.factories import FilmFactory
        from tests.test_app.models import Film

        FilmFactory()

        with self.context:
            films = list(Film.objects.select_related("language"))
            _ = films[0].language.name

        tracker = self.queries[-1]
        film_rows = tracker.rows["test_app.Film"]
        required_fields = [
            self.idx_to_columns[Film._meta.label][idx] for idx in film_rows.columns_required.list()
        ]
        # FK used in select_related should be required
        self.assertIn("id", required_fields)  # PK always required
        self.assertIn("language_id", required_fields)

    def test_forward_one_to_one_select_related_is_required(self):
        """Verify that O2O FK field (user_id) is required when select_related is used."""
        from tests.test_app.factories import StaffMemberFactory
        from tests.test_app.models import StaffMember

        StaffMemberFactory()

        with self.context:
            staff = list(StaffMember.objects.select_related("user"))
            _ = staff[0].user.username

        tracker = self.queries[-1]
        staff_rows = tracker.rows["test_app.StaffMember"]
        required_fields = [
            self.idx_to_columns[StaffMember._meta.label][idx]
            for idx in staff_rows.columns_required.list()
        ]
        # O2O FK used in select_related should be required
        self.assertIn("user_id", required_fields)

    def test_reverse_one_to_one_not_required_on_parent(self):
        """Verify that for reverse O2O, no FK field is required on the parent model."""
        from tests.test_app.factories import StaffMemberFactory
        from tests.test_app.models import User

        staff = StaffMemberFactory()

        with self.context:
            users = list(User.objects.select_related("staff_member").filter(pk=staff.user.pk))
            _ = users[0].staff_member

        self.assertEqual(len(self.queries), 1)
        tracker = self.queries[-1]
        user_rows = tracker.rows[User._meta.label]
        required_fields = [
            self.idx_to_columns[User._meta.label][idx] for idx in user_rows.columns_required.list()
        ]
        # Only PK should be required on User (the FK is on StaffMember)
        self.assertIn("id", required_fields)
        # staff_member is a reverse relation, no FK column on User
        self.assertNotIn("staff_member_id", required_fields)

    def test_multi_level_select_related_required(self):
        """Verify that intermediate FKs are required in multi-level select_related."""
        from tests.test_app.factories import AddressFactory
        from tests.test_app.models import Address, City

        AddressFactory()

        with self.context:
            addresses = list(Address.objects.select_related("city__country"))
            _ = addresses[0].city.country.country  # Country model uses 'country' field, not 'name'

        tracker = self.queries[-1]

        # Address should have city_id as required
        address_rows = tracker.rows["test_app.Address"]
        address_required = [
            self.idx_to_columns[Address._meta.label][idx]
            for idx in address_rows.columns_required.list()
        ]
        self.assertIn("id", address_required)
        self.assertIn("city_id", address_required)

        # City should have country_id as required
        city_rows = tracker.rows["test_app.Address__city"]
        city_required = [
            self.idx_to_columns[City._meta.label][idx] for idx in city_rows.columns_required.list()
        ]
        self.assertIn("id", city_required)
        self.assertIn("country_id", city_required)
