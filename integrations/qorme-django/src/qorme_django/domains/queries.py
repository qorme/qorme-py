import logging
from collections.abc import Iterable
from functools import cache

from django.db.models import Model, query
from django.db.models.query import QuerySet

from qorme.context.tracking import get_query_context
from qorme.domain import Domain
from qorme.orm.tracking import ORMQuery
from qorme.orm.types import QueryType, RowType
from qorme.utils.config import ConfigurationError

logger = logging.getLogger(__name__)


@cache
def get_row_type(iterable_cls: type) -> RowType:
    if issubclass(iterable_cls, query.ModelIterable):
        return RowType.MODEL
    elif issubclass(iterable_cls, query.ValuesIterable):
        return RowType.DICT
    elif issubclass(iterable_cls, query.ValuesListIterable):
        return RowType.SEQUENCE
    elif issubclass(iterable_cls, query.FlatValuesListIterable):
        return RowType.SCALAR
    raise ValueError(f"Unknown iterable class: {iterable_cls}")


@cache
def get_query_type(method_name: str) -> QueryType:
    if method_name == "exists":
        return QueryType.EXISTS
    elif method_name == "count":
        return QueryType.COUNT
    raise ValueError(f"Unknown query type: {method_name}")


def get_joined_instances(
    query: "QuerySet", instance: "Model", select_related: bool | dict | None = None
) -> Iterable[tuple[str, "Model"]]:
    """
    Yield (field_name, related_instance) tuples for instances that were
    loaded via select_related in the current query.

    IMPORTANT: We only yield instances that are in select_related, not all
    cached relations in fields_cache. fields_cache may contain objects
    that were pre-populated by Django (e.g., when accessing through a
    reverse FK relation) but were NOT actually loaded via SQL JOIN.
    """
    if not select_related:
        # No select_related on this query (False or None), no joined instances
        return

    for rel_field, rel_instance in instance._state.fields_cache.items():
        if (rel_instance is not None) and (select_related is True or rel_field in select_related):
            # Either all relations were joined, or this specific one was
            yield rel_field, rel_instance


