"""
For each model, keep track of columns in form (col: index)
Wrap field descriptors and add field index to accessed bitset
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from qorme.domain import Domain
from qorme.orm.tracking import get_orm_query
from qorme.utils.bitset import BitSet
from qorme_django import constants

if TYPE_CHECKING:
    from qorme.ingest.payload import Payload
    from qorme.orm.tracking import ORMQuery

logger = logging.getLogger(__name__)


def fqn(descriptor):
    klass = descriptor.__class__
    return f"{klass.__module__}.{klass.__name__}"


class UnknownDescriptorError(ValueError): ...


class FieldDescriptor:
    __slots__ = "index", "_get"

    def __init__(self, index, descriptor):
        self.index = index
        self._get = descriptor.__get__

    def __get__(self, instance, cls):
        if accessed := self._get_columns_accessed(instance):
            accessed.set(self.index)
        return self._get(instance, cls)

    def _get_columns_accessed(self, instance) -> BitSet | None:
        if not instance:
            return
        if accessed := getattr(instance, "__columns_accessed__", None):
            # Already set, use it
            return accessed
        if get_orm_query(None):
            # __columns_accessed__ not yet set for the current query, create it (lazily)
            # to ensure all accesses are tracked.
            # This may be django internals accessing some fields
            # before returning the instance to user code.
            accessed = instance.__columns_accessed__ = BitSet()
            return accessed


# Force them to be data descriptors
class DeferredAttributeDescriptor(FieldDescriptor):
    __slots__ = "attname"

    def __init__(self, index, descriptor, attname):
        super().__init__(index, descriptor)
        self.attname = attname

    def __set__(self, instance, value):
        instance.__dict__[self.attname] = value

    def __delete__(self, instance):
        del instance.__dict__[self.attname]


class EditableFieldDescriptor(FieldDescriptor):
    __slots__ = "_set"

    def __init__(self, index, descriptor):
        super().__init__(index, descriptor)
        self._set = descriptor.__set__

    def __set__(self, instance, value):
        self._set(instance, value)


class ColumnsTracking(Domain):
    """Tracking fields accessed can help detect unused fields (and use `only` or `defer`)"""

    name = "django.columns"

    __slots__ = "idx_to_columns", "idx_to_columns_map", "known_descriptors"

    def setup(self):
        self.idx_to_columns = {}
        self.idx_to_columns_map = {}
        self.known_descriptors = self.config.known_descriptors | constants.KNOWN_DESCRIPTORS

    def register_event_handlers(self) -> None:
        self.deps.events.register_track_model_handler(self._track_model_handler)
        self.deps.events.register_new_instance_handler(self._new_instance_handler)
        self.deps.events.register_process_payload_handler(self._process_payload_handler)

    def unregister_event_handlers(self) -> None:
        self.deps.events.unregister_track_model_handler(self._track_model_handler)
        self.deps.events.unregister_new_instance_handler(self._new_instance_handler)
        self.deps.events.unregister_process_payload_handler(self._process_payload_handler)

    def _process_payload_handler(self, payload: Payload) -> None:
        if payload.rows:
            payload.idx_to_columns = self.idx_to_columns

    def _track_model_handler(self, model):
        from django.db.models.fields.related_descriptors import (
            ForeignKeyDeferredAttribute,
            ReverseManyToOneDescriptor,
        )
        from django.db.models.query_utils import DeferredAttribute

        for_model = self.idx_to_columns[model._meta.label] = []
        for_model_map = self.idx_to_columns_map[model._meta.label] = {}
        for field in model._meta._get_fields(
            forward=True, reverse=False, include_hidden=True, include_parents=True
        ):
            if not (column := getattr(field, "column", None)):
                continue
            descriptor = getattr(model, column)
            if isinstance(descriptor, ReverseManyToOneDescriptor):
                continue
            idx = len(for_model)
            for_model.append(column)
            for_model_map[column] = idx
            if isinstance(descriptor, DeferredAttribute):
                # Use self.wrap
                setattr(model, column, DeferredAttributeDescriptor(idx, descriptor, column))
            elif (
                isinstance(descriptor, ForeignKeyDeferredAttribute)
                or fqn(descriptor) in self.known_descriptors
            ):
                setattr(model, column, EditableFieldDescriptor(idx, descriptor))
            else:
                # Handle fields we know if needed, i.e never defer unknown
                raise UnknownDescriptorError([column, fqn(descriptor)])
            # TODO: uninstall_wrappers, check inheritance

    def _new_instance_handler(
        self, instance: Any, path: str, query_tracker: ORMQuery, select_related: dict | None
    ) -> None:
        rows = query_tracker.get_rows(
            instance, path, select_related, self._get_columns_loaded, self._get_columns_required
        )
        rows.count += 1
        # Merge already accessed columns
        if accessed := getattr(instance, "__columns_accessed__", None):
            rows.columns_accessed.ior(accessed)
        # Attach shared accessed bitset to instance
        instance.__columns_accessed__ = rows.columns_accessed

    def _get_columns_loaded(self, instance, select_related: dict | None) -> BitSet:
        loaded = BitSet()
        data = instance.__dict__
        for idx, col in enumerate(self.idx_to_columns[instance._meta.label]):
            if col in data:
                loaded.set(idx)
        return loaded

    def _get_columns_required(self, instance, select_related: dict | None) -> BitSet:
        required = BitSet()
        idx_to_columns_map = self.idx_to_columns_map[instance._meta.label]
        # Add primary key
        pk_name = instance._meta.pk.attname
        if (idx := idx_to_columns_map.get(pk_name)) is not None:
            required.set(idx)

        # From Django docs, if you are using select_related() to retrieve related models,
        # you shouldn't defer the loading of the field that connects from the primary
        # model to the related one,
        # doing so will result in an error.
        # Therefore, we mark the join fields as required.
        if not isinstance(select_related, dict):
            return required

        for field in select_related:
            rel_field = instance._meta.get_field(field)
            rel_name = getattr(rel_field, "attname", rel_field.name)
            if (rel_idx := idx_to_columns_map.get(rel_name)) is not None:
                required.set(rel_idx)

        return required
