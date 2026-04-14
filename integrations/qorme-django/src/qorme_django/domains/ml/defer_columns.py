from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from qorme.ml.domain import MLDomain
from qorme.ml.instance import MLInstance, build_rel_path
from qorme.orm.types import RowType

if TYPE_CHECKING:
    from qorme.orm.tracking import ORMQuery


logger = logging.getLogger(__name__)


def _get_paths(model, path, select_related):
    yield model, path

    if not select_related:
        return

    for rel_path in select_related:
        rel_field = model._meta.get_field(rel_path)
        yield from _get_paths(
            rel_field.related_model, build_rel_path(path, rel_path), select_related[rel_path]
        )


class DeferColumns(MLDomain):
    name = "defer_columns"
    ml_category = "defer-columns"

    __slots__ = ()

    def optimize(self, query_tracker: ORMQuery) -> None:
        if query_tracker.data.row_type != RowType.MODEL:
            return

        dj_query = query_tracker.query
        if dj_query is None:
            return

        query = dj_query.query
        if query.select_related is True:
            # We need to know the fields that will be traversed
            # which isn't obvious when using qs.select_related()
            # i.e without passing any fields.
            # It's also not encouraged.
            return

        if query.deferred_loading[0]:
            # .defer or .only already applied, don't optimize.
            return

        to_defer = set()
        predictions = []
        for model, path in _get_paths(dj_query.model, "", query.select_related):
            if not (ml_model := self.get_model(model._meta.label)):
                continue

            prediction = ml_model.predict(MLInstance(path, query_tracker))
            if not prediction:
                continue

            for field in ml_model.decode_target(prediction.predicted):
                to_defer.add(build_rel_path(path, field))

            prediction.data["path"] = build_rel_path(query_tracker.data.model, path)
            predictions.append(prediction)

        if not to_defer:
            return

        logger.debug("Deferring %s", to_defer)
        query.clear_deferred_loading()
        query.add_deferred_loading(to_defer)
        query_tracker.data.ml_predictions[self.ml_category] = predictions
