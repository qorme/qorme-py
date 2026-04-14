from unittest.mock import patch

from django.core.management import call_command

from qorme.context.types import ContextType
from tests.test_app.factories import FilmFactory

from .utils import TrackingTestUtils, capture_query_trackers


class TestCLI(TrackingTestUtils):
    domains = {"cli": {"handler": "qorme_django.domains.cli.CLITracking"}}

    def test_command_execution_tracking(self):
        """Test that management command execution is properly tracked."""
        FilmFactory.create_batch(2)

        # Execute command
        with capture_query_trackers():
            context, stdout_mock = call_command("test_command")

        # Check command execution output.
        stdout_mock.write.assert_any_call("%i films", 2)

        # Check context data
        self.assertEqual(context.data.name, "tests.test_app.test_command")
        self.assertEqual(context.data.type, ContextType.CLI)

        # Verify queries were tracked
        self.assertEqual(len(self.queries), 1)  # One query to fetch films

    def test_django_core_command_no_tracking(self):
        """Test that Django core commands are not tracked."""
        with (
            patch("qorme_django.domains.cli.QueryContext") as mock_tracker,
            patch(
                "django.core.management.commands.migrate.Command.handle", return_value=None
            ) as mock_handle,
        ):
            # Execute a Django core command
            call_command("migrate")

            # Verify handle was called
            mock_handle.assert_called_once()

            # Verify Context was not initialized
            mock_tracker.assert_not_called()