class QueryTracking(Domain):
    name = "django.queries"

    __slots__ = "_models", "_include_app", "_include_model"

    def setup(self):
        if self.config.apps_to_include and self.config.apps_to_exclude:
            raise ConfigurationError(
                "apps_to_include and apps_to_exclude are mutually exclusive. Got: "
                f"include={self.config.apps_to_include}, "
                f"exclude={self.config.apps_to_exclude}"
            )
        if self.config.models_to_include and self.config.models_to_exclude:
            raise ConfigurationError(
                "models_to_include and models_to_exclude are mutually exclusive. Got: "
                f"include={self.config.models_to_include}, "
                f"exclude={self.config.models_to_exclude}"
            )

        if self.config.apps_to_include:
            self._include_app = lambda model: model._meta.app_label in self.config.apps_to_include
        elif self.config.apps_to_exclude:
            self._include_app = (
                lambda model: model._meta.app_label not in self.config.apps_to_exclude
            )
        else:
            self._include_app = lambda _: True

        if self.config.models_to_include:
            self._include_model = (
                lambda model: self._include_app(model)
                or model._meta.label in self.config.models_to_include
            )
        elif self.config.models_to_exclude:
            self._include_model = (
                lambda model: self._include_app(model)
                or model._meta.label not in self.config.models_to_exclude
            )
        else:
            self._include_model = self._include_app

        self._models: dict[str, bool] = {}

    def install_wrappers(self):
        self.wrap_iterables()
        self.wrap_queryset_methods()
        self.wrap_model_get_state()

    def wrap_iterables(self):
        for iterable_cls in [
            query.ModelIterable,
            query.ValuesIterable,
            query.ValuesListIterable,
            query.FlatValuesListIterable,
            query.NamedValuesListIterable,
        ]:
            self.wrapper.wrap(iterable_cls, "__iter__", self._iterate_wrapper)

    def wrap_queryset_methods(self):
        self.wrapper.wrap(QuerySet, "exists", self._queryset_method_wrapper)
        self.wrapper.wrap(QuerySet, "count", self._queryset_method_wrapper)
        # self.wrapper.wrap(QuerySet, "__contains__", lambda: self._contains_wrapper)

    def wrap_model_get_state(self):
        self.wrapper.wrap(Model, "__getstate__", self._model_get_state_wrapper)

    def _iterate_wrapper(self, wrapped, instance, args, kwargs):
        """
        Creates a wrapper for queryset iteration methods.

        This wrapper tracks query execution and instance creation during queryset
        iteration. It's used to monitor SELECT queries that return multiple rows.

        Args:
            query_type: Type of query being executed
            row_type: Type of rows being returned

        Returns:
            A wrapper function that handles query tracking during iteration
        """

        qs = instance.queryset
        if self.skip_query(qs):
            yield from wrapped(*args, **kwargs)
            return

        row_type = get_row_type(type(instance))
        model = qs.model._meta.label
        query_tracker = ORMQuery(
            query=qs,
            model=model,
            row_type=row_type,
            query_type=QueryType.SELECT,
        )
        with query_tracker:
            if row_type != RowType.MODEL:
                yield from wrapped(*args, **kwargs)
                return

            seen = set()
            select_related = qs._query.select_related
            for obj in wrapped(*args, **kwargs):
                self.on_new_instance(obj, query_tracker, model, seen, select_related)
                yield obj

    def _queryset_method_wrapper(self, wrapped, instance, args, kwargs):
        """Returns a wrapper for Queryset.count and Queryset.exists."""

        if instance._result_cache is not None or self.skip_query(instance):
            return wrapped(*args, **kwargs)

        query_tracker = ORMQuery(
            query=instance,
            model=instance.model._meta.label,
            row_type=RowType.SCALAR,
            query_type=get_query_type(wrapped.__name__),
        )
        with query_tracker:
            return wrapped(*args, **kwargs)

    def _contains_wrapper(self, wrapped, instance, args, kwargs):
        """Simulates __contains__ behaviour on the Queryset class for result cache stats."""
        instance._fetch_all()
        return args[0] in instance._result_cache

    def _model_get_state_wrapper(self, wrapped, instance, args, kwargs):
        state = wrapped(*args, **kwargs)
        # TODO: Fix me. Ugly hack!
        # 1. Affect all models
        # 2. Includes logic from other domains
        state.pop("__query_tracker__", None)
        state.pop("__columns_accessed__", None)
        return state

    def skip_query(self, query: QuerySet) -> bool:
        if get_query_context(None) is None:
            return True
        self._track_model(query.model, query._query.select_related)
        return not self._models[query.model._meta.label]

    def _track_model(self, model: type[Model], select_related: bool | dict[str, dict]) -> None:
        if model._meta.label not in self._models:
            track_model = self._include_model(model)
            self._models[model._meta.label] = track_model
            if track_model:
                self.deps.events.on_track_model(model)
        if not isinstance(select_related, dict) or not self._models[model._meta.label]:
            # Model shouldn't be tracked, don't recurse in joined columns
            return
        for rel_name, sub_sel in select_related.items():
            field = model._meta.get_field(rel_name)
            rel_model = field.related_model
            if issubclass(rel_model, Model):
                self._track_model(rel_model, sub_sel)

    def on_new_instance(
        self,
        instance: "Model",
        query_tracker: "ORMQuery",
        path: str,
        seen: set,
        select_related=None,
    ):
        seen.add(id(instance))
        self.deps.events.on_new_instance(instance, path, query_tracker, select_related)
        for joined_field, joined_instance in get_joined_instances(
            query_tracker.query, instance, select_related
        ):
            if id(joined_instance) in seen:
                continue

            self.on_new_instance(
                joined_instance,
                query_tracker,
                f"{path}__{joined_field}" if path else joined_field,
                seen,
                (
                    select_related.get(joined_field)
                    if isinstance(select_related, dict)
                    else select_related
                ),
            )
