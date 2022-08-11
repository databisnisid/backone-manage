from django.apps import AppConfig


class ControllersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'controllers'

    def ready(self):
        import controllers.signals
