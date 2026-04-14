from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from django.template import Node

import qorme.utils.traceback as tb_utils
from qorme.context.tracking import get_query_context
from qorme.domain import Domain

if TYPE_CHECKING:
    from qorme.orm.tracking import ORMQuery


logger = logging.getLogger(__name__)


class TemplateTracking(Domain):
    name = "django.template"

    __slots__ = ()

    def register_event_handlers(self) -> None:
        self.deps.events.register_query_started_handler(self._query_started_handler)

    def unregister_event_handlers(self) -> None:
        self.deps.events.unregister_query_started_handler(self._query_started_handler)

    def install_wrappers(self) -> None:
        self._wrap_template_render()

    def _wrap_template_render(self) -> None:
        from django.template.backends.django import Template

        self.wrapper.wrap(Template, "render", self._template_render_wrapper)

    def _template_render_wrapper(self, wrapped, instance, args, kwargs):
        if not (context := get_query_context(None)) or context.get_state("in_template_render"):
            return wrapped(*args, **kwargs)

        with context.state(in_template_render=True):
            return wrapped(*args, **kwargs)

    def _query_started_handler(self, query_tracker: ORMQuery) -> None:
        if (
            (context := get_query_context(None))
            and context.get_state("in_template_render")
            and (template_info := self.get_template_info())
        ):
            query_tracker.data.template = template_info

    def get_template_info(self):
        # TODO: Rewrite the loop in Cython or find a way without loop.
        template_info = None
        frame = sys._getframe()

        while frame := frame.f_back:
            if frame.f_code.co_name != "render":
                continue

            node = frame.f_locals.get("self")
            if not isinstance(node, Node):
                continue

            # Hack to force SafeString to be a raw 'str'
            # to avoid encoding issues with msgspec.
            template_name = node.origin.template_name + ""
            lineno = node.token.lineno
            line = tb_utils.get_line(node.origin.name, lineno)
            template_info = tb_utils.TracebackEntry(template_name, "", line, lineno)
            break

        del frame
        return template_info
