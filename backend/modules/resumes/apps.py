from django.apps import AppConfig
class ResumesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.resumes"
    label = "resumes"

    def ready(self):
        from . import signals  # noqa: F401
