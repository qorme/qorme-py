from django.apps import AppConfig
from django.conf import settings

from qorme.manager import TrackingManager
from qorme_django.defaults import QORME_DJANGO_SETTINGS


class QormeDjangoConfig(AppConfig):
    name = "qorme_django"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        TrackingManager.install(
            settings=getattr(settings, "QORME", {}), defaults=QORME_DJANGO_SETTINGS
        )
