"""Imprévus de voyage (docs/IMPREVUS_VOYAGE.md) : tracés sur le départ, avec seulement les écritures de ce qui change.

Comptes proposés, modifiables sur chaque frais : à valider par l'expert-comptable.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _compte(numero, intitule):
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]


class Incident(models.Model):
    PANNE, TRANSBORDEMENT, REMPLACEMENT, DECLASSEMENT, RETARD, ACCIDENT, PERTE, AMENDE, VENTE_A_BORD, ANNULATION, AUTRE = (
        "PANNE", "TRANSBORDEMENT", "REMPLACEMENT", "DECLASSEMENT", "RETARD", "ACCIDENT", "PERTE", "AMENDE", "VENTE_A_BORD",
        "ANNULATION", "AUTRE")
    TYPES = [(PANNE, "Panne en route"), (TRANSBORDEMENT, "Transbordement vers un autre car"),
             (REMPLACEMENT, "Véhicule remplacé avant le départ"), (DECLASSEMENT, "Voyageurs VIP déclassés"),
             (RETARD, "Retard important"), (ACCIDENT, "Accident"), (PERTE, "Bagage ou colis perdu / abîmé"),
             (AMENDE, "Amende, contravention"), (VENTE_A_BORD, "Voyageurs pris en route (recette à bord)"),
             (ANNULATION, "Départ annulé par la compagnie"), (AUTRE, "Autre imprévu")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    depart = models.ForeignKey("transport.Depart", on_delete=models.PROTECT, related_name="incidents")
    type_incident = models.CharField("Imprévu", max_length=15, choices=TYPES)
    date = models.DateField(default=timezone.localdate)
    lieu = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=250, blank=True)
    vehicule_secours = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT,
                                         related_name="+", verbose_name="Car de secours (de la société)")
    part_restante = models.DecimalField("Part du trajet restant (%)", max_digits=5, decimal_places=2, default=ZERO)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Imprévu de voyage"

    def __str__(self):
        return f"{self.numero} {self.get_type_incident_display()} ({self.depart.numero})"

    def save(self, *args, **kwargs):
        self.numero = self.numero or Sequence.piece("INC", self.date.year)
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic
    def transborder(cls, depart, part_restante, vehicule_secours=None, lieu="", description="", utilisateur=None):
        """Panne en route : les voyageurs finissent le trajet dans un autre car. Car de la société : la part du trajet
        restant de la recette (billets et bagages) lui passe ; car loué : la recette reste au car en panne, qui porte
        la location (frais d'imprévu)."""
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        from .models import Depart, ParametresTransport, _proprietaire

        depart = Depart.objects.select_for_update().get(pk=depart.pk)
        _proprietaire(depart, f"Le départ {depart.numero}")
        if depart.statut not in (Depart.PARTI, Depart.ARRIVE):
            raise ValidationError("Le transbordement concerne un car parti.")
        part = Decimal(part_restante)
        if not part.is_finite() or not ZERO < part <= 100:
            raise ValidationError("La part du trajet restant est un pourcentage entre 0 et 100.")
        if vehicule_secours is not None and vehicule_secours.pk == depart.vehicule_id:
            raise ValidationError("Le car de secours doit être un autre véhicule.")
        if vehicule_secours is not None and not vehicule_secours.actif:
            raise ValidationError("Le véhicule de secours est inactif.")
        precedent = cls.objects.filter(depart=depart, type_incident=cls.TRANSBORDEMENT).first()
        if precedent is not None:
            if (precedent.part_restante == part and precedent.vehicule_secours_id == getattr(vehicule_secours, "pk", None)
                    and precedent.lieu == lieu and precedent.description == description):
                return precedent  # même opération réémise : aucune seconde écriture
            raise ValidationError("Un transvasement est déjà enregistré pour ce départ. Consultez son historique avant tout nouveau changement.")
        incident = cls.objects.create(depart=depart, type_incident=cls.TRANSBORDEMENT, part_restante=part, lieu=lieu,
                                      description=description, vehicule_secours=vehicule_secours, cree_par=utilisateur)
        if vehicule_secours is not None and depart.ecriture_recettes_id:
            p = ParametresTransport.get()
            produits = {c.pk for c in (p.compte_billets, p.compte_bagages) if c is not None}
            lignes = []
            for l in depart.ecriture_recettes.lignes.filter(compte_id__in=produits, vehicule_id=depart.vehicule_id):
                montant = (Decimal(l.credit - l.debit) * part / 100).quantize(Decimal("1"))
                if montant:
                    lignes += [{"compte": l.compte, "debit": montant, "vehicule": depart.vehicule, "section": l.section},
                               {"compte": l.compte, "credit": montant, "vehicule": vehicule_secours, "section": l.section}]
            if lignes:
                incident.ecriture = creer_ecriture(
                    Journal.objects.get(code="OD"), incident.date,
                    f"Transbordement {incident.numero} : {depart.vehicule.immatriculation} → {vehicule_secours.immatriculation} "
                    f"({part} % du trajet)", lignes, reference=incident.numero, origine=depart.numero)
                incident.save(update_fields=["ecriture"])
        return incident

    @classmethod
    @transaction.atomic
    def recette_a_bord(cls, depart, montant, nombre, caisse, lieu="", utilisateur=None):
        """Voyageurs pris en route : l'argent remis par le convoyeur à l'arrivée est une recette du car."""
        from apps.comptabilite.services import creer_ecriture

        from .models import Depart, ParametresTransport, _ventiler

        if depart.statut not in (Depart.PARTI, Depart.ARRIVE, Depart.CLOTURE):
            raise ValidationError("La recette à bord concerne un car parti.")
        montant = Decimal(montant)
        if montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        p = ParametresTransport.get()
        incident = cls.objects.create(depart=depart, type_incident=cls.VENTE_A_BORD, lieu=lieu, cree_par=utilisateur,
                                      description=f"{nombre} voyageur(s) pris en route")
        incident.ecriture = creer_ecriture(
            caisse, incident.date, f"Recette à bord {incident.numero} départ {depart.numero} ({nombre} voyageur(s))",
            [{"compte": caisse.compte_tresorerie, "debit": montant}]
            + [{**l, "vehicule": depart.vehicule, "section": depart.ligne.gare_depart.section}
               for l in _ventiler(montant, p.compte_billets, p.taxe_billets)],
            reference=incident.numero, origine=depart.numero)
        incident.save(update_fields=["ecriture"])
        return incident


class FraisIncident(models.Model):
    """Argent payé ou rendu à cause d'un imprévu, imputé au véhicule concerné."""

    DEDOMMAGEMENT, LOCATION, DEPANNAGE, VOYAGEURS, INDEMNITE, AMENDE, AUTRE = (
        "DEDOMMAGEMENT", "LOCATION", "DEPANNAGE", "VOYAGEURS", "INDEMNITE", "AMENDE", "AUTRE")
    NATURES = [(DEDOMMAGEMENT, "Dédommagement des voyageurs (déclassement, retard)"),
               (LOCATION, "Location d'un car de secours"), (DEPANNAGE, "Dépannage, remorquage"),
               (VOYAGEURS, "Repas, hébergement des voyageurs bloqués"), (INDEMNITE, "Indemnité (accident, bagage, colis)"),
               (AMENDE, "Amende, contravention"), (AUTRE, "Autre frais")]
    COMPTES = {DEDOMMAGEMENT: ("709", "Rabais, remises et ristournes accordés"),
               LOCATION: ("6228", "Locations et charges locatives diverses"),
               DEPANNAGE: ("624", "Entretien, réparations et maintenance"), VOYAGEURS: ("638", "Autres charges externes"),
               INDEMNITE: ("658", "Charges diverses"), AMENDE: ("658", "Charges diverses"), AUTRE: ("658", "Charges diverses")}
    CAISSE, FOURNISSEUR, CHAUFFEUR = "CAISSE", "FOURNISSEUR", "CHAUFFEUR"
    PAIEMENTS = [(CAISSE, "Payé en caisse"), (FOURNISSEUR, "À payer au fournisseur (en compte)"),
                 (CHAUFFEUR, "Payé en caisse, imputable au chauffeur (retenue sur salaire)")]

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="frais")
    nature = models.CharField(max_length=15, choices=NATURES)
    libelle = models.CharField(max_length=150)
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    compte = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               help_text="Vide : compte proposé pour la nature (à valider)")
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                 help_text="Vide : le car du départ")
    paiement = models.CharField(max_length=12, choices=PAIEMENTS, default=CAISSE)
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    fournisseur = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        verbose_name = "Frais d'imprévu"

    @transaction.atomic
    def enregistrer(self):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        depart = self.incident.depart
        vehicule = self.vehicule or depart.vehicule
        compte = self.compte or _compte(*self.COMPTES[self.nature])
        if self.paiement == self.FOURNISSEUR:
            if not self.fournisseur_id:
                raise ValidationError("Choisissez le fournisseur.")
            journal, credit = Journal.objects.get(code="OD"), {"compte": self.fournisseur.get_compte_collectif(),
                                                                 "tiers": self.fournisseur}
        else:
            if not self.caisse_id or not self.caisse.compte_tresorerie_id:
                raise ValidationError("Choisissez la caisse qui paie.")
            journal, credit = self.caisse, {"compte": self.caisse.compte_tresorerie}
        if self.paiement == self.CHAUFFEUR:             # avancé par la société, retenu sur le salaire : pas de charge
            if depart.chauffeur_id is None:
                raise ValidationError("Ce départ n'a pas de chauffeur.")
            debit = {"compte": _compte("421", "Personnel, avances et acomptes")}
        else:
            debit = {"compte": compte, "vehicule": vehicule, "section": depart.ligne.gare_depart.section}
        self.compte = None if self.paiement == self.CHAUFFEUR else compte
        self.save()
        self.ecriture = creer_ecriture(
            journal, self.incident.date, f"{self.incident.numero} {self.get_nature_display()} : {self.libelle}"[:200],
            [{**debit, "debit": self.montant}, {**credit, "credit": self.montant}],
            reference=self.incident.numero, origine=depart.numero)
        self.save(update_fields=["ecriture"])
        return self

