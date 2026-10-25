"""Personnel et paie. Aucun taux légal n'est imposé : les cotisations (CNPS…) et impôts (IRPP, CAC, CFC, RAV, TDL…)
sont des rubriques que la société paramètre avec son expert-comptable.

Écritures (journal OD), par bulletin, à la validation de la paie :
  D 661 salaire brut (+ comptes des primes)   [sur le véhicule de l'employé s'il en a un : chauffeur, convoyeur]
  C 422 net à payer · C comptes des retenues (CNPS, impôts…) · C 421 avances reprises
  Charges patronales : D compte de charge (664…) / C organisme (431…)
Avance sur salaire : D 421 / C caisse. Paiement des salaires : D 422 / C caisse ou banque.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _arrondi(v):
    return Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _compte(numero, intitule):
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]


class Employe(models.Model):
    BILLETTERIE, COLIS, GARAGE, CONDUITE, ADMINISTRATION, AUTRE = "BILLETTERIE", "COLIS", "GARAGE", "CONDUITE", "ADMIN", "AUTRE"
    SERVICES = [(BILLETTERIE, "Billetterie"), (COLIS, "Colis et expéditions"), (GARAGE, "Garage"),
                (CONDUITE, "Conduite (chauffeurs, convoyeurs)"), (ADMINISTRATION, "Administration, direction"), (AUTRE, "Autre")]
    PAIEMENTS = [("ESPECES", "Espèces"), ("VIREMENT", "Virement"), ("MOBILE_MONEY", "Mobile Money")]

    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField("Nom et prénom", max_length=120)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    poste = models.CharField(max_length=80, blank=True, help_text="Ex. guichetier, chauffeur, mécanicien")
    service = models.CharField(max_length=12, choices=SERVICES, default=AUTRE)
    agence = models.ForeignKey("core.Agence", null=True, blank=True, on_delete=models.PROTECT, related_name="employes")
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT, related_name="employes",
                                 verbose_name="Véhicule affecté",
                                 help_text="Chauffeur, convoyeur : son salaire est compté dans les dépenses de ce véhicule")
    chauffeur = models.OneToOneField("transport.Chauffeur", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="employe", help_text="Fiche chauffeur utilisée sur les départs")
    salaire_base = models.DecimalField("Salaire de base mensuel", max_digits=12, decimal_places=0, default=ZERO)
    date_embauche = models.DateField("Date d'embauche", null=True, blank=True)
    HABITUEL, VOYAGES, JOURS, AGENCE = "HABITUEL", "VOYAGES", "JOURS", "AGENCE"
    VENTILATIONS = [(HABITUEL, "Sur le véhicule affecté"), (VOYAGES, "Au prorata des voyages effectués dans le mois"),
                    (JOURS, "Au prorata des jours passés sur chaque véhicule"), (AGENCE, "Charge de l'agence (aucun véhicule)")]
    ventilation = models.CharField("Salaire imputé", max_length=10, choices=VENTILATIONS, default=HABITUEL,
                                   help_text="Selon l'accord avec la société ; voyages et jours : départs où l'employé est "
                                             "chauffeur ou convoyeur (à défaut : véhicule affecté)")
    numero_cnps = models.CharField("N° CNPS", max_length=30, blank=True)
    mode_paiement = models.CharField("Paiement du salaire", max_length=15, choices=PAIEMENTS, default="ESPECES")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Employé"

    def __str__(self):
        return f"{self.matricule} - {self.nom}"

    def avances_a_reprendre(self):
        return sum((a.montant for a in self.avances.filter(bulletin__isnull=True, ecriture__isnull=False)), ZERO)

    def repartition(self, debut, fin):
        """[(véhicule, fraction)] du coût de l'employé sur la période, selon son mode d'imputation (total = 1)."""
        from collections import Counter

        from django.db.models import Q

        from apps.transport.models import Depart

        habituel = [(self.vehicule, Decimal(1))] if self.vehicule_id else []
        if self.ventilation == self.AGENCE:
            return []
        if self.ventilation == self.HABITUEL:
            return habituel
        filtre = Q(convoyeur=self)
        if self.chauffeur_id:
            filtre |= Q(chauffeur_id=self.chauffeur_id)
        departs = (Depart.objects.filter(filtre, date__range=(debut, fin), vehicule__isnull=False)
                   .filter(statut__in=[Depart.PARTI, Depart.ARRIVE, Depart.CLOTURE]).select_related("vehicule"))
        if self.ventilation == self.VOYAGES:
            poids = Counter(d.vehicule for d in departs)
        else:
            poids = Counter(v for v, _ in {(d.vehicule, d.date) for d in departs})
        total = sum(poids.values())
        if not total:
            return habituel
        return [(v, Decimal(n) / total) for v, n in sorted(poids.items(), key=lambda x: x[0].immatriculation)]


class RubriquePaie(models.Model):
    GAIN, RETENUE, PATRONALE = "GAIN", "RETENUE", "PATRONALE"
    NATURES = [(GAIN, "Gain (prime, indemnité, heures supplémentaires)"), (RETENUE, "Retenue salariale (cotisation, impôt…)"),
               (PATRONALE, "Charge patronale")]
    MONTANT, TAUX = "MONTANT", "TAUX"
    CALCULS = [(MONTANT, "Montant fixe"), (TAUX, "Pourcentage du brut")]

    code = models.CharField(max_length=10, unique=True)
    libelle = models.CharField("Libellé", max_length=100)
    nature = models.CharField(max_length=10, choices=NATURES, default=GAIN)
    calcul = models.CharField(max_length=10, choices=CALCULS, default=MONTANT)
    valeur = models.DecimalField("Montant ou taux (%)", max_digits=12, decimal_places=2, default=ZERO,
                                 help_text="Taux à fixer avec l'expert-comptable : rien n'est imposé par le logiciel")
    plafond = models.DecimalField("Plafond de la base", max_digits=12, decimal_places=0, null=True, blank=True,
                                  help_text="Pour un taux : brut retenu au plus à ce montant (ex. plafond de cotisation)")
    compte = models.ForeignKey("comptabilite.Compte", on_delete=models.PROTECT, related_name="+",
                               help_text="Gain : compte de charge (661…) ; retenue : organisme ou État (431, 447…) ; "
                                         "patronale : compte de charge (664…)")
    compte_contrepartie = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="+", help_text="Charge patronale : organisme à payer (431…)")
    automatique = models.BooleanField("Sur tous les bulletins", default=False,
                                      help_text="Ajoutée d'office à chaque bulletin (sinon, à ajouter employé par employé)")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nature", "code"]
        verbose_name = "Rubrique de paie"
        verbose_name_plural = "Rubriques de paie"

    def __str__(self):
        return f"{self.code} - {self.libelle}"

    def clean(self):
        if self.nature == self.PATRONALE and not self.compte_contrepartie_id:
            raise ValidationError({"compte_contrepartie": "Indiquez l'organisme à payer pour une charge patronale."})

    def montant(self, brut):
        if self.calcul == self.MONTANT:
            return _arrondi(self.valeur)
        base = min(brut, self.plafond) if self.plafond else brut
        return _arrondi(base * self.valeur / 100)


class Avance(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name="avances", verbose_name="Employé")
    date = models.DateField(default=timezone.localdate)
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    caisse = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    motif = models.CharField(max_length=150, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    bulletin = models.ForeignKey("Bulletin", null=True, blank=True, on_delete=models.SET_NULL, related_name="avances_reprises",
                                 help_text="Bulletin sur lequel l'avance a été reprise")

    class Meta:
        ordering = ["-date"]

    @transaction.atomic
    def enregistrer(self):
        from apps.comptabilite.services import creer_ecriture

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        if not self.caisse.compte_tresorerie_id:
            raise ValidationError("Cette caisse n'a pas de compte de trésorerie.")
        self.save()
        self.ecriture = creer_ecriture(self.caisse, self.date, f"Avance sur salaire {self.employe.nom}",
                                       [{"compte": _compte("421", "Personnel, avances et acomptes"), "debit": self.montant},
                                        {"compte": self.caisse.compte_tresorerie, "credit": self.montant}],
                                       reference=self.employe.matricule)
        self.save(update_fields=["ecriture"])
        return self


class PeriodePaie(models.Model):
    BROUILLON, VALIDEE, PAYEE = "BROUILLON", "VALIDEE", "PAYEE"
    STATUTS = [(BROUILLON, "En préparation"), (VALIDEE, "Validée (comptabilisée)"), (PAYEE, "Payée")]

    annee = models.PositiveIntegerField()
    mois = models.PositiveSmallIntegerField()
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_paiement = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                             related_name="+")

    class Meta:
        ordering = ["-annee", "-mois"]
        unique_together = [("annee", "mois")]
        verbose_name = "Paie du mois"

    def __str__(self):
        return f"Paie {self.mois:02d}/{self.annee}"

    @property
    def fin_de_mois(self):
        import calendar
        import datetime

        return datetime.date(self.annee, self.mois, calendar.monthrange(self.annee, self.mois)[1])

    @transaction.atomic
    def generer(self):
        """Prépare un bulletin par employé actif (salaire de base, rubriques automatiques, avances à reprendre)."""
        if self.statut != self.BROUILLON:
            raise ValidationError("La paie est déjà validée.")
        for e in Employe.objects.filter(actif=True):
            bulletin, cree = Bulletin.objects.get_or_create(periode=self, employe=e, defaults={"salaire_base": e.salaire_base})
            if cree:
                for r in RubriquePaie.objects.filter(actif=True, automatique=True):
                    bulletin.lignes.create(rubrique=r)
            bulletin.calculer()
        return self.bulletins.count()

    @transaction.atomic
    def valider(self, date=None):
        """Comptabilise toute la paie du mois (une écriture), salaire des chauffeurs sur leur véhicule."""
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.BROUILLON:
            raise ValidationError("La paie est déjà validée.")
        bulletins = list(self.bulletins.select_related("employe__vehicule"))
        if not bulletins:
            raise ValidationError("Aucun bulletin : préparez d'abord les bulletins.")
        salaires, net_du, avances = _compte("661", "Rémunérations directes versées au personnel national"), \
            _compte("422", "Personnel, rémunérations dues"), _compte("421", "Personnel, avances et acomptes")
        lignes = []
        debut = self.fin_de_mois.replace(day=1)
        for b in bulletins:
            b.calculer()
            repartition = b.employe.repartition(debut, self.fin_de_mois)

            def charges(compte, montant, libelle):
                """Charge répartie sur les véhicules selon le mode d'imputation de l'employé (reste : agence)."""
                if not repartition:
                    return [{"compte": compte, "debit": montant, "libelle": libelle}]
                parts = [_arrondi(montant * f) for _, f in repartition[:-1]]
                parts.append(montant - sum(parts, ZERO))
                return [{"compte": compte, "debit": m, "vehicule": v, "section": v.section, "libelle": libelle}
                        for (v, _), m in zip(repartition, parts) if m]

            lignes += charges(salaires, b.salaire_base, f"Salaire {b.employe.nom}")
            for l in b.lignes.select_related("rubrique"):
                r = l.rubrique
                if r.nature == RubriquePaie.GAIN:
                    lignes += charges(r.compte, l.montant, f"{r.libelle} {b.employe.nom}")
                elif r.nature == RubriquePaie.RETENUE:
                    lignes.append({"compte": r.compte, "credit": l.montant})
                else:
                    lignes += charges(r.compte, l.montant, f"{r.libelle} {b.employe.nom}")
                    lignes.append({"compte": r.compte_contrepartie, "credit": l.montant})
            if b.avances:
                lignes.append({"compte": avances, "credit": b.avances})
            lignes.append({"compte": net_du, "credit": b.net})
            b.avances_a_reprendre().update(bulletin=b)
        self.ecriture = creer_ecriture(Journal.objects.get(code="OD"), date or self.fin_de_mois, f"{self}", lignes,
                                       reference=f"PAIE{self.annee}{self.mois:02d}")
        self.statut = self.VALIDEE
        self.save(update_fields=["statut", "ecriture"])
        return self

    @transaction.atomic
    def payer(self, caisse, date=None):
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.VALIDEE:
            raise ValidationError("Validez la paie avant de la payer.")
        if not caisse.compte_tresorerie_id:
            raise ValidationError("Cette caisse ou banque n'a pas de compte de trésorerie.")
        total = sum((b.net for b in self.bulletins.all()), ZERO)
        self.ecriture_paiement = creer_ecriture(caisse, date or timezone.localdate(), f"Paiement des salaires {self.mois:02d}/{self.annee}",
                                                [{"compte": _compte("422", "Personnel, rémunérations dues"), "debit": total},
                                                 {"compte": caisse.compte_tresorerie, "credit": total}],
                                                reference=f"PAIE{self.annee}{self.mois:02d}")
        self.statut = self.PAYEE
        self.save(update_fields=["statut", "ecriture_paiement"])
        return self


class Bulletin(models.Model):
    periode = models.ForeignKey(PeriodePaie, on_delete=models.CASCADE, related_name="bulletins")
    employe = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name="bulletins")
    salaire_base = models.DecimalField(max_digits=12, decimal_places=0, default=ZERO)
    brut = models.DecimalField(max_digits=12, decimal_places=0, default=ZERO)
    retenues = models.DecimalField(max_digits=12, decimal_places=0, default=ZERO)
    avances = models.DecimalField("Avances reprises", max_digits=12, decimal_places=0, default=ZERO)
    net = models.DecimalField("Net à payer", max_digits=12, decimal_places=0, default=ZERO)
    patronales = models.DecimalField("Charges patronales", max_digits=12, decimal_places=0, default=ZERO)

    class Meta:
        ordering = ["employe__nom"]
        unique_together = [("periode", "employe")]

    def avances_a_reprendre(self):
        return self.employe.avances.filter(models.Q(bulletin__isnull=True) | models.Q(bulletin=self), ecriture__isnull=False,
                                           date__lte=self.periode.fin_de_mois)

    def calculer(self):
        """Gains d'abord (le brut), puis les retenues et charges calculées sur ce brut."""
        lignes = list(self.lignes.select_related("rubrique"))
        brut = self.salaire_base
        for l in lignes:
            if l.rubrique.nature == RubriquePaie.GAIN:
                l.montant = l.montant_saisi if l.montant_saisi is not None else l.rubrique.montant(self.salaire_base)
                brut += l.montant
        retenues = patronales = ZERO
        for l in lignes:
            if l.rubrique.nature != RubriquePaie.GAIN:
                l.montant = l.montant_saisi if l.montant_saisi is not None else l.rubrique.montant(brut)
                if l.rubrique.nature == RubriquePaie.RETENUE:
                    retenues += l.montant
                else:
                    patronales += l.montant
            l.save(update_fields=["montant"])
        avances = sum((a.montant for a in self.avances_a_reprendre()), ZERO)
        self.brut, self.retenues, self.patronales = brut, retenues, patronales
        self.avances = min(avances, max(brut - retenues, ZERO))
        self.net = brut - retenues - self.avances
        self.save(update_fields=["brut", "retenues", "patronales", "avances", "net"])


class LigneBulletin(models.Model):
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name="lignes")
    rubrique = models.ForeignKey(RubriquePaie, on_delete=models.PROTECT, related_name="+")
    montant_saisi = models.DecimalField("Montant saisi", max_digits=12, decimal_places=0, null=True, blank=True,
                                        help_text="Vide : calculé par la rubrique")
    montant = models.DecimalField(max_digits=12, decimal_places=0, default=ZERO)

    class Meta:
        ordering = ["rubrique__nature", "rubrique__code"]
