"""Véhicules de partenaires propriétaires (audit P3 ; skill réf. 06).

Contrat versionné par véhicule (jamais écrasé : un avenant crée une nouvelle version datée) :
  - COMMISSION : l'agence garde un pourcentage des recettes du véhicule ; le propriétaire reçoit le reste, moins les
    dépenses que le contrat met à sa charge (carburant, réparations, équipage, frais de route, autres) ;
  - LOCATION : l'agence paie un forfait par jour ou par mois (au prorata des jours du contrat) ;
  - VARIABLE : le propriétaire reçoit un pourcentage de la marge du véhicule (recettes − dépenses retenues au contrat) ;
  - FIXE_PLUS_VARIABLE : fixe garanti + complément = % de (marge − fixe) ;
  - AVANCE_SUR_VARIABLE : droit = % de la marge ; le fixe périodique est versé en AVANCE (règlement), jamais en charge.
  Le variable négatif n'est ramené à zéro que si le contrat le prévoit (case « plancher à zéro »).
Décompte de période : calculé depuis la comptabilité du véhicule, figé avec la version du contrat, puis approuvé.
  Approbation   D 622 rémunération du propriétaire (fixe et variable, sur le véhicule) / C 467 compte du propriétaire
                (montant négatif : le propriétaire doit à l'agence, sens inverse)
  Avance, retrait, règlement   D 467 propriétaire / C caisse ou banque (jamais une nouvelle charge)
Le compte du propriétaire (467, paramétrable) est distinct de son éventuel compte fournisseur (401) : pas de
compensation implicite. « Salaire du propriétaire » est un libellé métier : il ne passe jamais par la paie.
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


def compte_proprietaires():
    """Sous-compte des propriétaires de véhicules (distinct des fournisseurs), paramétré dans le transport."""
    from apps.transport.models import ParametresTransport

    return ParametresTransport.get().compte_proprietaires


def compte_remuneration():
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero="622", defaults={"intitule": "Locations et charges locatives"})[0]


class ContratPartenaire(models.Model):
    COMMISSION, LOCATION, VARIABLE, FIXE_PLUS_VARIABLE, AVANCE_SUR_VARIABLE = (
        "COMMISSION", "LOCATION", "VARIABLE", "FIXE_VARIABLE", "AVANCE_VARIABLE")
    MODELES = [(COMMISSION, "Compte du véhicule : recettes − dépenses − pourcentage de la société (+ fixe mensuel éventuel)"),
               (LOCATION, "Salaire mensuel fixe du propriétaire (forfait)"),
               (VARIABLE, "Part du propriétaire sur la marge (variable)"),
               (FIXE_PLUS_VARIABLE, "Fixe garanti + complément variable"),
               (AVANCE_SUR_VARIABLE, "Fixe versé en avance sur le variable")]
    VARIABLES = (VARIABLE, FIXE_PLUS_VARIABLE, AVANCE_SUR_VARIABLE)
    MOIS, JOUR = "MOIS", "JOUR"
    PERIODICITES = [(MOIS, "Par mois"), (JOUR, "Par jour")]
    BROUILLON, ACTIF, CLOS = "BROUILLON", "ACTIF", "CLOS"
    STATUTS = [(BROUILLON, "En préparation"), (ACTIF, "En vigueur"), (CLOS, "Terminé / remplacé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, blank=True, help_text="Même numéro pour toutes les versions du contrat")
    version = models.PositiveIntegerField(default=1)
    partenaire = models.ForeignKey("commercial.Tiers", on_delete=models.PROTECT, related_name="contrats_partenaire",
                                   help_text="Tiers propriétaire de véhicule, sans participation au capital ; compte auxiliaire propriétaire séparé")
    vehicule = models.ForeignKey("transport.Vehicule", on_delete=models.PROTECT, related_name="contrats_partenaire")
    modele = models.CharField("Modèle", max_length=16, choices=MODELES, default=COMMISSION)
    debut = models.DateField("En vigueur du")
    fin = models.DateField("Au", null=True, blank=True)
    RECETTES, MARGE, A_CONFIRMER = "RECETTES", "MARGE", "A_CONFIRMER"
    ASSIETTES = [(A_CONFIRMER, "À confirmer avec le propriétaire du véhicule"), (RECETTES, "Recettes du véhicule"),
                 (MARGE, "Résultat : recettes moins dépenses contractuelles (signé)")]
    assiette_commission = models.CharField("Base du pourcentage société", max_length=12, choices=ASSIETTES, default=RECETTES,
        help_text="Les contrats historiques conservent leur calcul. Pour un nouveau contrat, confirmer explicitement la base.")
    taux_commission = models.DecimalField("Pourcentage de la société (%)", max_digits=5, decimal_places=2,
                                          default=ZERO)
    montant_location = models.DecimalField("Montant fixe (fixe mensuel, location, fixe garanti ou avance)", max_digits=14,
                                           decimal_places=0, default=ZERO,
                                           help_text="Compte du véhicule : fixe versé chaque mois EN PLUS du compte (0 si le "
                                                     "contrat n'en prévoit pas)")
    periodicite = models.CharField("Fixe payé", max_length=5, choices=PERIODICITES, default=MOIS)
    taux_proprietaire = models.DecimalField("Part du propriétaire sur la marge (%)", max_digits=5, decimal_places=2,
                                            default=ZERO, help_text="Modèles variables : base = recettes − dépenses retenues")
    plancher_zero = models.BooleanField("Variable ramené à zéro si la marge est négative", default=False,
                                        help_text="Seulement si le contrat le prévoit ; sinon la perte est due par le propriétaire")
    charge_carburant = models.BooleanField("Carburant à la charge du propriétaire", default=True)
    charge_reparations = models.BooleanField("Réparations et pièces à sa charge", default=True)
    charge_equipage = models.BooleanField("Salaire de l'équipage à sa charge", default=True)
    charge_route = models.BooleanField("Péages et frais de route à sa charge", default=True)
    charge_autres = models.BooleanField("Assurances, papiers et autres charges du véhicule à sa charge", default=True,
                                        help_text="Par défaut, toutes les dépenses du véhicule, gérées et imputées par la "
                                                  "société sans intervention du propriétaire, vont au compte du véhicule")
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
        if self.modele in (self.LOCATION, self.FIXE_PLUS_VARIABLE, self.AVANCE_SUR_VARIABLE) and self.montant_location <= 0:
            raise ValidationError("Indiquez le montant fixe.")
        if self.modele in self.VARIABLES and not ZERO < self.taux_proprietaire <= 100:
            raise ValidationError("Indiquez la part du propriétaire sur la marge (entre 0 et 100 %).")

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
        if self.modele == self.COMMISSION and self.assiette_commission == self.A_CONFIRMER:
            raise ValidationError("Confirmez la base du pourcentage société avant d'activer ce contrat.")
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
    fixe = models.DecimalField("Droit fixe", max_digits=14, decimal_places=0, default=ZERO)
    variable = models.DecimalField("Droit variable", max_digits=14, decimal_places=0, default=ZERO)
    montant_du = models.DecimalField("Dû au propriétaire", max_digits=14, decimal_places=0, default=ZERO)
    detail = models.JSONField(default=dict, blank=True, help_text="Règles appliquées et détail du calcul (figé)")
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_fixe = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="+", help_text="Droit fixe, quand le contrat a fixe et variable")
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approuve_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fin", "-numero"]
        verbose_name = "Décompte partenaire"

    def __str__(self):
        return f"{self.numero} {self.contrat.vehicule.immatriculation} {self.debut:%d/%m} → {self.fin:%d/%m/%Y}"

    @staticmethod
    def evaluer(contrat, debut, fin):
        """Calcul du droit du propriétaire sur la période (sans rien enregistrer) : sert au décompte et à l'aperçu."""
        from apps.comptabilite.models import Ecriture, LigneEcriture
        from apps.transport.models import ParametresTransport

        d, f = max(debut, contrat.debut), min(fin, contrat.fin or fin)
        if d > f:
            raise ValidationError("Le contrat ne couvre pas cette période.")
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
        commission = location = fixe = variable = ZERO

        def prorata_fixe():
            jour, total = d, ZERO
            while jour <= f:
                total += (contrat.montant_location if contrat.periodicite == ContratPartenaire.JOUR
                          else contrat.montant_location / calendar.monthrange(jour.year, jour.month)[1])
                jour += datetime.timedelta(days=1)
            return _arrondi(total)

        marge = recettes - depenses
        if contrat.modele == ContratPartenaire.COMMISSION:
            # Compte du véhicule : recettes − dépenses à sa charge − pourcentage de la société, plus le fixe mensuel éventuel
            if contrat.assiette_commission == ContratPartenaire.A_CONFIRMER:
                raise ValidationError("La base du pourcentage société n'est pas confirmée.")
            base_commission = marge if contrat.assiette_commission == ContratPartenaire.MARGE else recettes
            commission = _arrondi(base_commission * contrat.taux_commission / 100)
            variable = recettes - commission - depenses
            fixe = prorata_fixe() if contrat.montant_location > 0 else ZERO
            du = fixe + variable
        elif contrat.modele == ContratPartenaire.LOCATION:
            location = fixe = prorata_fixe()
            du = location - depenses
        else:
            base = marge
            if contrat.modele == ContratPartenaire.FIXE_PLUS_VARIABLE:
                fixe = prorata_fixe()                    # dû même si la marge est insuffisante (fixe garanti)
                base = marge - fixe
            variable = _arrondi(base * contrat.taux_proprietaire / 100)
            if contrat.plancher_zero and variable < 0:
                variable = ZERO
            du = fixe + variable
        return {"debut": d, "fin": f, "recettes": recettes, "commission": commission, "depenses": depenses,
                "location": location, "fixe": fixe, "variable": variable, "montant_du": du,
                "detail": {"contrat": contrat.numero, "version": contrat.version, "modele": contrat.modele,
                           "taux_commission": str(contrat.taux_commission), "assiette_commission": contrat.assiette_commission,
                           "montant_location": str(contrat.montant_location),
                           "periodicite": contrat.periodicite, "a_sa_charge": sorted(a_sa_charge),
                           "taux_proprietaire": str(contrat.taux_proprietaire), "plancher_zero": contrat.plancher_zero,
                           "marge": str(marge), "avance_periodique": str(contrat.montant_location)
                           if contrat.modele == ContratPartenaire.AVANCE_SUR_VARIABLE else "0",
                           "depenses_par_categorie": {c: str(m) for c, m in sorted(par_categorie.items())}}}

    @classmethod
    @transaction.atomic
    def calculer(cls, contrat, debut, fin):
        """Recettes et dépenses du véhicule (comptabilité) sur la partie de la période couverte par le contrat."""
        if contrat.statut == ContratPartenaire.BROUILLON:
            raise ValidationError("Le contrat n'est pas en vigueur.")
        e = cls.evaluer(contrat, debut, fin)
        deja = Decompte.objects.filter(contrat__vehicule=contrat.vehicule, debut__lte=e["fin"], fin__gte=e["debut"]).first()
        if deja:
            raise ValidationError(f"Cette période est déjà dans le décompte {deja.numero}.")
        return cls.objects.create(contrat=contrat, numero=Sequence.piece("DCP", e["fin"].year), **e)

    @staticmethod
    def compte_en_cours(contrat, jusqua=None):
        """Compte du véhicule depuis le dernier décompte (ou le début du contrat) jusqu'à aujourd'hui : provisoire,
        consultable par le propriétaire ; il devient disponible au retrait une fois le compte arrêté (décompte)."""
        jusqua = jusqua or timezone.localdate()
        dernier = Decompte.objects.filter(contrat__vehicule=contrat.vehicule).order_by("-fin").first()
        debut = max(contrat.debut, dernier.fin + datetime.timedelta(days=1)) if dernier else contrat.debut
        if debut > min(jusqua, contrat.fin or jusqua):
            return None
        return Decompte.evaluer(contrat, debut, jusqua)

    @transaction.atomic
    def approuver(self, utilisateur=None, date=None):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.BROUILLON:
            raise ValidationError("Décompte déjà approuvé.")
        partenaire, vehicule = self.contrat.partenaire, self.contrat.vehicule
        compte_partenaire = {"compte": compte_proprietaires(), "tiers": partenaire}
        charge = {"compte": compte_remuneration(), "vehicule": vehicule, "section": vehicule.section}
        journal, date = Journal.objects.get(code="OD"), date or self.fin
        if self.contrat.modele in ContratPartenaire.VARIABLES:
            parts = [("Droit fixe", self.fixe), ("Droit variable", self.variable)]
        elif self.contrat.modele == ContratPartenaire.COMMISSION and self.fixe:
            parts = [("Fixe mensuel", self.fixe), ("Compte du véhicule", self.variable)]
        else:
            parts = [("Rémunération", self.montant_du)]
        ecritures = []
        for libelle, montant in parts:                  # une écriture par droit : fixe et variable bien distincts
            if not montant:
                continue
            lignes = ([{**charge, "debit": montant}, {**compte_partenaire, "credit": montant}] if montant > 0
                      else [{**compte_partenaire, "debit": -montant}, {**charge, "credit": -montant}])
            ecritures.append(creer_ecriture(journal, date, f"{libelle} {self.numero} {vehicule.immatriculation} - {partenaire.nom}",
                                            lignes, reference=self.numero))
        self.ecriture = ecritures[-1] if ecritures else None
        self.ecriture_fixe = ecritures[0] if len(ecritures) == 2 else None
        self.statut, self.approuve_par, self.approuve_le = self.APPROUVE, utilisateur, timezone.now()
        self.save()
        return self


