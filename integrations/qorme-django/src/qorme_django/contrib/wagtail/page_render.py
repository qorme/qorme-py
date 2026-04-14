from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wagtail.models import Page

from qorme.context.tracking import QueryContext
from qorme.context.types import ContextType
from qorme.domain import Domain

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.template.response import TemplateResponse


class PageRender(Domain):
    name = "wagtail.page_render"

    __slots__ = ()

    def install_wrappers(self) -> None:
        self.wrapper.wrap(Page, "serve", self._serve_wrapper)

    def _serve_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Page,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        response = wrapped(*args, **kwargs)
        if hasattr(response, "render") and callable(response.render):
            # Attach the page instance to the response so we can access it during render
            # TODO: Use context state?
            response._qorme_page = instance
            # Wrap the render method of the response instance
            self.wrapper.wrap(response, "render", self._render_wrapper)
        return response

    def _render_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: TemplateResponse,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        if page := instance.__dict__.pop("_qorme_page", None):
            with QueryContext(
                name=str(page._meta.verbose_name),
                type=ContextType.HTTP,
                deps=self.deps,
            ):
                return wrapped(*args, **kwargs)

        return wrapped(*args, **kwargs)
