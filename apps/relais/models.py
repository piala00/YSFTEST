"""Relais Internet des échanges : une boîte aux lettres par site, sur un petit serveur en ligne.

Le relais ne connaît ni la société ni ses données : il garde des lots CHIFFRÉS (illisibles pour lui) jusqu'à ce que
le site destinataire les retire. Chaque site s'authentifie par un jeton (seule son empreinte est conservée).
"""
import hashlib
import secrets

from django.db import models


def empreinte(jeton):
    return hashlib.sha256(jeton.encode("utf-8")).hexdigest()


class SiteRelais(models.Model):
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100, blank=True)
    empreinte_jeton = models.CharField(max_length=64, unique=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    dernier_contact = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    def nouveau_jeton(self):
        """Crée (ou remplace) le jeton du site ; il n'est montré qu'une fois."""
        jeton = secrets.token_urlsafe(32)
        self.empreinte_jeton = empreinte(jeton)
        return jeton


class LotDepose(models.Model):
    destination = models.ForeignKey(SiteRelais, on_delete=models.CASCADE, related_name="boite")
    expediteur = models.ForeignKey(SiteRelais, on_delete=models.CASCADE, related_name="+")
    nom = models.CharField(max_length=160)
    taille = models.PositiveBigIntegerField()
    empreinte = models.CharField(max_length=64)
    depose_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["depose_le", "id"]
        unique_together = ("destination", "nom")
