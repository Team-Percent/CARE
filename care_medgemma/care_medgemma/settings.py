from typing import Any

import environ
from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from rest_framework.settings import perform_import

from care_medgemma.apps import PLUGIN_NAME

env = environ.Env()


class PluginSettings:  # pragma: no cover
    """
    A settings object that allows plugin settings to be accessed as
    properties. For example:

        from care_medgemma.settings import plugin_settings
        print(plugin_settings.MEDGEMMA_MOCK_MODE)
    """

    def __init__(
        self,
        plugin_name: str = None,
        defaults: dict | None = None,
        import_strings: set | None = None,
        required_settings: set | None = None,
    ) -> None:
        if not plugin_name:
            raise ValueError("Plugin name must be provided")
        self.plugin_name = plugin_name
        self.defaults = defaults or {}
        self.import_strings = import_strings or set()
        self.required_settings = required_settings or set()
        self._cached_attrs = set()

    def __getattr__(self, attr) -> Any:
        if attr not in self.defaults:
            raise AttributeError("Invalid setting: '%s'" % attr)

        val = self.defaults[attr]
        try:
            val = self.user_settings[attr]
        except KeyError:
            try:
                val = env(attr, cast=type(val))
            except environ.ImproperlyConfigured:
                pass

        if attr in self.import_strings:
            val = perform_import(val, attr)

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    @property
    def user_settings(self) -> dict:
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "PLUGIN_CONFIGS", {}).get(
                self.plugin_name, {}
            )
        return self._user_settings

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


DEFAULTS = {
    # MedGemma configuration
    "MEDGEMMA_MOCK_MODE": True,
    "MEDGEMMA_MODEL_VERSION": "medgemma-mock-1.0",
    "MEDGEMMA_API_ENDPOINT": "",
    "MEDGEMMA_API_KEY": "",
    # Ollama local server configuration (for real MedGemma mode)
    "MEDGEMMA_OLLAMA_HOST": "http://172.19.127.189:11434/api/chat",
    "MEDGEMMA_OLLAMA_MODEL": "CareAnalyzer",
    "MEDGEMMA_REQUEST_TIMEOUT": 120,
    # FHIR configuration
    "FHIR_VERSION": "R5",
    "FHIR_BUNDLE_PAGE_SIZE": 50,
    # Consent configuration
    "CONSENT_TOKEN_TTL_HOURS": 1,
    "CONSENT_MAX_GRANTS_PER_DAY": 100,
    # Emergency access
    "EMERGENCY_TOKEN_TTL_HOURS": 4,
    "EMERGENCY_MAX_PER_DOCTOR_PER_DAY": 5,
    # Rate limiting
    "RATE_LIMIT_FHIR_FETCHES_PER_HOUR": 500,
}

plugin_settings = PluginSettings(
    PLUGIN_NAME,
    defaults=DEFAULTS,
)


@receiver(setting_changed)
def reload_plugin_settings(*args, **kwargs) -> None:
    setting = kwargs["setting"]
    if setting == "PLUGIN_CONFIGS":
        plugin_settings.reload()
