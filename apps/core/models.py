from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Societe(models.Model):
    """Fiche unique de l'entreprise utilisatrice de l'ERP."""

    TVA_A_PARAMETRER = ""
    TVA_ASSUJETTIE = "ASSUJETTIE"
    TVA_NON_ASSUJETTIE = "NON_ASSUJETTIE"
    REGIMES_TVA = [
        (TVA_A_PARAMETRER, "À paramétrer"),
        (TVA_ASSUJETTIE, "Assujettie à la TVA"),
        (TVA_NON_ASSUJETTIE, "Non assujettie à la TVA"),
    ]

    raison_sociale = models.CharField(max_length=150, default="Ma Société")
    sigle = models.CharField(max_length=30, blank=True)
    forme_juridique = models.CharField(max_length=30, blank=True, help_text="SARL, SA, SAS, ETS...")
    niu = models.CharField("N° contribuable (NIU)", max_length=30, blank=True)
    rccm = models.CharField("RCCM", max_length=50, blank=True)
    adresse = models.CharField(max_length=200, blank=True)
    ville = models.CharField(max_length=80, blank=True)
    pays = models.CharField(max_length=80, default="Cameroun")
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    devise = models.CharField(max_length=10, default="XAF")
    regime_tva = models.CharField(
        "Régime de TVA", max_length=20, choices=REGIMES_TVA, blank=True, default=TVA_A_PARAMETRER,
        help_text="Non assujettie : les ventes sont facturées sans TVA et la TVA payée aux fournisseurs entre dans "
                  "le coût d'achat (pas de TVA déductible). Confirmez votre régime auprès de votre centre des impôts. "
                  "Le changement s'applique aux documents validés ensuite.")
    taux_tva_defaut = models.DecimalField("Taux TVA par défaut (%)", max_digits=5, decimal_places=2, default=Decimal("19.25"))
    stock_negatif_autorise = models.BooleanField(
        "Autoriser le stock négatif", default=False,
        help_text="Si décoché, une sortie de stock supérieure au stock disponible du dépôt est refusée")
    pied_facture = models.TextField(blank=True, help_text="Mentions affichées en bas des factures")

    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Société"

    def __str__(self):
        return self.raison_sociale

    @property
    def assujettie_tva(self):
        """Tant que le régime n'est pas paramétré, la société est traitée comme assujettie (comportement historique)."""
        return self.regime_tva != self.TVA_NON_ASSUJETTIE

    @property
    def tva_a_parametrer(self):
        return self.regime_tva == self.TVA_A_PARAMETRER

    @classmethod
    def get(cls):
        obj = cls.objects.order_by("pk").first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class Exercice(models.Model):
    code = models.CharField(max_length=20, unique=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    cloture = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_debut"]
        verbose_name = "Exercice comptable"
        verbose_name_plural = "Exercices comptables"

    def __str__(self):
        return self.code

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
            raise ValidationError("La date de début doit précéder la date de fin.")

    @classmethod
    def pour_date(cls, date):
        exercice = cls.objects.filter(date_debut__lte=date, date_fin__gte=date).first()
        if exercice is None:
            raise ValidationError(f"Aucun exercice comptable ne couvre la date du {date:%d/%m/%Y}.")
        if exercice.cloture:
            raise ValidationError(f"L'exercice {exercice.code} est clôturé.")
        return exercice

    @classmethod
    def courant(cls):
        from django.utils import timezone

        today = timezone.localdate()
        return cls.objects.filter(date_debut__lte=today, date_fin__gte=today).first() or cls.objects.first()


class Sequence(models.Model):
    """Compteur de numérotation (factures, pièces comptables...) par code et par année."""

    code = models.CharField(max_length=20)
    annee = models.PositiveIntegerField()
    dernier_numero = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("code", "annee")

    def __str__(self):
        return f"{self.code}{self.annee} → {self.dernier_numero}"

    @classmethod
    def suivant(cls, code, annee, largeur=5):
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(code=code, annee=annee)
            seq.dernier_numero += 1
            seq.save(update_fields=["dernier_numero"])
        return f"{code}{annee}-{seq.dernier_numero:0{largeur}d}"


class DroitAcces(models.Model):
    """Fichier › Autorisations d'accès : niveau d'un profil (groupe) sur une entrée de menu d'un logiciel."""

    from .droits import NIVEAUX as _NIVEAUX

    groupe = models.ForeignKey("auth.Group", on_delete=models.CASCADE, related_name="droits", verbose_name="Profil")
    module = models.CharField("Logiciel", max_length=20)
    code = models.CharField("Entrée de menu", max_length=100)
    niveau = models.CharField(max_length=20, choices=_NIVEAUX)

    class Meta:
        unique_together = ("groupe", "module", "code")
        verbose_name = "Autorisation d'accès"
        verbose_name_plural = "Autorisations d'accès"

    def __str__(self):
        return f"{self.groupe} · {self.module} · {self.code} : {self.get_niveau_display()}"
