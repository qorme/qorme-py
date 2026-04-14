import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    pass


class Language(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True)


class Category(TimeStampedModel):
    name = models.CharField(max_length=25, unique=True)


class Country(TimeStampedModel):
    country = models.CharField(max_length=50, unique=True)


class City(TimeStampedModel):
    city = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["city", "country"], name="unique_city_country")
        ]


class Address(TimeStampedModel):
    # TODO: Rename to ContactDetails
    address = models.CharField(max_length=50)
    address_2 = models.CharField(max_length=50, blank=True, null=True)
    district = models.CharField(max_length=20)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="addresses")
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True)


class Actor(TimeStampedModel):
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)

    class Meta:
        indexes = [models.Index(fields=["last_name"], name="idx_actor_last_name")]


class Film(TimeStampedModel):
    class Rating(models.TextChoices):
        GENERAL_AUDIENCES = "G", "General Audiences"
        PARENTAL_GUIDANCE_SUGGESTED = "PG", "Parental Guidance Suggested"
        PARENTS_STRONGLY_CAUTIONED = "PG-13", "Parents Strongly Cautioned"
        RESTRICTED = "R", "Restricted"
        ADULTS_ONLY = "NC-17", "Adults Only"

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    release_year = models.PositiveSmallIntegerField(
        null=True, validators=[MinValueValidator(1900), MaxValueValidator(2025)]
    )
    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name="films")
    original_language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, related_name="original_films"
    )
    rental_duration = models.DurationField(default=timedelta(days=3))
    rental_rate = models.DecimalField(max_digits=4, decimal_places=2, default="4.99")
    length = models.SmallIntegerField(blank=True, null=True)
    replacement_cost = models.DecimalField(max_digits=5, decimal_places=2, default="19.99")
    rating = models.CharField(
        choices=Rating.choices, default=Rating.GENERAL_AUDIENCES, max_length=5
    )
    special_features = models.CharField(max_length=100, blank=True, null=True)
    imdb_url = models.URLField()
    actors = models.ManyToManyField(Actor, related_name="films")
    categories = models.ManyToManyField(Category, related_name="films")
    comments = GenericRelation("Comment")


class StaffMember(TimeStampedModel):
    user = models.OneToOneField(User, related_name="staff_member", on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    picture = models.ImageField(upload_to="staff", blank=True, null=True)
    store = models.ForeignKey("Store", on_delete=models.PROTECT, related_name="staff_members")


class Store(TimeStampedModel):
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    manager = models.ForeignKey(
        StaffMember, on_delete=models.SET_NULL, null=True, related_name="managed_store"
    )
    comments = GenericRelation("Comment")


class Inventory(TimeStampedModel):
    film = models.ForeignKey(Film, on_delete=models.PROTECT, related_name="inventory_items")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="inventory_items")

    class Meta:
        indexes = [models.Index(fields=["store", "film"], name="idx_store_film")]


class Customer(TimeStampedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.EmailField(blank=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="customers")
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["last_name"], name="idx_customer_last_name")]


class Comment(models.Model):
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey()


class Rental(TimeStampedModel):
    rental_date = models.DateTimeField()
    rental_duration = models.DurationField()
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT, related_name="rentals")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="rentals")
    return_date = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="processed_rentals"
    )

    class Meta:
        unique_together = (("rental_date", "inventory", "customer"),)


class Payment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="payments")
    processed_by = models.ForeignKey(
        StaffMember, on_delete=models.PROTECT, related_name="processed_payments"
    )
    rental = models.ForeignKey(
        Rental, on_delete=models.SET_NULL, null=True, related_name="payments"
    )
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_info = models.JSONField()


# Multi-table inheritance models for testing parent pointers
class Task(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)


class GroupApprovalTask(Task):
    groups = models.ManyToManyField("auth.Group", related_name="approval_tasks")
