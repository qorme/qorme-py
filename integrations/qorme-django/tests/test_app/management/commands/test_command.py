from unittest.mock import MagicMock

from django.core.management.base import BaseCommand

from qorme.context.tracking import get_query_context
from tests.test_app.models import Film


class Command(BaseCommand):
    help = "Test command that performs some database operations."

    def handle(self, *args, **options):
        # Hack so we don't have issues output the context returned.
        self.stdout = MagicMock()
        self.stdout.write("%i films", Film.objects.count())
        return get_query_context(None), self.stdout
