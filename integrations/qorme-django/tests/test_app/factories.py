from datetime import timedelta, timezone

import factory
from django.contrib.contenttypes.models import ContentType
from factory import fuzzy
from factory.django import DjangoModelFactory

from tests.test_app import models


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = models.Language

    name = factory.Sequence(lambda n: factory.Faker._get_faker().unique.language_name())


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Category

    name = factory.Sequence(lambda n: factory.Faker._get_faker().unique.word())


class CountryFactory(DjangoModelFactory):
    class Meta:
        model = models.Country

    country = factory.Sequence(lambda n: factory.Faker._get_faker().unique.country())


class CityFactory(DjangoModelFactory):
    class Meta:
        model = models.City

    city = factory.Sequence(lambda n: factory.Faker._get_faker().unique.city())
    country = factory.SubFactory(CountryFactory)


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = models.Address

    address = factory.Faker("street_address")
    address_2 = factory.Faker("secondary_address")
    district = factory.Faker("state")
    city = factory.SubFactory(CityFactory)
    postal_code = factory.Faker("postcode")
    phone = factory.Sequence(lambda n: f"+1555{n:06d}")


class ActorFactory(DjangoModelFactory):
    class Meta:
        model = models.Actor

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class FilmFactory(DjangoModelFactory):
    class Meta:
        model = models.Film

    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    release_year = factory.Faker("random_int", min=1900, max=2025)
    language = factory.SubFactory(LanguageFactory)
    original_language = factory.SubFactory(LanguageFactory)
    rental_duration = factory.Faker("time_delta")
    rental_rate = fuzzy.FuzzyDecimal(0.99, 9.99, 2)
    length = factory.Faker("random_int", min=60, max=180)
    replacement_cost = fuzzy.FuzzyDecimal(9.99, 29.99, 2)
    rating = fuzzy.FuzzyChoice([x[0] for x in models.Film.Rating.choices])
    special_features = factory.LazyFunction(
        lambda: ",".join(factory.Faker._get_faker().words(nb=3))
    )
    imdb_url = factory.Faker("url")
    slug = factory.LazyAttribute(lambda obj: factory.Faker._get_faker().slug())

    @factory.post_generation
    def actors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for actor in extracted:
                self.actors.add(actor)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class StaffMemberFactory(DjangoModelFactory):
    class Meta:
        model = models.StaffMember

    user = factory.SubFactory(UserFactory)
    address = factory.SubFactory(AddressFactory)
    picture = factory.django.ImageField(filename="staff_photo.jpg")
    store = factory.SubFactory("tests.test_app.factories.StoreFactory")


class StoreFactory(DjangoModelFactory):
    class Meta:
        model = models.Store

    address = factory.SubFactory(AddressFactory)


class InventoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Inventory

    film = factory.SubFactory(FilmFactory)
    store = factory.SubFactory(StoreFactory)


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = models.Customer

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    address = factory.SubFactory(AddressFactory)
    store = factory.SubFactory(StoreFactory)
    created_at = factory.Faker("date_time_this_decade", tzinfo=timezone.utc)


class RentalFactory(DjangoModelFactory):
    class Meta:
        model = models.Rental

    rental_date = factory.Faker("date_time_this_year", tzinfo=timezone.utc)
    inventory = factory.SubFactory(InventoryFactory)
    customer = factory.SubFactory(CustomerFactory)
    return_date = factory.LazyAttribute(
        lambda obj: obj.rental_date
        + timedelta(days=factory.Faker._get_faker().random_int(min=1, max=14))
    )
    processed_by = factory.SubFactory(StaffMemberFactory)
    rental_duration = factory.LazyAttribute(
        lambda obj: obj.return_date - obj.rental_date if obj.return_date else None
    )


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = models.Payment

    customer = factory.SubFactory(CustomerFactory)
    processed_by = factory.SubFactory(StaffMemberFactory)
    rental = factory.SubFactory(RentalFactory)
    amount = fuzzy.FuzzyDecimal(0.99, 9.99, 2)
    payment_date = factory.LazyAttribute(
        lambda obj: obj.rental.rental_date
        + timedelta(minutes=factory.Faker._get_faker().random_int(min=1, max=60))
    )
    payment_info = factory.LazyFunction(
        lambda: {
            "transaction_id": factory.Faker._get_faker().uuid4(),
            "payment_method": factory.Faker._get_faker().random_element(
                elements=["credit_card", "debit_card", "cash", "paypal"]
            ),
            "card_type": factory.Faker._get_faker().random_element(
                elements=["visa", "mastercard", "amex"]
            ),
            "card_last_four": factory.Faker._get_faker().credit_card_number(card_type=None)[-4:],
            "status": "completed",
            "timestamp": factory.Faker._get_faker().iso8601(),
        }
    )


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = models.Comment

    text = factory.Faker("paragraph")
    date = factory.Faker("date_time_this_year", tzinfo=timezone.utc)
    customer = factory.SubFactory(CustomerFactory)

    # Default to Film as the content_object, but can be overridden
    content_object = factory.SubFactory(FilmFactory)

    @factory.lazy_attribute
    def content_type(self):
        return ContentType.objects.get_for_model(self.content_object.__class__)

    @factory.lazy_attribute
    def object_id(self):
        return self.content_object.id


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = models.Task

    name = factory.Faker("sentence", nb_words=3)


class GroupApprovalTaskFactory(TaskFactory):
    class Meta:
        model = models.GroupApprovalTask
