import gc
import unittest

from tests.test_app.factories import (
    ActorFactory,
    CityFactory,
    CommentFactory,
    CountryFactory,
    FilmFactory,
    InventoryFactory,
    StaffMemberFactory,
    StoreFactory,
    UserFactory,
)
from tests.test_app.models import (
    Actor,
    City,
    Comment,
    Country,
    Film,
    Inventory,
    StaffMember,
    Store,
    User,
)

from .utils import TrackingTestUtils


class TestRelationTracking(TrackingTestUtils):
    domains = {"relations": {"handler": "qorme_django.domains.relations.RelationTracking"}}

    def test_only(self):
        ActorFactory(last_name="Doa")

        with self.context:
            actor = Actor.objects.only("first_name").first()
            self.assertEqual(actor.last_name, "Doa")

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Actor")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Actor")
        self.assertEqual(relation.from_field, "last_name")
        self.assertTrue(relation.from_deferred)

    def test_defer(self):
        ActorFactory(first_name="Am")

        with self.context:
            actor = Actor.objects.defer("first_name").first()
            self.assertEqual(actor.first_name, "Am")

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Actor")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Actor")
        self.assertEqual(relation.from_field, "first_name")
        self.assertTrue(relation.from_deferred)

    def test_forward_many_to_one(self):
        """Test forward many-to-one relationships (ForeignKey)."""
        # Access from class
        self.assertIsNotNone(City.country)
        country = CountryFactory()
        CityFactory(country=country)

        with self.context:
            city = City.objects.last()
            self.assertEqual(city.country, country)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.City")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.City")
        self.assertEqual(relation.from_field, "country")
        self.assertFalse(relation.from_deferred)

    def test_forward_one_to_one(self):
        """Test forward one-to-one relationships."""
        # Access from class
        self.assertIsNotNone(StaffMember.user)
        user = UserFactory()
        StaffMemberFactory(user=user)

        with self.context:
            staff_member = StaffMember.objects.last()
            self.assertEqual(staff_member.user, user)
            new_user = UserFactory()
            self.assertNotEqual(staff_member.user, new_user)
            staff_member.user = new_user
            self.assertEqual(staff_member.user, new_user)
            staff_member.user = None

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.StaffMember")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.StaffMember")
        self.assertEqual(relation.from_field, "user")
        self.assertFalse(relation.from_deferred)

    def test_reverse_one_to_one(self):
        """Test reverse one-to-one relationships."""
        # Access from class
        self.assertIsNotNone(User.staff_member)
        staff_member = StaffMemberFactory(user=UserFactory())

        with self.context:
            user = User.objects.last()
            self.assertEqual(user.staff_member, staff_member)
            new_staff_member = StaffMemberFactory()
            self.assertNotEqual(user.staff_member, new_staff_member)
            user.staff_member = new_staff_member
            self.assertEqual(user.staff_member, new_staff_member)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.User")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.User")
        self.assertEqual(relation.from_field, "staff_member")
        self.assertFalse(relation.from_deferred)

    def test_reverse_many_to_one(self):
        """Test reverse many-to-one relationships."""
        # Access from class
        self.assertIsNotNone(Country.cities)
        country = CountryFactory()
        city_list = CityFactory.create_batch(2, country=country)

        with self.context:
            country = Country.objects.get(pk=country.pk)
            self.assertQuerySetEqual(country.cities.all(), city_list, ordered=False)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        # Check relation
        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Country")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Country")
        self.assertEqual(relation.from_field, "cities")
        self.assertFalse(relation.from_deferred)

    def test_many_to_many(self):
        """Test many-to-many relationships."""
        # Access from class
        self.assertIsNotNone(Film.actors)
        actors = ActorFactory.create_batch(2)
        film = FilmFactory(actors=actors)

        with self.context:
            film = Film.objects.last()
            for actor in film.actors.iterator():
                self.assertIn(film, actor.films.all())

        trackers = self.queries
        self.assertEqual(len(trackers), 2 + len(actors))

        # Check relations
        self.assertIsNone(trackers[0].data.relation)

        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Film")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Film")
        self.assertEqual(relation.from_field, "actors")
        self.assertFalse(relation.from_deferred)

        for i in range(len(actors)):
            relation = trackers[2 + i].data.relation
            self.assertEqual(relation.from_query_ts, trackers[1].data.timestamp)
            self.assertEqual(relation.from_query_uid, trackers[1].data.uid)
            self.assertEqual(relation.path, "test_app.Film__actors")
            self.assertEqual(relation.depth, 2)
            self.assertEqual(relation.from_model, "test_app.Actor")
            self.assertEqual(relation.from_field, "films")
            self.assertFalse(relation.from_deferred)

    def test_reverse_generic_many_to_one(self):
        """Test reverse generic many-to-one relationships."""
        # Access from class
        self.assertIsNotNone(Film.comments)
        film = FilmFactory()

        with self.context:
            film = Film.objects.last()
            CommentFactory.create_batch(2, content_object=film)

            for comment in film.comments.all():
                self.assertEqual(comment.object_id, film.pk)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)
        self.assertIsNone(trackers[0].data.relation)

        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Film")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Film")
        self.assertEqual(relation.from_field, "comments")
        self.assertFalse(relation.from_deferred)

    # Generic FKs not supported
    @unittest.expectedFailure
    def test_generic_foreign_key(self):
        """Test generic foreign key relationships."""
        # Access from class
        self.assertIsNotNone(Store.comments)
        store = StoreFactory()
        CommentFactory(content_object=store)

        with self.context:
            comment = Comment.objects.last()
            self.assertEqual(comment.content_object, store)
            comment.content_object = StoreFactory()
            self.assertNotEqual(comment.content_object, store)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Comment")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Comment")
        self.assertEqual(relation.from_field, "content_object")
        self.assertFalse(relation.from_deferred)

    def test_leaks(self):
        handler = self.manager.get_domain_handler("django.relations")
        num_wrapped = len(handler.wrapper)

        with self.context:
            StoreFactory.create_batch(3)
            for store in Store.objects.all():
                self.assertEqual(store.comments.count(), 0)

            CityFactory.create_batch(3)
            for city in City.objects.all():
                self.assertIsNotNone(city.country)

            for _i in range(3):
                FilmFactory(actors=ActorFactory.create_batch(2))

            for film in Film.objects.all():
                self.assertEqual(film.actors.count(), 2)

            # Clear references
            store = city = film = None

        gc.collect()
        num_model_tracked = 6
        self.assertEqual(len(handler.wrapper), num_wrapped + num_model_tracked)

    def test_prefetch_related(self):
        CityFactory.create_batch(2, country=CountryFactory())

        with self.context:
            country = Country.objects.prefetch_related("cities").get()
            self.assertEqual(len(country.cities.all()), 2)

        trackers = self.queries
        self.assertEqual(len(trackers), 2)

        self.assertIsNone(trackers[0].data.relation)
        relation = trackers[1].data.relation
        self.assertEqual(relation.from_query_ts, trackers[0].data.timestamp)
        self.assertEqual(relation.from_query_uid, trackers[0].data.uid)
        self.assertEqual(relation.path, "test_app.Country")
        self.assertEqual(relation.depth, 1)
        self.assertEqual(relation.from_model, "test_app.Country")
        self.assertEqual(relation.from_field, "cities")
        self.assertFalse(relation.from_deferred)

    def test_prefetch_related_2(self):
        stores = StoreFactory.create_batch(2)
        for store in stores:
            StaffMemberFactory.create_batch(2, store=store)

        with self.context:
            stores = Store.objects.prefetch_related("staff_members__address__city__country")
            self.assertEqual(len(stores), 2)
            for store in stores:
                for staff_member in store.staff_members.all():
                    self.assertIsNotNone(staff_member.address.city.country)

        trackers = self.queries
        self.assertEqual(len(trackers), 5)

        self.assertIsNone(trackers[0].data.relation)
        for i, (path, model, field) in enumerate(
            [
                ("test_app.Store", "test_app.Store", "staff_members"),
                ("test_app.Store__staff_members", "test_app.StaffMember", "address"),
                ("test_app.Store__staff_members__address", "test_app.Address", "city"),
                (
                    "test_app.Store__staff_members__address__city",
                    "test_app.City",
                    "country",
                ),
            ]
        ):
            relation = trackers[i + 1].data.relation
            self.assertEqual(relation.from_query_ts, trackers[i].data.timestamp)
            self.assertEqual(relation.from_query_uid, trackers[i].data.uid)
            self.assertEqual(relation.path, path)
            self.assertEqual(relation.depth, i + 1)
            self.assertEqual(relation.from_model, model)
            self.assertEqual(relation.from_field, field)
            self.assertFalse(relation.from_deferred)

    def test_depth_and_path(self):
        """Test depth and path tracking in relations."""
        InventoryFactory()
        with self.context:
            inventory = Inventory.objects.get()
            self.assertIsNotNone(inventory.store.address.city.country)

        path = Inventory._meta.label
        trackers = self.queries
        prev_relation = None
        self.assertEqual(len(trackers), 5)
        self.assertIsNone(trackers[0].data.relation)
        for i in range(1, len(trackers)):
            relation = trackers[i].data.relation
            self.assertIsNotNone(relation)
            if prev_relation:
                path += f"__{prev_relation.from_field}"
            self.assertEqual(relation.path, path)
            self.assertEqual(relation.depth, i)
            self.assertEqual(relation.from_query_uid, trackers[i - 1].data.uid)
            prev_relation = relation
