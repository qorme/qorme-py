from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor
from django.db.models.fields import related_descriptors

from qorme.domain import Domain
from qorme.orm.datastructures import Relation

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from django.db.models import Model

    from qorme.orm.tracking import ORMQuery

_NONE_INFO = "", 0, None, None


def get_parent_query_info(instance: Model, field) -> tuple[str, int, datetime | None, UUID | None]:
    return getattr(instance, "__rel_info__", _NONE_INFO)


def get_related_instance(queryset) -> Model | None:
    return queryset._hints.get("instance")


def get_related_field(queryset, related_instance):
    if field := queryset._hints.get("_field"):
        return field, False
    if refreshed := related_instance.__dict__.get("__refreshed__"):
        return refreshed, True
    return "", False


class RelationTracking(Domain):
    name = "django.relations"

    __slots__ = ()

    def register_event_handlers(self) -> None:
        self.deps.events.register_track_model_handler(self._track_model_handler)
        self.deps.events.register_query_started_handler(self._query_started_handler)
        self.deps.events.register_new_instance_handler(self._new_instance_handler)

    def unregister_event_handlers(self) -> None:
        self.deps.events.unregister_track_model_handler(self._track_model_handler)
        self.deps.events.unregister_query_started_handler(self._query_started_handler)
        self.deps.events.unregister_new_instance_handler(self._new_instance_handler)

    def install_wrappers(self):
        self._wrap_field_descriptors()

    def _track_model_handler(self, model):
        self.wrapper.wrap(model, "refresh_from_db", self._refresh_from_db_wrapper)

    def _refresh_from_db_wrapper(self, wrapped, instance, args, kwargs):
        if (fields := kwargs.get("fields")) and len(fields) == 1:
            instance.__refreshed__ = fields[0]
        return wrapped(*args, **kwargs)

    def _query_started_handler(self, query_tracker: ORMQuery) -> None:
        if not (related_instance := get_related_instance(query_tracker.query)):
            return
        from_field, from_deferred = get_related_field(query_tracker.query, related_instance)
        query_tracker.data.relation = Relation(
            related_instance._meta.label,
            from_field,
            from_deferred,
            *get_parent_query_info(related_instance, from_field),
        )

    def _new_instance_handler(
        self,
        instance: Model,
        path: str,
        query_tracker: ORMQuery,
        select_related: dict | None,
    ) -> None:
        if rel := query_tracker.data.relation:
            depth = rel.depth + 1
            path = f"{rel.path}__{rel.from_field}"
        else:
            depth = 1
        instance.__rel_info__ = path, depth, query_tracker.data.timestamp, query_tracker.data.uid

    def _wrap_field_descriptors(self):
        """
        Patches field descriptors to add a 'field' hint to querysets.
        This is a custom hint that's used in `get_related_field`.
        """

        self.wrapper.wrap(
            related_descriptors.ForwardManyToOneDescriptor,
            "get_queryset",
            self._forward_many_to_one_get_queryset_wrapper,
        )
        self.wrapper.wrap(
            related_descriptors.ReverseOneToOneDescriptor,
            "get_queryset",
            self._reverse_one_to_one_get_queryset_wrapper,
        )
        # `ManyToManyDescriptor` is a subclass of `ReverseManyToOneDescriptor`
        # so we only need to patch once, so is `ReverseGenericManyToOneDescriptor`
        self.wrapper.wrap(
            related_descriptors.ReverseManyToOneDescriptor,
            "__get__",
            self._reverse_many_to_one_get_manager_wrapper,
        )

    def _forward_many_to_one_get_queryset_wrapper(self, wrapped, instance, args, kwargs):
        return wrapped(*args, _field=instance.field.name, **kwargs)

    def _reverse_one_to_one_get_queryset_wrapper(self, wrapped, instance, args, kwargs):
        return wrapped(*args, _field=instance.related.name, **kwargs)

    def _get_descriptor_field_name(self, descriptor):
        if isinstance(descriptor, related_descriptors.ManyToManyDescriptor):
            return descriptor.rel.name if descriptor.reverse else descriptor.field.name
        if isinstance(descriptor, ReverseGenericManyToOneDescriptor):
            return descriptor.field.name
        return descriptor.rel.name

    def _reverse_many_to_one_get_manager_wrapper(self, wrapped, instance, args, kwargs):
        if (obj := args[1]) is None or not hasattr(obj, "__rel_info__"):
            return wrapped(*args, **kwargs)

        descriptor = args[0]
        hints = {"_field": self._get_descriptor_field_name(descriptor)}
        if isinstance(descriptor, ReverseGenericManyToOneDescriptor):
            hints["instance"] = obj

        related_manager = wrapped(*args, **kwargs)
        # Add hints to the related manager so that they are passed
        # to each queryset it produces.
        related_manager._hints.update(hints)
        return related_manager
