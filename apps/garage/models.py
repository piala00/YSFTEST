"""Garage : carburant et réparations des véhicules. Chaque opération passe son écriture sur le véhicule.

  Plein de carburant        D 6053 carburant (véhicule)        / C caisse, ou C 401 station (en compte)
  Réparation (à la clôture) D 624 pièces, main d'œuvre extérieure (véhicule) / C caisse, ou C 401 fournisseur
                            La main d'œuvre des mécaniciens salariés n'est pas repassée : elle est dans la paie.
Comptes réglables dans Paramètres transport, à valider par l'expert-comptable.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")
ESPECES, COMPTE = "ESPECES", "COMPTE"
PAIEMENTS = [(ESPECES, "Payé en caisse"), (COMPTE, "En compte fournisseur (à payer)")]


def _contrepartie(paiement, caisse, fournisseur, quoi):
    """(journal, ligne de contrepartie) d'une dépense payée en caisse ou due au fournisseur."""
    from apps.comptabilite.models import Journal

    if paiement == COMPTE:
        if fournisseur is None:
            raise ValidationError(f"{quoi} : choisissez le fournisseur (paiement en compte).")
        return Journal.objects.get(code="AC"), {"compte": fournisseur.get_compte_collectif(), "tiers": fournisseur}
    if caisse is None or not caisse.compte_tresorerie_id:
        raise ValidationError(f"{quoi} : choisissez une caisse qui a un compte de trésorerie.")
    return caisse, {"compte": caisse.compte_tresorerie}


