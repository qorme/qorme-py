import copy

from qorme.defaults import QORME_SETTINGS
from qorme_django import constants

QORME_DJANGO_SETTINGS = copy.deepcopy(QORME_SETTINGS)

# Add Django specific domains
QORME_DJANGO_SETTINGS.update(
    {
        "django": {
            "queries": {
                "handler": "qorme_django.domains.queries.QueryTracking",
                "apps_to_include": [],
                "apps_to_exclude": [],
                "models_to_include": [],
                "models_to_exclude": [],
            },
            "columns": {
                "handler": "qorme_django.domains.columns.ColumnsTracking",
                "known_descriptors": set(),
            },
            "requests": {
                "handler": "qorme_django.domains.requests.RequestTracking",
                "ignore_paths": [],
            },
            "cli": {"handler": "qorme_django.domains.cli.CLITracking"},
            "template": {"handler": "qorme_django.domains.template.TemplateTracking"},
            "relations": {"handler": "qorme_django.domains.relations.RelationTracking"},
            "defer_columns": {"handler": "qorme_django.domains.ml.defer_columns.DeferColumns"},
            "prefetch_relations": {
                "handler": "qorme_django.domains.ml.prefetch_relations.PrefetchRelations"
            },
        },
        # Contrib
        "taggit": {
            "relations": {
                "handler": "qorme_django.contrib.taggit.relations.RelationTracking",
            },
        },
        "wagtail": {
            "page_render": {
                "handler": "qorme_django.contrib.wagtail.page_render.PageRender",
            },
        },
    }
)

# Add Django modules to ignore in tracebacks
QORME_DJANGO_SETTINGS["deps"]["traceback"][
    "default_ignored_modules"
] += constants.IGNORE_MODULES_IN_TRACEBACK
