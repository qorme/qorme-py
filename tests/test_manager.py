import unittest
from unittest.mock import patch

from qorme.domain import Domain
from qorme.manager import TrackingManager


class TestModel:
    def __init__(self) -> None:
        self.save_calls = 0

    def save(self):
        return True


class NumCallsTracking(Domain):
    """A simple tracker that keeps count of calls."""

    name = "test_tracking"

    def install_wrappers(self) -> None:
        self.wrapper.wrap(TestModel, "save", self._save_wrapper)

    def _save_wrapper(self, wrapped, instance, args, kwargs):
        instance.save_calls += 1
        return wrapped(*args, **kwargs)


class DummyTracking(Domain):
    """A dummy tracker that does nothing."""

    name = "dummy_tracking"


class TestTrackingManager(unittest.TestCase):
    def create_manager(self, settings=None, defaults=None):
        if settings is None:
            settings = {
                "domains": ["test_tracking"],
                "test_tracking": {"handler": "tests.test_manager.NumCallsTracking"},
            }
        settings.setdefault("deps", {})
        return TrackingManager(settings=settings, defaults=defaults if defaults is not None else {})

    def test_start_domain_tracking(self):
        manager = self.create_manager()

        self.assertTrue(manager.start_domain_tracking("test_tracking"))
        self.assertIn("test_tracking", manager.domains)

        # Cleanup
        self.assertTrue(manager.stop_domain_tracking("test_tracking"))
        self.assertIsNone(manager.get_domain_handler("test_tracking"))

    def test_start_unexisting_domain(self):
        manager = self.create_manager()
        self.assertFalse(manager.start_domain_tracking("unexisting_domain"))
        self.assertIsNone(manager.get_domain_handler("unexisting_domain"))

    def test_start_domain_tracking_invalid_handler_class(self):
        """Test handling of import errors in domain tracking"""
        manager = self.create_manager(
            settings={"bad_domain": {"handler": "nonexistent.module.Handler"}}
        )

        with self.assertLogs(level="WARNING") as cm:
            self.assertFalse(manager.start_domain_tracking("bad_domain"))
            self.assertIn("Failed to import handler class for bad_domain domain", cm.output[0])
            self.assertIsNone(manager.get_domain_handler("bad_domain"))

    def test_start_domain_tracking_initialization_error(self):
        manager = self.create_manager()

        with (
            patch.object(
                NumCallsTracking,
                "__init__",
                side_effect=Exception("Initialization error"),
            ),
            self.assertLogs(level="WARNING") as cm,
        ):
            self.assertFalse(manager.start_domain_tracking("test_tracking"))
            self.assertIn("Failed initializing test_tracking domain handler", cm.output[0])
            self.assertIsNone(manager.get_domain_handler("test_tracking"))

    def test_start_domain_tracking_enable_error(self):
        manager = self.create_manager()

        with (
            patch.object(NumCallsTracking, "enable", side_effect=Exception("Enable error")),
            self.assertLogs(level="WARNING") as cm,
        ):
            self.assertFalse(manager.start_domain_tracking("test_tracking"))
            self.assertIn(
                "Caught error while enabling the test_tracking domain",
                cm.output[0],
            )
            self.assertIn("Exception: Enable error", cm.output[0])
            self.assertIsNone(manager.get_domain_handler("test_tracking"))

    def test_start_domain_tracking_failed_enable(self):
        manager = self.create_manager()

        with (
            patch.object(NumCallsTracking, "enable", return_value=False),
            self.assertLogs(level="WARNING") as cm,
        ):
            self.assertFalse(manager.start_domain_tracking("test_tracking"))
            self.assertIn("Failed to enable the test_tracking domain", cm.output[0])
            self.assertIsNone(manager.get_domain_handler("test_tracking"))

    def test_stop_domain_tracking_unexisting_domain(self):
        manager = self.create_manager()
        self.assertFalse(manager.stop_domain_tracking("unexisting_domain"))

    def test_stop_domain_tracking_error_on_disable(self):
        manager = self.create_manager()
        manager.start_domain_tracking("test_tracking")
        handler = manager.get_domain_handler("test_tracking")

        with (
            patch.object(NumCallsTracking, "disable", side_effect=Exception("Disable error")),
            self.assertLogs(level="WARNING") as cm,
        ):
            self.assertFalse(manager.stop_domain_tracking("test_tracking"))
            self.assertIn(
                "Caught Exception('Disable error') while disabling the test_tracking domain",
                cm.output[0],
            )
            self.assertIsNone(manager.get_domain_handler("test_tracking"))

        self.assertTrue(handler.disable())

    def test_stop_domain_tracking_failed_disable(self):
        manager = self.create_manager()
        manager.start_domain_tracking("test_tracking")
        handler = manager.get_domain_handler("test_tracking")

        with (
            patch.object(NumCallsTracking, "disable", return_value=False),
            self.assertLogs(level="WARNING") as cm,
        ):
            self.assertFalse(manager.stop_domain_tracking("test_tracking"))
            self.assertIn("Domain test_tracking was already disabled", cm.output[0])
            self.assertIsNone(manager.get_domain_handler("test_tracking"))

        self.assertTrue(handler.disable())

    def test_start_stop(self):
        manager = self.create_manager(
            settings={
                "domains": ["queries", "test_tracking"],
                "queries": {"handler": "tests.test_manager.DummyTracking"},
                "test_tracking": {"handler": "tests.test_manager.NumCallsTracking"},
            }
        )

        self.assertTrue(manager.start())
        self.assertTrue(manager.active)
        self.assertEqual(len(manager.domain_handlers), 2)
        self.assertIsInstance(manager.get_domain_handler("queries"), DummyTracking)
        self.assertIsInstance(manager.get_domain_handler("test_tracking"), NumCallsTracking)

        self.assertTrue(manager.stop())
        self.assertFalse(manager.active)
        self.assertEqual(len(manager.domain_handlers), 0)

    def test_start_inactive(self):
        manager = self.create_manager(settings={"active": False})

        self.assertFalse(manager.start())

    def test_stop_inactive(self):
        manager = self.create_manager()

        self.assertFalse(manager.stop())
        self.assertFalse(manager.active)
        self.assertEqual(len(manager.domain_handlers), 0)

    def test_warns_on_unstopped_instance(self):
        manager = self.create_manager()
        manager.start()
        handler = manager.get_domain_handler("test_tracking")

        with self.assertLogs(level="WARNING") as cm:
            manager_repr = repr(manager)
            handler.manager = None
            del manager
            self.assertIn(
                f"TrackingManager instance {manager_repr} was not properly stopped", cm.output[0]
            )

        self.assertTrue(handler.disable())

    def test_tracking_lifecycle(self):
        manager = self.create_manager()
        self.assertTrue(manager.start())

        # Perform some model operations
        test_model = TestModel()
        test_model.save()

        # Verify tracking
        self.assertEqual(test_model.save_calls, 1)

        # Stop tracking
        self.assertTrue(manager.stop())

        # Verify tracking stopped
        test_model.save()
        self.assertEqual(test_model.save_calls, 1)  # Count shouldn't increase
