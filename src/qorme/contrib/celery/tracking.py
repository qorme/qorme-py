import logging

from celery import Task
from celery.signals import task_postrun, task_prerun

from qorme.context.tracking import QueryContext, get_query_context
from qorme.context.types import ContextType
from qorme.domain import Domain

logger = logging.getLogger(__name__)


class CeleryTracking(Domain):
    name = "celery.tracking"

    __slots__ = "ignore_tasks"

    def setup(self):
        self.ignore_tasks = set(self.config.ignore_tasks)

    def register_event_handlers(self) -> None:
        task_prerun.connect(self._task_prerun_handler, weak=False)
        task_postrun.connect(self._task_postrun_handler, weak=False)

    def unregister_event_handlers(self) -> None:
        task_prerun.disconnect(self._task_prerun_handler)
        task_postrun.disconnect(self._task_postrun_handler)

    def ignore_task(self, task_name: str) -> bool:
        return task_name in self.ignore_tasks

    def _task_prerun_handler(self, task_id: str, task: Task, args: tuple, kwargs: dict, **_):
        name = task.name
        if name and not self.ignore_task(name):
            QueryContext(name, self.deps, ContextType.TASK, task_id=task_id).__enter__()

    def _task_postrun_handler(self, task_id: str, **_):
        if (context := get_query_context(None)) and context.data.data.get("task_id") == task_id:
            context.__exit__(None, None, None)
