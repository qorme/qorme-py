from django.core import signals

from qorme.context.tracking import QueryContext, get_query_context
from qorme.context.types import ContextType
from qorme.domain import Domain


def get_view_name(resolver_match) -> str:
    """Extract a meaningful view name from the resolver match."""
    if not resolver_match:
        return ""
    if view := (resolver_match.view_name or resolver_match.url_name):
        return view
    return getattr(resolver_match.func, "__name__", "")


class RequestTracking(Domain):
    name = "django.requests"

    __slots__ = "ignore_paths"

    def setup(self):
        self.ignore_paths = set(self.config.ignore_paths)

    def install_wrappers(self) -> None:
        from django.core.handlers.base import BaseHandler

        self.wrapper.wrap(BaseHandler, "resolve_request", self._resolve_request_wrapper)

    def register_event_handlers(self) -> None:
        signals.request_finished.connect(self._request_finished_hook, weak=False)

    def unregister_event_handlers(self) -> None:
        signals.request_finished.disconnect(self._request_finished_hook)

    def _resolve_request_wrapper(self, wrapped, instance, args, kwargs):
        request = args[0] if args else kwargs.get("request")
        resolver_match = wrapped(*args, **kwargs)
        view_name = get_view_name(resolver_match) or request.path
        if view_name not in self.ignore_paths:
            QueryContext(
                name=view_name,
                deps=self.deps,
                type=ContextType.HTTP,
                method=request.method,
                path=request.path,
                url_name=resolver_match.url_name or "",
                query_string=request.META.get("QUERY_STRING", ""),
            ).__enter__()
        return resolver_match

    def _request_finished_hook(self, sender, **kwargs):
        if (context := get_query_context(None)) and context.data.type == ContextType.HTTP:
            context.__exit__(None, None, None)
