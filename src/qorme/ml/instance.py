# from django.db.models.constants import LOOKUP_SEP
# Separator used to split filter strings apart.
LOOKUP_SEP = "__"


def build_rel_path(prefix, path):
    if not prefix:
        return path
    if not path:
        return prefix
    return LOOKUP_SEP.join([prefix, path])


class MLInstance:
    __slots__ = "path", "tracker"

    def __init__(self, path, tracker):
        self.path = path
        self.tracker = tracker

    def get_feature(self, feature):
        name, *args = feature.split(".")
        try:
            return EXTRACTOR_MAP[name](self, *args)
        except KeyError:
            raise ValueError(f"Unknown feature extractor: {name}") from None


def tb_extractor(instance, attr, idx):
    try:
        return getattr(instance.tracker.data.traceback[int(idx)], attr)
    except IndexError:
        return ""


def data_extractor(instance, attr):
    return instance.tracker.context.data.data.get(attr, "")


def context_extractor(instance, attr):
    if attr == "name":
        return instance.tracker.context.data.name
    if attr == "type":
        return instance.tracker.context.data.type.value
    raise ValueError


def relation_extractor(instance, attr):
    if attr == "path":
        return build_rel_path(instance.tracker.data.model, instance.path)
    raise ValueError


def template_extractor(instance, attr):
    if attr == "filename":
        return getattr(instance.tracker.data.template, "filename", "")
    if attr == "line":
        return getattr(instance.tracker.data.template, "line", "")
    raise ValueError


EXTRACTOR_MAP = {
    "tb": tb_extractor,
    "data": data_extractor,
    "context": context_extractor,
    "relation": relation_extractor,
    "template": template_extractor,
}
