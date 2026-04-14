from django.core.management.base import BaseCommand

from qorme.context.tracking import QueryContext
from qorme.context.types import ContextType
from qorme.domain import Domain


class CLITracking(Domain):
    name = "django.cli"

    __slots__ = ()

    def install_wrappers(self):
        self.wrapper.wrap(BaseCommand, "execute", self._execute_command_wrapper)

    def _ignore_command(self, command_name: str) -> bool:
        return command_name.startswith("django.core")

    def _execute_command_wrapper(self, wrapped, instance, args, kwargs):
        command_name = instance.__module__.replace(".management.commands", "")
        if self._ignore_command(command_name):
            return wrapped(*args, **kwargs)

        with QueryContext(name=command_name, deps=self.deps, type=ContextType.CLI):
            return wrapped(*args, **kwargs)
