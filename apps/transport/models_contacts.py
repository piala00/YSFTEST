import uuid

from django.conf import settings
from django.db import models


class PersonneGuichet(models.Model):
    """Coordonnées réutilisables du dossier local ; un téléphone peut appartenir à plusieurs personnes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=120)
    telephone = models.CharField(max_length=30)
    telephone_normalise = models.CharField(max_length=20, db_index=True)
    nom_normalise = models.CharField(max_length=240, db_index=True)
    piece_identite = models.CharField(max_length=40, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="+")
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom", "id"]
        verbose_name = "Coordonnées du guichet"

    def __str__(self):
        return f"{self.nom} — {self.telephone}"


class SaisieGuichet(models.Model):
    """Résultat d'un formulaire : un double clic ne doit jamais créer deux pièces."""
    cle = models.UUIDField(primary_key=True, editable=False)
    genre = models.CharField(max_length=10)
    empreinte = models.CharField(max_length=64)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    billet = models.OneToOneField("transport.Billet", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    colis = models.OneToOneField("transport.Colis", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)
