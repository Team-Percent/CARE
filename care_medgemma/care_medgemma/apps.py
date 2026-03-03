from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "care_medgemma"


class CareMedgemmaConfig(AppConfig):
    name = PLUGIN_NAME
    verbose_name = _("Care MedGemma")

    def ready(self):
        import care_medgemma.signals  # noqa: F401