class ReglementPartenaire(models.Model):
    REGLEMENT, AVANCE, RETRAIT = "REGLEMENT", "AVANCE", "RETRAIT"
    NATURES = [(REGLEMENT, "Règlement"), (AVANCE, "Avance (fixe versé avant le décompte)"), (RETRAIT, "Retrait autorisé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nature = models.CharField(max_length=10, choices=NATURES, default=REGLEMENT)
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
        if self.decompte_id and self.decompte.contrat.partenaire_id != self.partenaire_id:
            raise ValidationError("Ce décompte appartient à un autre propriétaire.")
        if not self.caisse.compte_tresorerie_id:
            raise ValidationError("Cette caisse ou banque n'a pas de compte de trésorerie.")
        self.numero = self.numero or Sequence.piece("RGP", self.date.year)
        self.cree_par = utilisateur
        self.save()
        self.ecriture = creer_ecriture(self.caisse, self.date, f"{self.get_nature_display().split(' (')[0]} {self.numero} - "
                                                               f"{self.partenaire.nom}",
                                       [{"compte": compte_proprietaires(), "tiers": self.partenaire, "debit": self.montant},
                                        {"compte": self.caisse.compte_tresorerie, "credit": self.montant}],
                                       reference=self.reference or self.numero)
        self.save(update_fields=["ecriture"])
        return self


def solde_partenaire(partenaire, jusqua=None):
    """Solde du compte du propriétaire en comptabilité générale (crédit = l'agence lui doit), à une date si donnée.
    Seul le sous-compte propriétaire compte (pas son compte fournisseur) ; les décomptes et règlements passés avant
    la séparation des comptes (sur 401) restent repris."""
    from django.db.models import Q

    from apps.comptabilite.models import LigneEcriture

    anciennes = list(Decompte.objects.filter(contrat__partenaire=partenaire, ecriture__isnull=False).values_list("ecriture_id", flat=True))
    anciennes += list(Decompte.objects.filter(contrat__partenaire=partenaire, ecriture_fixe__isnull=False)
                      .values_list("ecriture_fixe_id", flat=True))
    anciennes += list(ReglementPartenaire.objects.filter(partenaire=partenaire, ecriture__isnull=False).values_list("ecriture_id", flat=True))
    lignes = LigneEcriture.objects.filter(tiers=partenaire).filter(
        Q(compte=compte_proprietaires()) | Q(ecriture_id__in=anciennes, compte=partenaire.get_compte_collectif()))
    if jusqua is not None:
        lignes = lignes.filter(ecriture__date__lte=jusqua)
    return sum((l.credit - l.debit for l in lignes), ZERO)


class DemandeRetrait(models.Model):
    """Retrait demandé par le propriétaire : jamais au-delà de ce qui lui est dû et pas encore engagé, autorisé par
    une autre personne que le demandeur, puis payé (règlement « retrait »). Un résultat positif du véhicule n'ouvre
    pas à lui seul un droit de retrait : seul le solde comptabilisé de son compte compte."""

    DEMANDE, AUTORISE, REFUSE, PAYE = "DEMANDE", "AUTORISE", "REFUSE", "PAYE"
    STATUTS = [(DEMANDE, "Demandé"), (AUTORISE, "Autorisé, à payer"), (REFUSE, "Refusé"), (PAYE, "Payé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    partenaire = models.ForeignKey("commercial.Tiers", on_delete=models.PROTECT, related_name="retraits_partenaire")
    date = models.DateField(default=timezone.localdate)
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    motif = models.CharField(max_length=150, blank=True)
    statut = models.CharField(max_length=10, choices=STATUTS, default=DEMANDE)
    demande_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    decision_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reglement = models.OneToOneField(ReglementPartenaire, null=True, blank=True, on_delete=models.SET_NULL, related_name="retrait")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Demande de retrait"

    @staticmethod
    def disponible(partenaire, sauf=None):
        """Dû comptabilisé au propriétaire, moins les retraits déjà autorisés et pas encore payés."""
        engages = DemandeRetrait.objects.filter(partenaire=partenaire, statut=DemandeRetrait.AUTORISE)
        if sauf is not None:
            engages = engages.exclude(pk=sauf.pk)
        return solde_partenaire(partenaire) - sum((r.montant for r in engages), ZERO)

    def _controler(self):
        dispo = self.disponible(self.partenaire, sauf=self)
        if self.montant > dispo:
            raise ValidationError(f"Retrait de {self.montant:,.0f} refusé : disponible {max(dispo, ZERO):,.0f} FCFA "
                                  f"(dû comptabilisé moins retraits déjà autorisés).".replace(",", " "))

    @transaction.atomic
    def demander(self, utilisateur=None):
        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        self._controler()
        self.numero = self.numero or Sequence.piece("RTP", self.date.year)
        self.demande_par = utilisateur if getattr(utilisateur, "pk", None) else None
        self.save()
        return self

    @transaction.atomic
    def decider(self, autoriser, utilisateur=None, motif=""):
        if self.statut != self.DEMANDE:
            raise ValidationError("Cette demande a déjà reçu une décision.")
        if utilisateur is not None and self.demande_par_id == getattr(utilisateur, "pk", None) and not utilisateur.is_superuser:
            raise ValidationError("Le demandeur ne peut pas autoriser son propre retrait.")
        if autoriser:
            self._controler()                           # le solde a pu changer depuis la demande
        self.statut = self.AUTORISE if autoriser else self.REFUSE
        self.decision_par = utilisateur if getattr(utilisateur, "pk", None) else None
        self.motif = motif.strip() or self.motif
        self.save()
        return self

    @transaction.atomic
    def payer(self, caisse, utilisateur=None):
        type(self).objects.select_for_update().get(pk=self.pk)
        self.refresh_from_db()
        from apps.commercial.models import Tiers
        Tiers.objects.select_for_update().get(pk=self.partenaire_id)
        if self.statut != self.AUTORISE:
            raise ValidationError("Le retrait doit être autorisé avant d'être payé.")
        self._controler()
        r = ReglementPartenaire(partenaire=self.partenaire, montant=self.montant, caisse=caisse, nature=ReglementPartenaire.RETRAIT,
                                reference=self.numero)
        r.enregistrer(utilisateur)
        self.reglement, self.statut = r, self.PAYE
        self.save(update_fields=["reglement", "statut"])
        return self

