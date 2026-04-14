import unittest

from qorme.context.tracking import QueryContext
from qorme.context.types import ContextType
from qorme.contrib.celery.tracking import CeleryTracking
from qorme.deps import Deps
from qorme.utils.config import Config

from .app import add, ignored_task, multiply


class TestCeleryTracking(unittest.TestCase):
    config = Config(
        "test",
        data={
            "celery": {
                "tracking": {
                    "ignore_tasks": ["tests.contrib.celery.test_celery.ignored_task"],
                }
            }
        },
        defaults={
            "celery": {
                "tracking": {
                    "ignore_tasks": [],
                }
            }
        },
    )

    def setUp(self):
        self.deps = Deps(self.config)

        # Track created contexts
        self.contexts = []
        self.deps.events.register_context_created_handler(self.on_context_created)

        # Create and enable the domain
        self.domain = CeleryTracking(deps=self.deps, config=self.config.celery.tracking)
        self.domain.enable()

    def tearDown(self):
        self.domain.disable()
        super().tearDown()

    def on_context_created(self, context):
        self.contexts.append(context)

    def test_task_execution_tracking(self):
        """Test that task execution creates a QueryContext with correct attributes."""
        result = add.delay(2, 3)
        self.assertEqual(result.get(timeout=5), 5)

        # Verify context was created
        self.assertEqual(len(self.contexts), 1)
        context = self.contexts[0]

        # Check context type and attributes
        self.assertIsInstance(context, QueryContext)
        self.assertEqual(context.data.type, ContextType.TASK)
        self.assertEqual(context.data.name, add.name)

        # Check task-specific data
        self.assertIn("task_id", context.data.data)

    def test_ignored_task_not_tracked(self):
        """Test that tasks in ignore_tasks config are not tracked."""
        result = ignored_task.delay()
        self.assertEqual(result.get(timeout=5), "ignored")

        # Verify no context was created
        self.assertEqual(len(self.contexts), 0)

    def test_multiple_tasks_each_get_own_context(self):
        """Test that each task execution gets its own context."""
        results = [
            add.delay(1, 2),
            multiply.delay(3, 4),
            add.delay(5, 6),
        ]

        # Wait for all tasks to complete
        values = [r.get(timeout=5) for r in results]
        self.assertEqual(values, [3, 12, 11])

        # Verify each task got its own context
        self.assertEqual(len(self.contexts), 3)

        # Verify all contexts are QueryContext with TASK type
        for ctx in self.contexts:
            self.assertIsInstance(ctx, QueryContext)
            self.assertEqual(ctx.data.type, ContextType.TASK)
