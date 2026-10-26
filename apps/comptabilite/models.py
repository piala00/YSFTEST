import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

ZERO = Decimal("0")

CLASSES_SYSCOHADA = {
    1: "Comptes de ressources durables",
    2: "Comptes d'actif immobilisé",
    3: "Comptes de stocks",
    4: "Comptes de tiers",
    5: "Comptes de trésorerie",
    6: "Comptes de charges des activités ordinaires",
    7: "Comptes de produits des activités ordinaires",
    8: "Comptes des autres charges et des autres produits",
    9: "Comptes des engagements hors bilan et comptabilité analytique",
}


def longueur_comptes():
    """Longueur fixée des numéros de compte du dossier (0 : libre)."""
    from apps.core.models import Societe

    return Societe.objects.values_list("longueur_comptes", flat=True).first() or 0


def normaliser_numero(numero, longueur=None):
    """Numéro complété par des zéros à droite jusqu'à la longueur du dossier (« 4111 » → « 4111000 » à 7 chiffres).

    Les zéros à droite ne changent pas les regroupements par préfixe (classe 4, compte 41, 411…) : les états et
    les contrôles qui cherchent « commence par 411 » restent justes. Un numéro plus long est laissé tel quel.
    """
    if not isinstance(numero, str):
        return numero
    numero = numero.strip()
    longueur = longueur_comptes() if longueur is None else longueur
    if longueur and numero.isdigit() and len(numero) < longueur:
        return numero.ljust(longueur, "0")
    return numero


class CompteQuerySet(models.QuerySet):
    """Recherche par numéro exact normalisée : Compte.objects.get(numero="467") trouve 4670000 à 7 chiffres."""

    champ_numero = "numero"

    def _normaliser(self, kwargs):
        c = self.champ_numero
        if not any(k in kwargs for k in (c, f"{c}__exact", f"{c}__in")):
            return kwargs
        longueur = longueur_comptes()
        kwargs = dict(kwargs)
        for cle in (c, f"{c}__exact"):
            if cle in kwargs:
                kwargs[cle] = normaliser_numero(kwargs[cle], longueur)
        if f"{c}__in" in kwargs and not isinstance(kwargs[f"{c}__in"], models.QuerySet):
            kwargs[f"{c}__in"] = [normaliser_numero(n, longueur) for n in kwargs[f"{c}__in"]]
        return kwargs

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._normaliser(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._normaliser(kwargs))


class Compte(models.Model):
    numero = models.CharField("N° de compte", max_length=20, unique=True)
    intitule = models.CharField(max_length=200)
    lettrable = models.BooleanField(default=False, help_text="Comptes de tiers pouvant être lettrés")
    actif = models.BooleanField(default=True)

    objects = CompteQuerySet.as_manager()

    class Meta:
        ordering = ["numero"]
        verbose_name = "Compte"
        verbose_name_plural = "Plan comptable"

    def __str__(self):
        return f"{self.numero} - {self.intitule}"

    @property
    def classe(self):
        return int(self.numero[0]) if self.numero and self.numero[0].isdigit() else None

    @property
    def libelle_classe(self):
        return CLASSES_SYSCOHADA.get(self.classe, "")

    def save(self, *args, **kwargs):
        self.numero = normaliser_numero(self.numero)
        super().save(*args, **kwargs)

    def clean(self):
        self.numero = (self.numero or "").strip()
        if not self.numero.isdigit():
            raise ValidationError({"numero": "Le numéro de compte ne doit contenir que des chiffres."})
        if self.numero[0] == "0":
            raise ValidationError({"numero": "Les classes SYSCOHADA vont de 1 à 9."})
        longueur = longueur_comptes()
        if longueur and len(self.numero) > longueur:
            raise ValidationError({"numero": f"Le plan comptable de la société est à {longueur} chiffres."})
        self.numero = normaliser_numero(self.numero, longueur)

    @classmethod
    def par_numero(cls, numero):
        try:
            return cls.objects.get(numero=numero)
        except cls.DoesNotExist:
            raise ValidationError(f"Le compte {numero} n'existe pas dans le plan comptable.")


class Journal(models.Model):
    TYPE_VENTE = "VENTE"
    TYPE_ACHAT = "ACHAT"
    TYPE_TRESORERIE = "TRESORERIE"
    TYPE_OD = "OD"
    TYPE_AN = "AN"
    TYPES = [
        (TYPE_VENTE, "Ventes"),
        (TYPE_ACHAT, "Achats"),
        (TYPE_TRESORERIE, "Trésorerie"),
        (TYPE_OD, "Opérations diverses"),
        (TYPE_AN, "À-nouveaux"),
    ]

    code = models.CharField(max_length=10, unique=True)
    intitule = models.CharField(max_length=100)
    type_journal = models.CharField("Type", max_length=15, choices=TYPES)
    compte_tresorerie = models.ForeignKey(
        Compte, null=True, blank=True, on_delete=models.PROTECT,
        help_text="Pour les journaux de trésorerie (banque, caisse)",
    )
    cloture_au = models.DateField(
        "Période clôturée jusqu'au", null=True, blank=True,
        help_text="Clôture des journaux : aucune écriture ne peut plus être passée ou validée à cette date ou avant",
    )

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "Journaux"

    def __str__(self):
        return f"{self.code} - {self.intitule}"

    def verifier_periode(self, date):
        if self.cloture_au and date <= self.cloture_au:
            raise ValidationError(
                f"Le journal {self.code} est clôturé jusqu'au {self.cloture_au:%d/%m/%Y} : saisie impossible au {date:%d/%m/%Y}.")


