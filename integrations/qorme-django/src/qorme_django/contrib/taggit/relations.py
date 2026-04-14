from taggit.managers import _TaggableManager

from qorme.domain import Domain


class RelationTracking(Domain):
    name = "taggit.relations"

    __slots__ = ()

    def install_wrappers(self):
        self.wrapper.wrap(_TaggableManager, "get_queryset", self._get_queryset_wrapper)

    def _get_queryset_wrapper(self, wrapped, instance, args, kwargs):
        ret = wrapped(*args, **kwargs)
        field = instance.name or instance.prefetch_cache_name
        ret._hints.update(instance=instance.instance, _field=field)
        return ret
