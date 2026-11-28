from django.apps import AppConfig


class LicencesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.licences"
    verbose_name = "Licences"

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        from .licence import compter_ouverture

        user_logged_in.connect(compter_ouverture, dispatch_uid="licences-ouverture-essai")
