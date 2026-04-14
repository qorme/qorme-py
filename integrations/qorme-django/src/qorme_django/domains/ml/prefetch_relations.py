import logging
from typing import TYPE_CHECKING

from qorme.ml.domain import MLDomain
from qorme.ml.instance import MLInstance, build_rel_path
from qorme.orm.types import RowType

if TYPE_CHECKING:
    from qorme.orm.tracking import ORMQuery


logger = logging.getLogger(__name__)


class PrefetchRelations(MLDomain):
    name = "prefetch_relations"
    ml_category = "prefetch-relations"

    __slots__ = ()

    def optimize(self, query_tracker: "ORMQuery") -> None:
        if query_tracker.data.row_type != RowType.MODEL:
            return

        qs = query_tracker.query
        if qs is None:
            return

        queue = [("", qs.model)]
        prefetch = set()
        predictions = []
        while queue:
            path, model = queue.pop()
            if not (ml_model := self.get_model(model._meta.label)):
                continue

            prediction = ml_model.predict(MLInstance(path, query_tracker))
            if not prediction:
                continue

            prefetch.discard(path)
            for field in ml_model.decode_target(prediction.predicted):
                rel_path = build_rel_path(path, field)
                prefetch.add(rel_path)
                queue.append((rel_path, model._meta.get_field(field).related_model))

            prediction.data["path"] = build_rel_path(query_tracker.data.model, path)
            predictions.append(prediction)

        if not prefetch:
            return

        logger.debug("Prefetching %s", prefetch)
        if isinstance(qs._prefetch_related_lookups, list | tuple):
            # Check if any path from user choice conflicts with our prefetching
            # also need to handle Prefetch objects
            prefetch.update(qs._prefetch_related_lookups)
        qs._prefetch_related_lookups = prefetch
        query_tracker.data.ml_predictions[self.ml_category] = predictions
