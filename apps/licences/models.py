from django.conf import settings
from django.db import models


class EtatLicence(models.Model):
    """Mémoire de la période d'essai (une seule ligne), scellée avec l'empreinte du serveur."""
    debut_essai = models.DateField()
    derniere_date_vue = models.DateField()
    sceau = models.CharField(max_length=64)

    class Meta:
        verbose_name = "état de la licence"


class LicenceDeposee(models.Model):
    """Chaque fichier de licence déposé à l'écran (historique) ; la plus récente valide est appliquée."""
    contenu = models.TextField()
    numero = models.CharField(max_length=40, blank=True)
    client = models.CharField(max_length=150, blank=True)
    valide = models.BooleanField(default=False)
    motif = models.CharField("Motif du refus", max_length=200, blank=True)
    deposee_le = models.DateTimeField(auto_now_add=True)
    deposee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-deposee_le", "-id"]
        verbose_name = "licence déposée"
