from django.apps import AppConfig


class EchangesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.echanges"
    verbose_name = "Échanges entre sites"

    def ready(self):
        from . import signaux

        signaux.connecter()
