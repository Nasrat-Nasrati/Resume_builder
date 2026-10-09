from django.apps import AppConfig
class ExportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.exports"
    label = "exports"

    def ready(self):
        from . import signals  # noqa: F401
