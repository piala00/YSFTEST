"""Véhicules de partenaires propriétaires (audit P3 ; skill réf. 06).

Contrat versionné par véhicule (jamais écrasé : un avenant crée une nouvelle version datée) :
  - COMMISSION : l'agence garde un pourcentage des recettes du véhicule ; le propriétaire reçoit le reste, moins les
    dépenses que le contrat met à sa charge (carburant, réparations, équipage, frais de route, autres) ;
  - LOCATION : l'agence paie un forfait par jour ou par mois (au prorata des jours du contrat).
Décompte de période : calculé depuis la comptabilité du véhicule, figé avec la version du contrat, puis approuvé.
  Approbation   D 622 rémunération du propriétaire (sur le véhicule) / C 401 compte du partenaire
                (montant négatif : le propriétaire doit à l'agence, sens inverse)
  Règlement     D 401 partenaire / C caisse ou banque
Schéma « l'agence exploite pour son compte » : à valider par l'expert-comptable selon les contrats réels.
Le résultat du véhicule (analytique), le décompte (droit contractuel) et le solde du compte partenaire restent distincts.
"""
import calendar
import datetime
import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _arrondi(v):
    return Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def compte_remuneration():
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero="622", defaults={"intitule": "Locations et charges locatives"})[0]


class ContratPartenaire(models.Model):
    COMMISSION, LOCATION = "COMMISSION", "LOCATION"
    MODELES = [(COMMISSION, "Commission de l'agence sur les recettes"), (LOCATION, "Location forfaitaire")]
    MOIS, JOUR = "MOIS", "JOUR"
    PERIODICITES = [(MOIS, "Par mois"), (JOUR, "Par jour")]
    BROUILLON, ACTIF, CLOS = "BROUILLON", "ACTIF", "CLOS"
    STATUTS = [(BROUILLON, "En préparation"), (ACTIF, "En vigueur"), (CLOS, "Terminé / remplacé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, blank=True, help_text="Même numéro pour toutes les versions du contrat")
    version = models.PositiveIntegerField(default=1)
    partenaire = models.ForeignKey("commercial.Tiers", on_delete=models.PROTECT, related_name="contrats_partenaire",
                                   help_text="Le propriétaire (fiche fournisseur : son compte reçoit ce qui lui est dû)")
    vehicule = models.ForeignKey("transport.Vehicule", on_delete=models.PROTECT, related_name="contrats_partenaire")
    modele = models.CharField("Modèle", max_length=12, choices=MODELES, default=COMMISSION)
    debut = models.DateField("En vigueur du")
    fin = models.DateField("Au", null=True, blank=True)
    taux_commission = models.DecimalField("Commission de l'agence (%)", max_digits=5, decimal_places=2, default=ZERO)
    montant_location = models.DecimalField("Montant de la location", max_digits=14, decimal_places=0, default=ZERO)
    periodicite = models.CharField("Location payée", max_length=5, choices=PERIODICITES, default=MOIS)
    charge_carburant = models.BooleanField("Carburant à la charge du propriétaire", default=True)
    charge_reparations = models.BooleanField("Réparations et pièces à sa charge", default=True)
    charge_equipage = models.BooleanField("Salaire de l'équipage à sa charge", default=False)
    charge_route = models.BooleanField("Péages et frais de route à sa charge", default=True)
    charge_autres = models.BooleanField("Autres dépenses du véhicule à sa charge", default=False)
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["vehicule__immatriculation", "-debut"]
        unique_together = [("numero", "version")]
        verbose_name = "Contrat partenaire"

    def __str__(self):
        return f"{self.numero} v{self.version} {self.vehicule.immatriculation} - {self.partenaire.nom}"

    def clean(self):
        if self.fin and self.fin < self.debut:
            raise ValidationError("La fin du contrat précède son début.")
        if self.modele == self.COMMISSION and not ZERO <= self.taux_commission <= 100:
            raise ValidationError("La commission est un pourcentage entre 0 et 100.")
        if self.modele == self.LOCATION and self.montant_location <= 0:
            raise ValidationError("Indiquez le montant de la location.")

    def chevauchements(self):
        fin = self.fin or datetime.date.max
        qs = ContratPartenaire.objects.filter(vehicule=self.vehicule, statut=self.ACTIF, debut__lte=fin).exclude(pk=self.pk)
        return [c for c in qs if c.fin is None or c.fin >= self.debut]

    @transaction.atomic
    def activer(self, utilisateur=None):
        """Met le contrat en vigueur ; refusé s'il chevauche un autre contrat du véhicule."""
        if self.statut != self.BROUILLON:
            raise ValidationError("Ce contrat n'est plus en préparation.")
        self.full_clean()
        autres = self.chevauchements()
        if autres:
            raise ValidationError(f"Le véhicule a déjà un contrat sur cette période : {autres[0]} (faites un avenant).")
        self.numero = self.numero or Sequence.piece("CTP", self.debut.year)
        self.statut, self.approuve_par = self.ACTIF, utilisateur
        self.save()
        if self.vehicule.proprietaire_id != self.partenaire_id:
            self.vehicule.proprietaire = self.partenaire
            self.vehicule.save(update_fields=["proprietaire"])
        return self

    @transaction.atomic
    def avenant(self, a_partir_du, **changements):
        """Nouvelle version datée ; l'ancienne s'arrête la veille et reste dans l'historique."""
        if self.statut != self.ACTIF:
            raise ValidationError("Seul un contrat en vigueur reçoit un avenant.")
        if a_partir_du <= self.debut:
            raise ValidationError("L'avenant prend effet après le début du contrat.")
        nouveau = ContratPartenaire.objects.get(pk=self.pk)
        nouveau.pk, nouveau.uid, nouveau.version, nouveau.debut, nouveau.statut = None, uuid.uuid4(), self.version + 1, a_partir_du, self.BROUILLON
        for champ, valeur in changements.items():
            setattr(nouveau, champ, valeur)
        self.fin, self.statut = a_partir_du - datetime.timedelta(days=1), self.CLOS
        self.save(update_fields=["fin", "statut"])
        nouveau.save()
        return nouveau.activer()

    def categories_a_sa_charge(self):
        return {c for c, actif in (("carburant", self.charge_carburant), ("reparations", self.charge_reparations),
                                   ("equipage", self.charge_equipage), ("route", self.charge_route),
                                   ("autres", self.charge_autres)) if actif}


def _categorie_depense(numero, parametres):
    """Classe une charge du véhicule pour savoir si le contrat la met à la charge du propriétaire."""
    if numero == getattr(parametres.compte_carburant, "numero", ""):
        return "carburant"
    if numero in (getattr(parametres.compte_pieces, "numero", ""), getattr(parametres.compte_main_oeuvre, "numero", "")):
        return "reparations"
    if numero.startswith("66"):
        return "equipage"
    if numero.startswith(("638", "618")):
        return "route"
    return "autres"


class Decompte(models.Model):
    BROUILLON, APPROUVE = "BROUILLON", "APPROUVE"
    STATUTS = [(BROUILLON, "Calculé, à approuver"), (APPROUVE, "Approuvé (comptabilisé)")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    contrat = models.ForeignKey(ContratPartenaire, on_delete=models.PROTECT, related_name="decomptes")
    debut = models.DateField("Du")
    fin = models.DateField("Au")
    recettes = models.DecimalField(max_digits=14, decimal_places=0, default=ZERO)
    commission = models.DecimalField(max_digits=14, decimal_places=0, default=ZERO)
    depenses = models.DecimalField("Dépenses à la charge du propriétaire", max_digits=14, decimal_places=0, default=ZERO)
    location = models.DecimalField(max_digits=14, decimal_places=0, default=ZERO)
    montant_du = models.DecimalField("Dû au propriétaire", max_digits=14, decimal_places=0, default=ZERO)
    detail = models.JSONField(default=dict, blank=True, help_text="Règles appliquées et détail du calcul (figé)")
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approuve_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fin", "-numero"]
        verbose_name = "Décompte partenaire"

    def __str__(self):
        return f"{self.numero} {self.contrat.vehicule.immatriculation} {self.debut:%d/%m} → {self.fin:%d/%m/%Y}"

    @classmethod
    @transaction.atomic
    def calculer(cls, contrat, debut, fin):
        """Recettes et dépenses du véhicule (comptabilité) sur la partie de la période couverte par le contrat."""
        from apps.comptabilite.models import Ecriture, LigneEcriture
        from apps.transport.models import ParametresTransport

        if contrat.statut == ContratPartenaire.BROUILLON:
            raise ValidationError("Le contrat n'est pas en vigueur.")
        d, f = max(debut, contrat.debut), min(fin, contrat.fin or fin)
        if d > f:
            raise ValidationError("Le contrat ne couvre pas cette période.")
        deja = Decompte.objects.filter(contrat__vehicule=contrat.vehicule, debut__lte=f, fin__gte=d).first()
        if deja:
            raise ValidationError(f"Cette période est déjà dans le décompte {deja.numero}.")
        p = ParametresTransport.get()
        remuneration = compte_remuneration().numero
        lignes = (LigneEcriture.objects.filter(vehicule=contrat.vehicule, ecriture__statut=Ecriture.STATUT_VALIDEE,
                                               ecriture__date__range=(d, f)).exclude(compte__numero=remuneration)
                  .select_related("compte"))
        recettes, par_categorie = ZERO, {}
        a_sa_charge = contrat.categories_a_sa_charge()
        for l in lignes:
            n = l.compte.numero
            if n.startswith("7"):
                recettes += l.credit - l.debit
            elif n.startswith("6"):
                c = _categorie_depense(n, p)
                par_categorie[c] = par_categorie.get(c, ZERO) + l.debit - l.credit
        depenses = sum((m for c, m in par_categorie.items() if c in a_sa_charge), ZERO)
        commission = location = ZERO
        if contrat.modele == ContratPartenaire.COMMISSION:
            commission = _arrondi(recettes * contrat.taux_commission / 100)
            du = recettes - commission - depenses
        else:
            jour, total = d, ZERO
            while jour <= f:
                total += (contrat.montant_location if contrat.periodicite == ContratPartenaire.JOUR
                          else contrat.montant_location / calendar.monthrange(jour.year, jour.month)[1])
                jour += datetime.timedelta(days=1)
            location = _arrondi(total)
            du = location - depenses
        return cls.objects.create(
            contrat=contrat, debut=d, fin=f, recettes=recettes, commission=commission, depenses=depenses, location=location,
            montant_du=du, numero=Sequence.piece("DCP", f.year),
            detail={"contrat": contrat.numero, "version": contrat.version, "modele": contrat.modele,
                    "taux_commission": str(contrat.taux_commission), "montant_location": str(contrat.montant_location),
                    "periodicite": contrat.periodicite, "a_sa_charge": sorted(a_sa_charge),
                    "depenses_par_categorie": {c: str(m) for c, m in sorted(par_categorie.items())}})

    @transaction.atomic
    def approuver(self, utilisateur=None, date=None):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.BROUILLON:
            raise ValidationError("Décompte déjà approuvé.")
        partenaire, vehicule = self.contrat.partenaire, self.contrat.vehicule
        compte_partenaire = {"compte": partenaire.get_compte_collectif(), "tiers": partenaire}
        charge = {"compte": compte_remuneration(), "vehicule": vehicule, "section": vehicule.section}
        if self.montant_du:
            m = abs(self.montant_du)
            lignes = ([{**charge, "debit": m}, {**compte_partenaire, "credit": m}] if self.montant_du > 0
                      else [{**compte_partenaire, "debit": m}, {**charge, "credit": m}])
            self.ecriture = creer_ecriture(Journal.objects.get(code="OD"), date or self.fin,
                                           f"Décompte {self.numero} {vehicule.immatriculation} - {partenaire.nom}", lignes,
                                           reference=self.numero)
        self.statut, self.approuve_par, self.approuve_le = self.APPROUVE, utilisateur, timezone.now()
        self.save()
        return self


class ReglementPartenaire(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    partenaire = models.ForeignKey("commercial.Tiers", on_delete=models.PROTECT, related_name="reglements_partenaire")
    decompte = models.ForeignKey(Decompte, null=True, blank=True, on_delete=models.PROTECT, related_name="reglements")
    date = models.DateField(default=timezone.localdate)
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    caisse = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"}, verbose_name="Payé par")
    reference = models.CharField(max_length=60, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Règlement partenaire"

    @transaction.atomic
    def enregistrer(self, utilisateur=None):
        """Paiement réel au partenaire : apure sa dette, sans toucher au résultat du véhicule."""
        from apps.comptabilite.services import creer_ecriture

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        if self.decompte_id and self.decompte.statut != Decompte.APPROUVE:
            raise ValidationError("Le décompte n'est pas encore approuvé.")
        if not self.caisse.compte_tresorerie_id:
            raise ValidationError("Cette caisse ou banque n'a pas de compte de trésorerie.")
        self.numero = self.numero or Sequence.piece("RGP", self.date.year)
        self.cree_par = utilisateur
        self.save()
        self.ecriture = creer_ecriture(self.caisse, self.date, f"Règlement {self.numero} - {self.partenaire.nom}",
                                       [{"compte": self.partenaire.get_compte_collectif(), "tiers": self.partenaire, "debit": self.montant},
                                        {"compte": self.caisse.compte_tresorerie, "credit": self.montant}],
                                       reference=self.reference or self.numero)
        self.save(update_fields=["ecriture"])
        return self


def solde_partenaire(partenaire):
    """Solde du compte du partenaire (crédit = l'agence lui doit)."""
    from apps.comptabilite.models import LigneEcriture

    lignes = LigneEcriture.objects.filter(tiers=partenaire, compte=partenaire.get_compte_collectif())
    return sum((l.credit - l.debit for l in lignes), ZERO)