class Taxe(models.Model):
    """Structure > Taux de taxes."""

    COLLECTEE = "COLLECTEE"
    DEDUCTIBLE = "DEDUCTIBLE"
    SENS = [(COLLECTEE, "Collectée (ventes)"), (DEDUCTIBLE, "Déductible (achats)")]

    code = models.CharField(max_length=10, unique=True)
    intitule = models.CharField(max_length=100)
    sens = models.CharField(max_length=12, choices=SENS)
    taux = models.DecimalField("Taux (%)", max_digits=5, decimal_places=2)
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name="taxes")

    class Meta:
        ordering = ["code"]
        verbose_name = "Taux de taxe"
        verbose_name_plural = "Taux de taxes"

    def __str__(self):
        return f"{self.code} - {self.intitule} ({self.taux} %)"


class Banque(models.Model):
    """Structure > Banques : compte bancaire de la société, rattaché à un journal de trésorerie."""

    code = models.CharField(max_length=10, unique=True)
    intitule = models.CharField(max_length=100)
    domiciliation = models.CharField(max_length=100, blank=True)
    rib = models.CharField("RIB", max_length=40, blank=True)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="banques",
                                limit_choices_to={"type_journal": "TRESORERIE"})

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.intitule}"

    @property
    def compte(self):
        return self.journal.compte_tresorerie


class SectionAnalytique(models.Model):
    """Structure > Plan analytique : sections regroupées par plan (agences, activités...)."""

    plan = models.CharField("Plan analytique", max_length=50, default="Agences")
    code = models.CharField(max_length=20, unique=True)
    intitule = models.CharField(max_length=100)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["plan", "code"]
        verbose_name = "Section analytique"
        verbose_name_plural = "Plan analytique"

    def __str__(self):
        return f"{self.code} - {self.intitule}"


class Ecriture(models.Model):
    """Pièce comptable : ensemble de lignes équilibrées passées dans un journal."""

    STATUT_BROUILLARD = "BROUILLARD"
    STATUT_VALIDEE = "VALIDEE"
    STATUTS = [(STATUT_BROUILLARD, "Brouillard"), (STATUT_VALIDEE, "Validée")]

    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="ecritures")
    exercice = models.ForeignKey("core.Exercice", on_delete=models.PROTECT, related_name="ecritures")
    numero = models.CharField("N° pièce", max_length=30, unique=True)
    date = models.DateField()
    libelle = models.CharField(max_length=200)
    reference = models.CharField("Référence", max_length=50, blank=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default=STATUT_BROUILLARD)
    origine = models.CharField(max_length=50, blank=True, help_text="Document commercial à l'origine")
    source_cle = models.CharField("Clé dans le dossier d'origine", max_length=80, blank=True, db_index=True)
    source_empreinte = models.CharField(max_length=64, blank=True)
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True,
                                    help_text="Vide : écriture de ce dossier ; sinon reçue d'une agence (consolidation)")
    cree_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                 verbose_name="Créé par")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Écriture"

    def __str__(self):
        return f"{self.numero} - {self.libelle}"

    def totaux(self):
        agg = self.lignes.aggregate(d=Sum("debit"), c=Sum("credit"))
        return agg["d"] or ZERO, agg["c"] or ZERO

    @property
    def total_debit(self):
        return self.totaux()[0]

    @property
    def total_credit(self):
        return self.totaux()[1]

    @property
    def equilibree(self):
        debit, credit = self.totaux()
        return debit == credit and debit > 0

    def valider(self):
        from apps.core.synchronisation import verifier_saisie

        if self.statut == self.STATUT_VALIDEE:
            return
        verifier_saisie("la saisie des écritures")
        if not self.equilibree:
            debit, credit = self.totaux()
            raise ValidationError(f"Écriture déséquilibrée : débit {debit} ≠ crédit {credit}.")
        if self.exercice.cloture:
            raise ValidationError("L'exercice est clôturé.")
        self.journal.verifier_periode(self.date)
        self.statut = self.STATUT_VALIDEE
        self.save(update_fields=["statut"])
        from apps.echanges.publication import publier_ecriture

        publier_ecriture(self)


class LigneEcritureQuerySet(CompteQuerySet):
    """Même normalisation pour les lignes cherchées par numéro de compte (lignes.get(compte__numero="4111"))."""

    champ_numero = "compte__numero"


class LigneEcriture(models.Model):
    ecriture = models.ForeignKey(Ecriture, on_delete=models.CASCADE, related_name="lignes")
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name="lignes")
    tiers = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="lignes_ecriture")
    libelle = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    lettrage = models.CharField(max_length=10, blank=True, db_index=True)
    source_cle = models.CharField("Ligne d'origine", max_length=20, blank=True)
    section = models.ForeignKey(SectionAnalytique, null=True, blank=True, on_delete=models.PROTECT,
                                related_name="lignes", verbose_name="Section analytique")
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="lignes_ecriture", verbose_name="Véhicule",
                                 help_text="Compte du véhicule : ses recettes et ses dépenses (grand livre et balance des véhicules)")
    date_pointage = models.DateField("Pointé le", null=True, blank=True,
                                     help_text="Rapprochement bancaire : date du relevé sur lequel la ligne figure")

    objects = LigneEcritureQuerySet.as_manager()

    class Meta:
        ordering = ["id"]
        verbose_name = "Ligne d'écriture"

    def __str__(self):
        return f"{self.compte.numero} D:{self.debit} C:{self.credit}"

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Les montants doivent être positifs.")
        if self.debit and self.credit:
            raise ValidationError("Une ligne ne peut être à la fois au débit et au crédit.")
        if not self.debit and not self.credit:
            raise ValidationError("Saisir un montant au débit ou au crédit.")
