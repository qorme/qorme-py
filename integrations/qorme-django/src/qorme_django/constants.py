# List of modules that will be ignored if they are at the top of a stacktrace.
IGNORE_MODULES_IN_TRACEBACK = [
    "qorme_django",
    "django/db",
    "django/template",
    "django/test/",
    "django/core/servers",
    "django/core/handlers",
    "django/core/management",
    "django/contrib/staticfiles",
    "django/utils/deprecation.py",
    "manage.py",
]

# Set of descriptors that are known to work nicely with Qorme
# field descriptors patching for columns access tracking.
KNOWN_DESCRIPTORS = {
    "django_countries.fields.CountryDescriptor",
    "phonenumber_field.modelfields.PhoneNumberDescriptor",
    "taggit.managers._TaggableManager",
    "wagtail.fields.Creator",
}
