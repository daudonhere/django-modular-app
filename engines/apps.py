from django.apps import AppConfig

class EngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'engines'

    def ready(self):
        import engines.signals