class PleinCarburant(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField(max_length=10, blank=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    vehicule = models.ForeignKey("transport.Vehicule", on_delete=models.PROTECT, related_name="pleins", verbose_name="Véhicule")
    depart = models.ForeignKey("transport.Depart", null=True, blank=True, on_delete=models.PROTECT, related_name="pleins",
                               help_text="Voyage pour lequel le plein est fait (facultatif)")
    litres = models.DecimalField(max_digits=10, decimal_places=2)
    prix_litre = models.DecimalField("Prix du litre", max_digits=10, decimal_places=0)
    montant = models.DecimalField(max_digits=14, decimal_places=0, blank=True, help_text="Vide : litres × prix du litre")
    kilometrage = models.PositiveIntegerField("Compteur (km)", null=True, blank=True,
                                              help_text="Relevé au moment du plein : sert au calcul de la consommation")
    station = models.CharField(max_length=100, blank=True)
    paiement = models.CharField(max_length=10, choices=PAIEMENTS, default=ESPECES)
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    fournisseur = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                    help_text="Station où l'agence a un compte")
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Plein de carburant"
        verbose_name_plural = "Pleins de carburant"

    def __str__(self):
        return f"{self.numero} {self.vehicule.immatriculation} {self.litres} L"

    def precedent(self):
        return (PleinCarburant.objects.filter(vehicule=self.vehicule, kilometrage__isnull=False)
                .exclude(pk=self.pk).filter(models.Q(date__lt=self.date) | models.Q(date=self.date, pk__lt=self.pk or 0))
                .order_by("-date", "-pk").first())

    def consommation(self):
        """Litres aux 100 km depuis le plein précédent (plein à plein)."""
        avant = self.precedent()
        if self.kilometrage is None or avant is None or self.kilometrage <= avant.kilometrage:
            return None
        return (Decimal(self.litres) * 100 / (self.kilometrage - avant.kilometrage)).quantize(Decimal("0.1"))

    @transaction.atomic
    def enregistrer(self, utilisateur=None):
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        if self.litres is None or self.litres <= 0 or self.prix_litre is None or self.prix_litre < 0:
            raise ValidationError("Indiquez les litres et le prix du litre.")
        if self.montant is None:
            self.montant = (Decimal(self.litres) * Decimal(self.prix_litre)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        avant = self.precedent()
        if self.kilometrage is not None and avant is not None and self.kilometrage < avant.kilometrage:
            raise ValidationError(f"Compteur inférieur au plein précédent ({avant.kilometrage} km le {avant.date:%d/%m/%Y}).")
        journal, contrepartie = _contrepartie(self.paiement, self.caisse, self.fournisseur, "Plein")
        self.cree_par = self.cree_par or utilisateur
        self.numero = self.numero or Sequence.piece("CARB", self.date.year)
        self.save()
        if self.montant:
            p = ParametresTransport.get()
            self.ecriture = creer_ecriture(
                journal, self.date, f"Carburant {self.vehicule.immatriculation} {self.litres} L{f' - {self.station}' if self.station else ''}",
                [{"compte": p.compte_carburant, "vehicule": self.vehicule, "section": self.vehicule.section, "debit": self.montant},
                 {**contrepartie, "credit": self.montant}], reference=self.numero, origine=self.numero)
            self.save(update_fields=["ecriture"])
        return self


class OrdreReparation(models.Model):
    """Passage d'un véhicule au garage : panne, pièces, main d'œuvre ; comptabilisé à la clôture, sur le véhicule."""

    OUVERT, CLOTURE, ANNULE = "OUVERT", "CLOTURE", "ANNULE"
    STATUTS = [(OUVERT, "En cours"), (CLOTURE, "Terminé"), (ANNULE, "Annulé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField(max_length=10, blank=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    vehicule = models.ForeignKey("transport.Vehicule", on_delete=models.PROTECT, related_name="reparations",
                                 verbose_name="Véhicule")
    date_entree = models.DateField("Entrée au garage", default=timezone.localdate)
    date_sortie = models.DateField("Sortie", null=True, blank=True)
    kilometrage = models.PositiveIntegerField("Compteur (km)", null=True, blank=True)
    panne = models.CharField("Panne / travaux", max_length=250)
    intervenant = models.CharField("Mécanicien ou garage", max_length=120, blank=True)
    statut = models.CharField(max_length=10, choices=STATUTS, default=OUVERT)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date_entree", "-numero"]
        verbose_name = "Ordre de réparation"
        verbose_name_plural = "Ordres de réparation"

    def __str__(self):
        return f"{self.numero} {self.vehicule.immatriculation} - {self.panne}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = Sequence.piece("OR", self.date_entree.year)
        super().save(*args, **kwargs)

    @property
    def cout(self):
        return sum((l.montant for l in self.lignes.all()), ZERO)

    @property
    def cout_comptabilise(self):
        return sum((l.montant for l in self.lignes.all() if l.nature != LigneReparation.MAIN_OEUVRE_INTERNE), ZERO)

    @property
    def immobilisation_jours(self):
        fin = self.date_sortie or timezone.localdate()
        return (fin - self.date_entree).days

    @transaction.atomic
    def cloturer(self, caisse=None, date=None, utilisateur=None):
        """Le véhicule sort du garage : les pièces et travaux extérieurs passent en charges du véhicule."""
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        if self.statut != self.OUVERT:
            raise ValidationError("Cet ordre de réparation n'est plus en cours.")
        lignes_or = list(self.lignes.select_related("fournisseur"))
        if not lignes_or:
            raise ValidationError("Ajoutez les pièces et travaux avant de terminer la réparation.")
        date = date or timezone.localdate()
        if date < self.date_entree:
            raise ValidationError("La sortie ne peut précéder l'entrée au garage.")
        p = ParametresTransport.get()
        lignes, contreparties = [], {}
        for l in lignes_or:
            if l.nature == LigneReparation.MAIN_OEUVRE_INTERNE or not l.montant:
                continue
            compte = p.compte_pieces if l.nature == LigneReparation.PIECE else p.compte_main_oeuvre
            lignes.append({"compte": compte, "vehicule": self.vehicule, "section": self.vehicule.section, "debit": l.montant,
                           "libelle": f"{self.numero} {l.designation}"[:200]})
            journal, contrepartie = _contrepartie(l.paiement, caisse, l.fournisseur, l.designation)
            cle = (contrepartie["compte"].pk, getattr(contrepartie.get("tiers"), "pk", None))
            contreparties.setdefault(cle, {**contrepartie, "credit": ZERO})["credit"] += l.montant
        if lignes:
            journal = caisse if caisse is not None and all(l.paiement == ESPECES for l in lignes_or) else Journal.objects.get(code="OD")
            self.ecriture = creer_ecriture(journal, date, f"Réparation {self.numero} {self.vehicule.immatriculation} - {self.panne}",
                                           lignes + list(contreparties.values()), reference=self.numero, origine=self.numero)
        self.statut, self.date_sortie = self.CLOTURE, date
        self.save(update_fields=["statut", "date_sortie", "ecriture"])
        return self


class LigneReparation(models.Model):
    PIECE, MAIN_OEUVRE_EXTERNE, MAIN_OEUVRE_INTERNE = "PIECE", "MO_EXTERNE", "MO_INTERNE"
    NATURES = [(PIECE, "Pièce / fourniture"), (MAIN_OEUVRE_EXTERNE, "Main d'œuvre extérieure (garage, soudeur…)"),
               (MAIN_OEUVRE_INTERNE, "Main d'œuvre interne (pour mémoire : déjà dans la paie)")]

    ordre = models.ForeignKey(OrdreReparation, on_delete=models.CASCADE, related_name="lignes")
    nature = models.CharField(max_length=12, choices=NATURES, default=PIECE)
    designation = models.CharField("Désignation", max_length=150)
    quantite = models.DecimalField("Quantité", max_digits=10, decimal_places=2, default=Decimal("1"))
    prix_unitaire = models.DecimalField("Prix unitaire", max_digits=12, decimal_places=0, default=ZERO)
    paiement = models.CharField(max_length=10, choices=PAIEMENTS, default=ESPECES)
    fournisseur = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["pk"]

    @property
    def montant(self):
        return (Decimal(self.quantite) * Decimal(self.prix_unitaire)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
