from django.apps import AppConfig
import importlib

class ConfigsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "configs"

    def ready(self):
        import configs.signals
        importlib.import_module("configs.auth_extension")
