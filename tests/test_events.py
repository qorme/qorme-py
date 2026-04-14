import unittest
from unittest.mock import Mock

from qorme.events import Events, EventType


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.events = Events()

    def test_handler_exception_handling(self):
        """Test that exceptions in handlers are caught and logged."""
        handler_1 = Mock(side_effect=ValueError("Test error"))
        handler_2 = Mock()
        ctx_mock = Mock()

        self.events.register_context_created_handler(handler_1)
        self.events.register_context_created_handler(handler_2)

        with self.assertLogs(level="ERROR") as log:
            self.events.fire(EventType.CONTEXT_CREATED, ctx_mock)

        # Check that the exception was logged
        self.assertIn(
            f"Error in {handler_1} handler during EventType.CONTEXT_CREATED",
            log.records[0].getMessage(),
        )

        # Check that the second handler was still called
        handler_2.assert_called_once()

    def test_fire(self):
        event_types = [
            (
                EventType.CONTEXT_CREATED,
                self.events.register_context_created_handler,
                self.events.unregister_context_created_handler,
            ),
            (
                EventType.QUERY_DONE,
                self.events.register_query_done_handler,
                self.events.unregister_query_done_handler,
            ),
        ]
        for event_type, register, unregister in event_types:
            with self.subTest(event_type=event_type):
                handler = Mock()
                item_mock = Mock()

                # Register handler
                register(handler)

                # Fire event
                result = self.events.fire(event_type, item_mock)
                self.assertIsNone(result)

                handler.assert_called_once_with(item_mock)

                # Unregister handler
                unregister(handler)

                # Fire event
                self.events.fire(event_type, item_mock)

                handler.assert_called_once_with(item_mock)

    def test_multiple_handlers(self):
        handler_1 = Mock()
        handler_2 = Mock()
        ctx_mock = Mock()

        self.events.register_context_created_handler(handler_1)
        self.events.register_context_created_handler(handler_2)

        self.events.fire(EventType.CONTEXT_CREATED, ctx_mock)

        # Check that handlers were called with correct arguments
        handler_1.assert_called_once_with(ctx_mock)
        handler_2.assert_called_once_with(ctx_mock)

    def test_handler_registration_and_firing(self):
        """Test that handlers can be registered and fired for all event types."""
        for event_type in EventType:
            with self.subTest(event_type=event_type):
                event_name = event_type.value.lower()
                register_method_name = f"register_{event_name}_handler"
                unregister_method_name = f"unregister_{event_name}_handler"

                register_method = getattr(self.events, register_method_name)
                unregister_method = getattr(self.events, unregister_method_name)

                handler = Mock()
                mock_item = Mock()

                # Register handler
                register_method(handler)

                # Fire event
                self.events.fire(event_type, mock_item)

                # Check handler was called
                handler.assert_called_once_with(mock_item)

                # Unregister handler
                unregister_method(handler)

                # Fire event again
                handler.reset_mock()
                self.events.fire(event_type, mock_item)

                # Handler should not be called after unregistration
                handler.assert_not_called()

    def test_on_convenience_methods(self):
        """Test that on_* convenience methods work correctly and are equivalent to fire()."""
        for event_type in EventType:
            with self.subTest(event_type=event_type):
                event_name = event_type.value.lower()
                on_method_name = f"on_{event_name}"

                on_method = getattr(self.events, on_method_name)

                handler = Mock()
                mock_item1 = Mock()
                mock_item2 = Mock()

                # Register handler to test the on_* method
                register_method_name = f"register_{event_name}_handler"
                register_method = getattr(self.events, register_method_name)
                register_method(handler)

                # Test single item
                on_method(mock_item1)
                handler.assert_called_once_with(mock_item1)

                # Test multiple items
                handler.reset_mock()
                on_method(mock_item1, mock_item2)
                handler.assert_called_once_with(mock_item1, mock_item2)

                # Test that on_* method is equivalent to fire()
                handler.reset_mock()
                self.events.fire(event_type, mock_item1, mock_item2)
                expected_call = handler.call_args

                handler.reset_mock()
                on_method(mock_item1, mock_item2)
                actual_call = handler.call_args

                self.assertEqual(
                    expected_call,
                    actual_call,
                    f"on_{event_name} should be equivalent to fire({event_type.name})",
                )
