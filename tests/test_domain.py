import unittest
from unittest.mock import Mock, patch

from qorme.deps import Deps
from qorme.domain import Domain
from qorme.utils.config import Config


class DummyTracking(Domain):
    """Dummy domain implementation for testing."""

    name = "dummy"


class TestTrackingDomain(unittest.TestCase):
    def setUp(self):
        super().setUp()
        config = Config("test-dummy", data={"test": {}}, defaults={})
        self.domain = DummyTracking(deps=Deps(config), config=config.test)

    def test_enable_disable_lifecycle(self):
        with (
            patch.object(self.domain, "install_wrappers") as mock_install,
            patch.object(self.domain, "register_event_handlers") as mock_register,
        ):
            self.assertTrue(self.domain.enable())
            self.assertTrue(self.domain.enabled)
            mock_install.assert_called_once()
            mock_register.assert_called_once()

            # Second enable should fail
            self.assertFalse(self.domain.enable())
            mock_install.assert_called_once()
            mock_register.assert_called_once()

        with (
            patch.object(self.domain, "uninstall_wrappers") as uninstall_mock,
            patch.object(self.domain, "unregister_event_handlers") as unregister_mock,
        ):
            self.assertTrue(self.domain.disable())
            self.assertFalse(self.domain.enabled)
            uninstall_mock.assert_called_once()
            unregister_mock.assert_called_once()

            self.assertFalse(self.domain.disable())
            uninstall_mock.assert_called_once()
            unregister_mock.assert_called_once()

    def test_enable_atomic_behavior(self):
        class InstallError(Exception):
            pass

        class EnableHookError(Exception):
            pass

        # Test failure during install_wrappers
        with patch.object(self.domain, "install_wrappers") as mock_install:
            mock_install.side_effect = InstallError("Install failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.enable())
                self.assertIn("Failed to install wrappers for the dummy domain", log.output[0])

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)

        # Test failure during register_event_handlers
        with (
            patch.object(self.domain, "register_event_handlers") as mock_register,
            patch.object(self.domain, "unregister_event_handlers") as unregister_mock,
        ):
            mock_register.side_effect = EnableHookError("Enable hook failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.enable())
                self.assertIn(
                    "Failed to register event handlers for the dummy domain", log.output[0]
                )

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)
            unregister_mock.assert_called_once()

    def test_disable_atomic_behavior(self):
        # Setup initial state
        test_obj = Mock()
        test_obj.method = lambda: "original"

        # Enable self.domain and add a wrapper
        self.domain.enable()
        self.domain.wrapper.wrap(test_obj, "method", lambda *args: "wrapped")

        class DisableHookError(Exception):
            pass

        class UninstallError(Exception):
            pass

        # Test failure during unregister_event_handlers
        with patch.object(self.domain, "unregister_event_handlers") as unregister_mock:
            unregister_mock.side_effect = DisableHookError("Disable hook failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.disable())
                self.assertIn(
                    "Failed to unregister event handlers for the dummy domain", log.output[0]
                )

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)
            self.assertEqual(test_obj.method(), "original")

        # Re-enable self.domain for the next test
        self.domain.enable()

        # Test failure during uninstall_wrappers
        with patch.object(self.domain, "uninstall_wrappers") as uninstall_mock:
            uninstall_mock.side_effect = UninstallError("Uninstall failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.disable())
                self.assertIn("Failed to uninstall wrappers for the dummy domain", log.output[0])

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)
            self.assertEqual(test_obj.method(), "original")

    def test_enable_fails_during_install_wrappers(self):
        class InstallError(Exception):
            pass

        with patch.object(self.domain, "install_wrappers") as mock_install:
            mock_install.side_effect = InstallError("Install failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.enable())
                self.assertIn("Failed to install wrappers for the dummy domain", log.output[0])

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)

    def test_enable_fails_during_register_event_handlers(self):
        class EnableHookError(Exception):
            pass

        with (
            patch.object(self.domain, "register_event_handlers") as mock_register,
            patch.object(self.domain, "unregister_event_handlers") as unregister_mock,
        ):
            mock_register.side_effect = EnableHookError("Enable hook failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.enable())
                self.assertIn(
                    "Failed to register event handlers for the dummy domain", log.output[0]
                )

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)
            unregister_mock.assert_called_once()

    def test_disable_fails_during_unregister_event_handlers(self):
        test_obj = Mock()
        test_obj.method = lambda: "original"

        self.domain.enable()
        self.domain.wrapper.wrap(test_obj, "method", lambda *args: "wrapped")

        class DisableHookError(Exception):
            pass

        with patch.object(self.domain, "unregister_event_handlers") as unregister_mock:
            unregister_mock.side_effect = DisableHookError("Disable hook failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.disable())
                self.assertIn(
                    "Failed to unregister event handlers for the dummy domain", log.output[0]
                )

            self.assertFalse(self.domain.enabled)
            self.assertEqual(len(self.domain.wrapper), 0)
            self.assertEqual(test_obj.method(), "original")

    def test_disable_fails_during_uninstall_wrappers(self):
        test_obj = Mock()
        test_obj.method = lambda: "original"

        def wrapper(*args):
            return "wrapped"

        self.domain.enable()
        self.domain.wrapper.wrap(test_obj, "method", wrapper)

        class UninstallError(Exception):
            pass

        with patch.object(self.domain, "uninstall_wrappers") as uninstall_mock:
            uninstall_mock.side_effect = UninstallError("Uninstall failed")

            with self.assertLogs(level="WARNING") as log:
                self.assertFalse(self.domain.disable())
                self.assertIn("Failed to uninstall wrappers for the dummy domain", log.output[0])

            self.assertFalse(self.domain.enabled)
            # Unwrapping failed
            self.assertEqual(test_obj.method(), "wrapped")
            self.assertTrue(self.domain.wrapper.unwrap(test_obj, "method"))
