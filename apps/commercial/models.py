import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def arrondi(valeur, decimales=0):
    """Arrondi commercial (le FCFA n'a pas de centimes)."""
    quantum = Decimal(1).scaleb(-decimales)
    return Decimal(valeur).quantize(quantum, rounding=ROUND_HALF_UP)


class Tiers(models.Model):
    CLIENT = "CLIENT"
    FOURNISSEUR = "FOURNISSEUR"
    TYPES = [(CLIENT, "Client"), (FOURNISSEUR, "Fournisseur")]

    type_tiers = models.CharField("Type", max_length=12, choices=TYPES, default=CLIENT)
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField("Raison sociale / Nom", max_length=150)
    niu = models.CharField("NIU", max_length=30, blank=True)
    rccm = models.CharField("RCCM", max_length=50, blank=True)
    adresse = models.CharField(max_length=200, blank=True)
    ville = models.CharField(max_length=80, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    compte_collectif = models.ForeignKey(
        "comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT,
        help_text="Par défaut : 4111 pour les clients, 4011 pour les fournisseurs",
    )
    delai_paiement = models.PositiveIntegerField("Délai de paiement (jours)", default=30)
    plafond_credit = models.DecimalField("Plafond d'encours", max_digits=18, decimal_places=2, default=ZERO)
    assujetti_tva = models.BooleanField("Assujetti à la TVA", default=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Tiers"
        verbose_name_plural = "Tiers"

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @property
    def est_client(self):
        return self.type_tiers == self.CLIENT

    def get_compte_collectif(self):
        from apps.comptabilite.models import Compte

        if self.compte_collectif_id:
            return self.compte_collectif
        return Compte.par_numero("4111" if self.est_client else "4011")

    def solde_comptable(self):
        """Solde du tiers en comptabilité (débiteur > 0 pour un client qui doit de l'argent)."""
        agg = self.lignes_ecriture.aggregate(d=Sum("debit"), c=Sum("credit"))
        return (agg["d"] or ZERO) - (agg["c"] or ZERO)

    def encours(self):
        """Montant restant dû sur les factures validées."""
        return sum((d.reste_a_payer for d in self.documents.filter(
            type_document__in=Document.TYPES_FACTURATION, statut=Document.VALIDE)), ZERO)


class FamilleArticle(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)
    compte_vente = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    compte_achat = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["libelle"]
        verbose_name = "Famille d'articles"
        verbose_name_plural = "Familles d'articles"

    def __str__(self):
        return self.libelle


class Article(models.Model):
    MARCHANDISE = "MARCHANDISE"
    PRODUIT_FINI = "PRODUIT_FINI"
    SERVICE = "SERVICE"
    NATURES = [(MARCHANDISE, "Marchandise"), (PRODUIT_FINI, "Produit fini"), (SERVICE, "Service")]
    COMPTES_VENTE_DEFAUT = {MARCHANDISE: "701", PRODUIT_FINI: "702", SERVICE: "706"}
    COMPTES_ACHAT_DEFAUT = {MARCHANDISE: "601", PRODUIT_FINI: "602", SERVICE: "605"}

    reference = models.CharField(max_length=30, unique=True)
    designation = models.CharField(max_length=200)
    nature = models.CharField(max_length=15, choices=NATURES, default=MARCHANDISE)
    famille = models.ForeignKey(FamilleArticle, null=True, blank=True, on_delete=models.SET_NULL, related_name="articles")
    unite = models.CharField(max_length=20, default="U")
    prix_achat = models.DecimalField("Prix d'achat HT", max_digits=18, decimal_places=2, default=ZERO)
    prix_vente = models.DecimalField("Prix de vente HT", max_digits=18, decimal_places=2, default=ZERO)
    taux_tva = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=Decimal("19.25"))
    suivi_stock = models.BooleanField(default=True)
    stock = models.DecimalField(max_digits=18, decimal_places=3, default=ZERO)
    stock_minimum = models.DecimalField("Stock d'alerte", max_digits=18, decimal_places=3, default=ZERO)
    compte_vente = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    compte_achat = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["designation"]

    def __str__(self):
        return f"{self.reference} - {self.designation}"

    @property
    def en_alerte(self):
        return self.suivi_stock and self.stock <= self.stock_minimum

    @property
    def valeur_stock(self):
        return self.stock * self.prix_achat

    def get_compte_vente(self):
        from apps.comptabilite.models import Compte

        if self.compte_vente_id:
            return self.compte_vente
        if self.famille and self.famille.compte_vente_id:
            return self.famille.compte_vente
        return Compte.par_numero(self.COMPTES_VENTE_DEFAUT[self.nature])

    def get_compte_achat(self):
        from apps.comptabilite.models import Compte

        if self.compte_achat_id:
            return self.compte_achat
        if self.famille and self.famille.compte_achat_id:
            return self.famille.compte_achat
        return Compte.par_numero(self.COMPTES_ACHAT_DEFAUT[self.nature])


class Document(models.Model):
    """Pièce commerciale : devis, commande, livraison, facture, avoir (ventes et achats)."""

    # Ventes
    DEVIS = "DEVIS"
    COMMANDE = "COMMANDE"
    LIVRAISON = "LIVRAISON"
    FACTURE = "FACTURE"
    AVOIR = "AVOIR"
    # Achats
    ACHAT_COMMANDE = "ACHAT_COMMANDE"
    ACHAT_RECEPTION = "ACHAT_RECEPTION"
    ACHAT_FACTURE = "ACHAT_FACTURE"
    ACHAT_AVOIR = "ACHAT_AVOIR"

    TYPES = [
        (DEVIS, "Devis"),
        (COMMANDE, "Bon de commande client"),
        (LIVRAISON, "Bon de livraison"),
        (FACTURE, "Facture client"),
        (AVOIR, "Avoir client"),
        (ACHAT_COMMANDE, "Bon de commande fournisseur"),
        (ACHAT_RECEPTION, "Bon de réception"),
        (ACHAT_FACTURE, "Facture fournisseur"),
        (ACHAT_AVOIR, "Avoir fournisseur"),
    ]
    PREFIXES = {
        DEVIS: "DV", COMMANDE: "BC", LIVRAISON: "BL", FACTURE: "FA", AVOIR: "AV",
        ACHAT_COMMANDE: "CF", ACHAT_RECEPTION: "BR", ACHAT_FACTURE: "FF", ACHAT_AVOIR: "AF",
    }
    TYPES_VENTE = (DEVIS, COMMANDE, LIVRAISON, FACTURE, AVOIR)
    TYPES_ACHAT = (ACHAT_COMMANDE, ACHAT_RECEPTION, ACHAT_FACTURE, ACHAT_AVOIR)
    TYPES_FACTURATION = (FACTURE, AVOIR, ACHAT_FACTURE, ACHAT_AVOIR)
    TYPES_AVOIR = (AVOIR, ACHAT_AVOIR)
    TYPES_LOGISTIQUES = (LIVRAISON, ACHAT_RECEPTION)
    # Enchaînement autorisé des transformations
    TRANSFORMATIONS = {
        DEVIS: (COMMANDE, FACTURE),
        COMMANDE: (LIVRAISON, FACTURE),
        LIVRAISON: (FACTURE,),
        FACTURE: (AVOIR,),
        ACHAT_COMMANDE: (ACHAT_RECEPTION, ACHAT_FACTURE),
        ACHAT_RECEPTION: (ACHAT_FACTURE,),
        ACHAT_FACTURE: (ACHAT_AVOIR,),
    }

    BROUILLON = "BROUILLON"
    VALIDE = "VALIDE"
    TRANSFORME = "TRANSFORME"
    ANNULE = "ANNULE"
    STATUTS = [(BROUILLON, "Brouillon"), (VALIDE, "Validé"), (TRANSFORME, "Transformé"), (ANNULE, "Annulé")]

    type_document = models.CharField("Type", max_length=20, choices=TYPES)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    date_echeance = models.DateField("Échéance", null=True, blank=True)
    tiers = models.ForeignKey(Tiers, on_delete=models.PROTECT, related_name="documents")
    reference_externe = models.CharField("Réf. externe", max_length=50, blank=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default=BROUILLON)
    origine = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents_generes")
    notes = models.TextField(blank=True)
    total_ht = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    total_tva = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    total_ttc = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="document")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]

    def __str__(self):
        return f"{self.numero_affiche} - {self.tiers.nom}"

    # --- Propriétés -----------------------------------------------------
    @property
    def est_vente(self):
        return self.type_document in self.TYPES_VENTE

    @property
    def est_facturation(self):
        return self.type_document in self.TYPES_FACTURATION

    @property
    def est_avoir(self):
        return self.type_document in self.TYPES_AVOIR

    @property
    def modifiable(self):
        return self.statut == self.BROUILLON

    @property
    def transformations_possibles(self):
        if self.statut not in (self.VALIDE, self.TRANSFORME):
            return []
        libelles = dict(self.TYPES)
        return [(t, libelles[t]) for t in self.TRANSFORMATIONS.get(self.type_document, ())]

    @property
    def montant_regle(self):
        return self.imputations.aggregate(s=Sum("montant"))["s"] or ZERO

    @property
    def reste_a_payer(self):
        if not self.est_facturation or self.est_avoir:
            return ZERO
        return self.total_ttc - self.montant_regle

    @property
    def mouvemente_stock(self):
        """Une facture ne mouvemente le stock que si elle n'est pas issue d'un BL / BR."""
        if self.type_document in self.TYPES_LOGISTIQUES or self.est_avoir:
            return True
        if self.type_document in (self.FACTURE, self.ACHAT_FACTURE):
            return not self._issue_d_un_document_logistique()
        return False

    def _issue_d_un_document_logistique(self):
        doc = self.origine
        while doc is not None:
            if doc.type_document in self.TYPES_LOGISTIQUES:
                return True
            doc = doc.origine
        return False

    # --- Calculs --------------------------------------------------------
    def recalculer(self, save=True):
        lignes = list(self.lignes.all())
        self.total_ht = sum((l.montant_ht for l in lignes), ZERO)
        self.total_tva = sum((l.montant_tva for l in lignes), ZERO)
        self.total_ttc = self.total_ht + self.total_tva
        if save:
            self.save(update_fields=["total_ht", "total_tva", "total_ttc"])

    def ventilation_tva(self):
        """Bases HT et TVA regroupées par taux."""
        bases = {}
        for ligne in self.lignes.all():
            base = bases.setdefault(ligne.taux_tva, {"taux": ligne.taux_tva, "base": ZERO, "tva": ZERO})
            base["base"] += ligne.montant_ht
            base["tva"] += ligne.montant_tva
        return sorted(bases.values(), key=lambda b: b["taux"])

    @property
    def est_brouillon_numero(self):
        return self.numero.startswith("BROU-")

    @property
    def numero_affiche(self):
        return "(brouillon)" if self.est_brouillon_numero else self.numero

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"BROU-{uuid.uuid4().hex[:12].upper()}"
        if not self.date_echeance and self.est_facturation and self.tiers_id:
            self.date_echeance = self.date + timezone.timedelta(days=self.tiers.delai_paiement)
        super().save(*args, **kwargs)

    # --- Cycle de vie ---------------------------------------------------
    def clean(self):
        if self.tiers_id:
            attendu = Tiers.CLIENT if self.type_document in self.TYPES_VENTE else Tiers.FOURNISSEUR
            if self.tiers.type_tiers != attendu:
                raise ValidationError({"tiers": f"Ce type de document requiert un tiers de type « {attendu.lower()} »."})

    @transaction.atomic
    def valider(self):
        from apps.comptabilite.services import comptabiliser_document

        if self.statut != self.BROUILLON:
            raise ValidationError("Seul un document en brouillon peut être validé.")
        if not self.lignes.exists():
            raise ValidationError("Le document ne contient aucune ligne.")
        self.recalculer(save=False)
        if self.est_brouillon_numero:
            self.numero = Sequence.suivant(self.PREFIXES[self.type_document], self.date.year)
        self.statut = self.VALIDE
        self.save()
        if self.mouvemente_stock:
            self._mouvementer_stock()
        if self.est_facturation:
            comptabiliser_document(self)
        if self.origine and self.origine.statut == self.VALIDE:
            self.origine.statut = self.TRANSFORME
            self.origine.save(update_fields=["statut"])
        return self

    def _mouvementer_stock(self):
        entree = (self.type_document in (self.ACHAT_RECEPTION, self.ACHAT_FACTURE, self.AVOIR))
        for ligne in self.lignes.select_related("article"):
            article = ligne.article
            if article is None or not article.suivi_stock:
                continue
            quantite = ligne.quantite if entree else -ligne.quantite
            MouvementStock.objects.create(
                article=article, date=self.date, quantite=quantite, document=self,
                libelle=f"{self.get_type_document_display()} {self.numero}",
            )
            Article.objects.filter(pk=article.pk).update(stock=models.F("stock") + quantite)

    @transaction.atomic
    def transformer(self, type_cible, utilisateur=None):
        if type_cible not in self.TRANSFORMATIONS.get(self.type_document, ()):
            raise ValidationError("Transformation non autorisée pour ce document.")
        if self.statut not in (self.VALIDE, self.TRANSFORME):
            raise ValidationError("Le document doit être validé avant d'être transformé.")
        nouveau = Document.objects.create(
            type_document=type_cible, tiers=self.tiers, origine=self, date=timezone.localdate(),
            reference_externe=self.reference_externe, notes=self.notes, cree_par=utilisateur,
        )
        for ligne in self.lignes.all():
            ligne.pk = None
            ligne.document = nouveau
            ligne.save()
        nouveau.recalculer()
        return nouveau

    @transaction.atomic
    def annuler(self):
        if self.statut == self.BROUILLON:
            self.statut = self.ANNULE
            self.save(update_fields=["statut"])
            return
        if self.est_facturation:
            raise ValidationError("Une facture validée ne s'annule pas : établissez un avoir.")
        if self.mouvemente_stock and self.statut == self.VALIDE:
            for mvt in self.mouvements_stock.all():
                Article.objects.filter(pk=mvt.article_id).update(stock=models.F("stock") - mvt.quantite)
            self.mouvements_stock.all().delete()
        self.statut = self.ANNULE
        self.save(update_fields=["statut"])


class LigneDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, null=True, blank=True, on_delete=models.PROTECT)
    designation = models.CharField(max_length=200, blank=True)
    quantite = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("1"))
    prix_unitaire = models.DecimalField("P.U. HT", max_digits=18, decimal_places=2, default=ZERO)
    remise = models.DecimalField("Remise (%)", max_digits=5, decimal_places=2, default=ZERO)
    taux_tva = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=Decimal("19.25"))
    montant_ht = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    montant_tva = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)

    class Meta:
        ordering = ["id"]
        verbose_name = "Ligne de document"

    def __str__(self):
        return self.designation

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva

    def calculer(self):
        brut = Decimal(self.quantite) * Decimal(self.prix_unitaire)
        self.montant_ht = arrondi(brut * (1 - Decimal(self.remise) / 100))
        self.montant_tva = arrondi(self.montant_ht * Decimal(self.taux_tva) / 100)

    def save(self, *args, **kwargs):
        if self.article_id and not self.designation:
            self.designation = self.article.designation
        if self.document_id and not self.document.tiers.assujetti_tva and self.document.est_vente:
            self.taux_tva = ZERO
        self.calculer()
        super().save(*args, **kwargs)


class Reglement(models.Model):
    ESPECES = "ESPECES"
    CHEQUE = "CHEQUE"
    VIREMENT = "VIREMENT"
    MOBILE_MONEY = "MOBILE_MONEY"
    MODES = [(ESPECES, "Espèces"), (CHEQUE, "Chèque"), (VIREMENT, "Virement"), (MOBILE_MONEY, "Mobile Money")]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    tiers = models.ForeignKey(Tiers, on_delete=models.PROTECT, related_name="reglements")
    mode = models.CharField(max_length=15, choices=MODES, default=ESPECES)
    journal = models.ForeignKey(
        "comptabilite.Journal", on_delete=models.PROTECT,
        limit_choices_to={"type_journal": "TRESORERIE"},
        help_text="Journal de trésorerie (banque, caisse, mobile money)",
    )
    montant = models.DecimalField(max_digits=18, decimal_places=2)
    reference = models.CharField("Référence (n° chèque, transaction...)", max_length=60, blank=True)
    libelle = models.CharField(max_length=200, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="reglement")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Règlement"

    def __str__(self):
        return f"{self.numero} - {self.tiers.nom} - {self.montant}"

    @property
    def est_encaissement(self):
        return self.tiers.est_client

    @property
    def montant_impute(self):
        return self.imputations.aggregate(s=Sum("montant"))["s"] or ZERO

    @property
    def montant_non_impute(self):
        return self.montant - self.montant_impute

    def clean(self):
        if self.montant is not None and self.montant <= 0:
            raise ValidationError({"montant": "Le montant doit être positif."})

    @transaction.atomic
    def enregistrer(self, factures=None):
        """Numérote, comptabilise et impute le règlement sur les factures (FIFO par défaut)."""
        from apps.comptabilite.services import comptabiliser_reglement

        if not self.numero:
            prefixe = "RC" if self.est_encaissement else "RF"
            self.numero = Sequence.suivant(prefixe, self.date.year)
        self.save()
        comptabiliser_reglement(self)
        if factures is None:
            types = (Document.FACTURE,) if self.est_encaissement else (Document.ACHAT_FACTURE,)
            factures = self.tiers.documents.filter(type_document__in=types, statut=Document.VALIDE).order_by("date", "numero")
        disponible = self.montant_non_impute
        for facture in factures:
            if disponible <= 0:
                break
            reste = facture.reste_a_payer
            if reste <= 0:
                continue
            montant = min(reste, disponible)
            Imputation.objects.create(reglement=self, document=facture, montant=montant)
            disponible -= montant
        return self


class Imputation(models.Model):
    reglement = models.ForeignKey(Reglement, on_delete=models.CASCADE, related_name="imputations")
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="imputations")
    montant = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        verbose_name = "Imputation de règlement"


class MouvementStock(models.Model):
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name="mouvements")
    date = models.DateField()
    quantite = models.DecimalField(max_digits=18, decimal_places=3, help_text="Positif = entrée, négatif = sortie")
    document = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="mouvements_stock")
    libelle = models.CharField(max_length=200)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Mouvement de stock"
