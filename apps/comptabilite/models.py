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


class Compte(models.Model):
    numero = models.CharField("N° de compte", max_length=20, unique=True)
    intitule = models.CharField(max_length=200)
    lettrable = models.BooleanField(default=False, help_text="Comptes de tiers pouvant être lettrés")
    actif = models.BooleanField(default=True)

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

    def clean(self):
        if not self.numero.isdigit():
            raise ValidationError({"numero": "Le numéro de compte ne doit contenir que des chiffres."})
        if self.numero[0] == "0":
            raise ValidationError({"numero": "Les classes SYSCOHADA vont de 1 à 9."})

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

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "Journaux"

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
    cree_le = models.DateTimeField(auto_now_add=True)

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
        if self.statut == self.STATUT_VALIDEE:
            return
        if not self.equilibree:
            debit, credit = self.totaux()
            raise ValidationError(f"Écriture déséquilibrée : débit {debit} ≠ crédit {credit}.")
        if self.exercice.cloture:
            raise ValidationError("L'exercice est clôturé.")
        self.statut = self.STATUT_VALIDEE
        self.save(update_fields=["statut"])


class LigneEcriture(models.Model):
    ecriture = models.ForeignKey(Ecriture, on_delete=models.CASCADE, related_name="lignes")
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name="lignes")
    tiers = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="lignes_ecriture")
    libelle = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    lettrage = models.CharField(max_length=10, blank=True, db_index=True)

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
