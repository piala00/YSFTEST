"""Échanges entre sites hors ligne (agences ↔ siège) par lots signés, transmis par n'importe quel canal
(WhatsApp, Telegram, courriel, clé USB). Spécification : skill erp-ohada-retour-revue-conditionnements-consolidation,
references/SPEC_ECHANGES_AGENCES.md.

Principe : chaque site enregistre ses faits (écritures validées, billets, colis, départs…) dans un journal d'événements
sortant, dans la même transaction que l'opération. Un lot reprend une plage continue de ce journal. Le destinataire
vérifie la signature, écarte les doublons, repère les manques, puis intègre chaque fait une seule fois, sans refaire
l'opération (pas de nouvelle vente, pas de seconde écriture).
"""
import uuid

from django.conf import settings
from django.db import models


class Evenement(models.Model):
    """Journal sortant de ce site : un fait par ligne, numéroté sans trou."""

    sequence = models.PositiveBigIntegerField(unique=True)
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    type = models.CharField(max_length=30)
    objet_uid = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    operation = models.CharField(max_length=20, default="ENREGISTRE")
    date_metier = models.DateField(null=True, blank=True)
    auteur = models.CharField(max_length=150, blank=True)
    payload = models.JSONField()
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence"]
        verbose_name = "Événement à transmettre"

    def __str__(self):
        return f"{self.sequence} {self.type} {self.operation}"


class LotEmis(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    destination = models.ForeignKey("core.Agence", on_delete=models.PROTECT, related_name="lots_emis")
    sequence_de = models.PositiveBigIntegerField(default=0)
    sequence_a = models.PositiveBigIntegerField(default=0)
    nombre = models.PositiveIntegerField("Événements", default=0)
    relayes = models.PositiveIntegerField("Événements relayés", default=0)
    nom_fichier = models.CharField(max_length=120)
    empreinte = models.CharField(max_length=64)
    taille = models.PositiveIntegerField(default=0)
    cree_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-cree_le"]
        verbose_name = "Lot envoyé"


class LotRecu(models.Model):
    uid = models.UUIDField(unique=True)
    source = models.ForeignKey("core.Agence", on_delete=models.PROTECT, related_name="lots_recus")
    empreinte = models.CharField(max_length=64)
    nom_fichier = models.CharField(max_length=200, blank=True)
    nombre = models.PositiveIntegerField(default=0)
    recu_le = models.DateTimeField(auto_now_add=True)
    recu_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    rapport = models.TextField(blank=True)

    class Meta:
        ordering = ["-recu_le"]
        verbose_name = "Lot reçu"


class EvenementRecu(models.Model):
    """Boîte de réception : chaque fait reçu, une seule fois, avec son état d'intégration."""

    ATTENTE, INTEGRE, IGNORE, CONFLIT, REJET = "ATTENTE", "INTEGRE", "IGNORE", "CONFLIT", "REJET"
    STATUTS = [(ATTENTE, "En attente"), (INTEGRE, "Intégré"), (IGNORE, "Sans objet ici"), (CONFLIT, "Conflit"),
               (REJET, "Rejeté")]

    site_origine = models.ForeignKey("core.Agence", on_delete=models.PROTECT, related_name="evenements_origine")
    uid = models.UUIDField()
    sequence = models.PositiveBigIntegerField()
    type = models.CharField(max_length=30)
    objet_uid = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    operation = models.CharField(max_length=20)
    date_metier = models.DateField(null=True, blank=True)
    auteur = models.CharField(max_length=150, blank=True)
    payload = models.JSONField()
    empreinte = models.CharField(max_length=64)
    relaye = models.BooleanField(default=False, help_text="Reçu par l'intermédiaire du siège")
    statut = models.CharField(max_length=10, choices=STATUTS, default=ATTENTE)
    message = models.CharField(max_length=300, blank=True)
    lot = models.ForeignKey(LotRecu, on_delete=models.PROTECT, related_name="evenements")
    integre_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["site_origine", "sequence"]
        unique_together = [("site_origine", "uid")]
        verbose_name = "Événement reçu"


class Relais(models.Model):
    """Au siège : fait d'une agence déjà transmis à une autre agence concernée (ex. colis à remettre)."""

    evenement = models.ForeignKey(EvenementRecu, on_delete=models.CASCADE, related_name="relais")
    destination = models.ForeignKey("core.Agence", on_delete=models.CASCADE, related_name="+")
    lot = models.ForeignKey(LotEmis, on_delete=models.CASCADE, related_name="+")

    class Meta:
        unique_together = [("evenement", "destination")]
