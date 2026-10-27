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


class DemandeCorrection(models.Model):
    """La direction signale une erreur dans la comptabilité d'une agence et lui demande de la corriger.

    La direction n'écrit jamais dans les comptes de l'agence : l'agence corrige elle-même (extourne puis bonne écriture,
    ou conteste) ; ses écritures de correction remontent par le lot suivant et la demande se clôt chez les deux.
    Au siège : la demande d'origine (site_origine vide). À l'agence : la copie reçue (site_origine = code du siège).
    """

    DEMANDEE, RECUE, CORRIGEE, CONTESTEE, ANNULEE = "DEMANDEE", "RECUE", "CORRIGEE", "CONTESTEE", "ANNULEE"
    STATUTS = [(DEMANDEE, "Envoyée à l'agence"), (RECUE, "Reçue par l'agence"), (CORRIGEE, "Corrigée par l'agence"),
               (CONTESTEE, "Contestée par l'agence"), (ANNULEE, "Annulée par la direction")]
    ORDRE = {DEMANDEE: 0, RECUE: 1, CORRIGEE: 2, CONTESTEE: 2, ANNULEE: 3}
    OUVERTS = (DEMANDEE, RECUE)

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False)
    numero = models.CharField("N°", max_length=20)
    agence = models.CharField("Agence concernée", max_length=10)
    ecriture_uid = models.UUIDField("Écriture en cause")
    ecriture_numero = models.CharField("N° de pièce", max_length=30, blank=True)
    ecriture_date = models.DateField("Date de la pièce", null=True, blank=True)
    ecriture_libelle = models.CharField("Libellé de la pièce", max_length=200, blank=True)
    motif = models.TextField("Erreur constatée")
    correction_attendue = models.TextField("Correction attendue", blank=True)
    demandee_par = models.CharField("Demandée par", max_length=150, blank=True)
    demandee_le = models.DateTimeField("Demandée le", null=True, blank=True)
    echeance = models.DateField("À corriger avant le", null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUTS, default=DEMANDEE)
    reponse = models.TextField("Réponse de l'agence", blank=True)
    repondu_par = models.CharField("Répondu par", max_length=150, blank=True)
    repondu_le = models.DateTimeField("Répondu le", null=True, blank=True)
    ecritures_correction = models.JSONField("Écritures de correction (uid)", default=list, blank=True)
    annulee_motif = models.CharField("Motif de l'annulation", max_length=200, blank=True)

    class Meta:
        ordering = ["-demandee_le", "-id"]
        verbose_name = "demande de correction"
        verbose_name_plural = "demandes de correction"

    def __str__(self):
        return f"{self.numero} — {self.agence} — {self.get_statut_display()}"

    @property
    def ouverte(self):
        return self.statut in self.OUVERTS

    @property
    def en_retard(self):
        import datetime

        return self.ouverte and self.echeance is not None and self.echeance < datetime.date.today()
