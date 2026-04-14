import tempfile

SECRET_KEY = "django-insecure-2p1&(r-6(88=)txivii25r^o%4-&00u5vgs#n93r#t8+y0"

DEBUG = False

INSTALLED_APPS = [
    # "qorme_django",
    "tests.test_app",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATIC_URL = "/static/"

MEDIA_ROOT = tempfile.TemporaryDirectory().name

ROOT_URLCONF = "tests.test_app.urls"

AUTH_USER_MODEL = "test_app.User"

USE_TZ = True
