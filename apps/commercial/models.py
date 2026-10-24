import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.core.models import Sequence, Societe

ZERO = Decimal("0")


def taux_tva_defaut():
    """Taux proposé à la création d'un article : celui de la fiche société.

    Ne lit que ce champ : SQL Server évalue ce défaut pendant les migrations, avant que les nouvelles colonnes
    de la fiche société n'existent."""
    taux = Societe.objects.order_by("pk").values_list("taux_tva_defaut", flat=True).first()
    return taux if taux is not None else Societe._meta.get_field("taux_tva_defaut").default


def arrondi(valeur, decimales=0):
    """Arrondi commercial (le FCFA n'a pas de centimes)."""
    quantum = Decimal(1).scaleb(-decimales)
    return Decimal(valeur).quantize(quantum, rounding=ROUND_HALF_UP)


class CategorieTarifaire(models.Model):
    """Catégorie tarifaire client (Fichier › Paramètres société › Tiers), ex. GROS, DÉTAIL."""

    code = models.CharField(max_length=20, unique=True)
    intitule = models.CharField(max_length=100)

    class Meta:
        ordering = ["code"]
        verbose_name = "Catégorie tarifaire"
        verbose_name_plural = "Catégories tarifaires"

    def __str__(self):
        return self.intitule


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
    vente_credit = models.BooleanField(
        "Client à crédit", default=True,
        help_text="Décoché : client au comptant (pas de compte de crédit) ; une vente non réglée est signalée")
    RISQUE_AUCUN = "AUCUN"
    RISQUE_AVERTIR = "AVERTIR"
    RISQUE_BLOQUER = "BLOQUER"
    CODES_RISQUE = [(RISQUE_AUCUN, "Pas de contrôle"), (RISQUE_AVERTIR, "Avertissement si dépassement"),
                    (RISQUE_BLOQUER, "Blocage si dépassement")]
    code_risque = models.CharField("Code risque", max_length=10, choices=CODES_RISQUE, default=RISQUE_AVERTIR,
                                   help_text="Réaction quand l'encours dépasse le plafond (clients)")
    categorie_tarifaire = models.ForeignKey(CategorieTarifaire, null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name="clients", verbose_name="Catégorie tarifaire")
    compte_bloque = models.BooleanField(
        "Compte bloqué", default=False,
        help_text="Aucun document ne peut être saisi pour ce tiers (différent du code risque « Blocage », "
                  "qui laisse saisir devis et commandes avec un message)")
    payeur = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="tiers_payes", verbose_name="Tiers payeur",
        help_text="Tiers qui règle les factures (siège, centrale, maison mère). Vide : le tiers règle lui-même.")
    assujetti_tva = models.BooleanField("Assujetti à la TVA", default=True)
    regime_fiscal = models.CharField("Régime d'imposition", max_length=20, choices=Societe.REGIMES_FISCAUX, blank=True,
                                     help_text="Utile pour l'AIR et le précompte (taux selon le régime)")
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

    def clean(self):
        if self.payeur_id:
            if self.payeur_id == self.pk:
                raise ValidationError({"payeur": "Laissez vide quand le tiers règle lui-même."})
            if self.payeur.type_tiers != self.type_tiers:
                raise ValidationError({"payeur": "Le tiers payeur doit être du même type (client ou fournisseur)."})
            if self.payeur.payeur_id:
                raise ValidationError({"payeur": f"{self.payeur.nom} a lui-même un tiers payeur : choisissez ce dernier."})

    @property
    def tiers_payeur(self):
        return self.payeur or self

    def doublons_possibles(self):
        """Tiers de même type au nom identique (casse et espaces ignorées) : à revoir avant de créer un doublon."""
        mots = self.nom.split()
        if not mots:
            return []
        nom = " ".join(mots).lower()
        candidats = Tiers.objects.filter(type_tiers=self.type_tiers, nom__istartswith=mots[0]).exclude(pk=self.pk)
        return [t for t in candidats if " ".join(t.nom.split()).lower() == nom]

    def get_compte_collectif(self):
        from apps.comptabilite.models import Compte

        if self.compte_collectif_id:
            return self.compte_collectif
        return Compte.par_numero("4111" if self.est_client else "4011")

    def solde_comptable(self):
        """Solde du tiers en comptabilité (débiteur > 0 pour un client qui doit de l'argent)."""
        agg = self.lignes_ecriture.aggregate(d=Sum("debit"), c=Sum("credit"))
        return (agg["d"] or ZERO) - (agg["c"] or ZERO)

    def depassement_encours(self, montant_supplementaire=ZERO):
        """Montant au-delà du plafond si l'on ajoute `montant_supplementaire` à l'encours (0 si aucun)."""
        if not self.plafond_credit:
            return ZERO
        total = self.encours() + montant_supplementaire
        return max(total - self.plafond_credit, ZERO)

    def factures_a_regler(self):
        """Factures et avoirs validés dont ce tiers est le payeur (les siennes et celles des tiers qu'il paie)."""
        return Document.objects.filter(Q(payeur=self) | Q(payeur__isnull=True, tiers=self),
                                       type_document__in=Document.TYPES_FACTURATION, statut=Document.VALIDE)

    def recus_en_attente(self):
        """Reçus de ce client dont une partie attend d'être rattachée à une facture (hors avances sur commande)."""
        recus = (Reglement.objects.filter(tiers=self, commande__isnull=True).annotate(impute=Sum("imputations__montant"))
                 .order_by("date", "numero"))
        return [r for r in recus if r.montant > (r.impute or ZERO)]

    def encours(self):
        """Montant restant dû sur les factures validées dont il est le payeur."""
        return sum((d.reste_a_payer for d in self.factures_a_regler()), ZERO)


class Depot(models.Model):
    """Dépôt de stockage (magasin, agence, entrepôt)."""

    code = models.CharField(max_length=20, unique=True)
    intitule = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200, blank=True)
    ville = models.CharField(max_length=80, blank=True)
    responsable = models.CharField(max_length=100, blank=True)
    principal = models.BooleanField("Dépôt principal", default=False)
    vente_detail = models.BooleanField(
        "Vente au détail autorisée", default=False,
        help_text="Boutique / dépôt de détail : seul type de dépôt où l'on peut vendre au détail quand la société réserve "
                  "le détail à des dépôts désignés (Paramètres de la société)")
    fiche_debut = models.DateField(
        "Début de la fiche de stock", null=True, blank=True,
        help_text="Le fichiste pointe les bons à partir de cette date ; le stock antérieur sert d'ouverture de la fiche. "
                  "Vide : dès la première entrée de stock du dépôt dans le logiciel")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["-principal", "intitule"]
        verbose_name = "Dépôt de stockage"
        verbose_name_plural = "Dépôts de stockage"

    def __str__(self):
        return self.intitule

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.principal:
            Depot.objects.exclude(pk=self.pk).filter(principal=True).update(principal=False)

    @classmethod
    def par_defaut(cls):
        depot = cls.objects.filter(principal=True).first() or cls.objects.filter(actif=True).first()
        if depot is None:
            depot = cls.objects.create(code="DP", intitule="Dépôt principal", principal=True)
        return depot


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
    taux_tva = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=taux_tva_defaut,
                                   help_text="Taux légal du produit, appliqué aux achats et, si la société est assujettie, aux ventes")
    suivi_stock = models.BooleanField(default=True)
    stock = models.DecimalField("Stock total", max_digits=18, decimal_places=3, default=ZERO)
    cmup = models.DecimalField("CMUP", max_digits=18, decimal_places=4, default=ZERO,
                               help_text="Coût moyen unitaire pondéré, recalculé à chaque entrée en stock")
    stock_minimum = models.DecimalField("Stock d'alerte", max_digits=18, decimal_places=3, default=ZERO)
    fournisseur_principal = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, related_name="articles_fournis",
                                              limit_choices_to={"type_tiers": "FOURNISSEUR"},
                                              help_text="Fournisseur proposé par le réapprovisionnement")
    compte_vente = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    compte_achat = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    article_detail = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="articles_gros",
        verbose_name="Article de détail",
        help_text="Article vendu au détail (ex. bouteille de 1 L) : au transfert vers un dépôt de vente au détail, "
                  "cet article y est converti automatiquement")
    facteur_detail = models.DecimalField(
        "Unités de détail par unité", max_digits=12, decimal_places=3, null=True, blank=True,
        help_text="Ex. 15 : un carton de 15 L donne 15 bouteilles de 1 L")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["designation"]

    def clean(self):
        if bool(self.article_detail_id) != bool(self.facteur_detail):
            raise ValidationError("Indiquez à la fois l'article de détail et le nombre d'unités de détail par unité.")
        if self.article_detail_id:
            detail = self.article_detail
            if self.facteur_detail <= 0:
                raise ValidationError({"facteur_detail": "Le nombre d'unités de détail doit être positif."})
            if detail.pk == self.pk or detail.article_detail_id:
                raise ValidationError({"article_detail": "Choisissez un article de détail simple (pas cet article, "
                                                         "ni un article qui se convertit lui-même)."})
            if self.suivi_stock and not detail.suivi_stock:
                raise ValidationError({"article_detail": "L'article de détail doit être suivi en stock."})

    def prix_pour(self, tiers):
        """Prix de vente HT pour un client et sa source (« catégorie GROS », « fiche article »)."""
        if tiers is not None and tiers.categorie_tarifaire_id:
            tarif = self.tarifs.filter(categorie_id=tiers.categorie_tarifaire_id).first()
            if tarif:
                return tarif.prix_vente, f"catégorie tarifaire {tiers.categorie_tarifaire}"
        return self.prix_vente, "fiche article"

    def __str__(self):
        return f"{self.reference} - {self.designation}"

    @property
    def en_alerte(self):
        return self.suivi_stock and self.stock <= self.stock_minimum

    @property
    def cout_unitaire(self):
        """Coût de valorisation du stock : CMUP, à défaut prix d'achat."""
        return self.cmup or self.prix_achat

    @property
    def valeur_stock(self):
        return arrondi(self.stock * self.cout_unitaire)

    def recalculer_cmup(self, quantite, cout):
        """CMUP = (stock × CMUP + quantité entrée × coût d'entrée) / (stock + quantité entrée)."""
        stock = max(self.stock, ZERO)
        total = stock + quantite
        nouveau = ((stock * self.cout_unitaire + quantite * Decimal(cout)) / total) if total > 0 else Decimal(cout)
        self.cmup = nouveau.quantize(Decimal("0.0001"))
        Article.objects.filter(pk=self.pk).update(cmup=self.cmup)

    def stock_depot(self, depot):
        ligne = self.stocks_depots.filter(depot=depot).first()
        return ligne.quantite if ligne else ZERO

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
    """Pièce commerciale : documents des ventes, des achats et des stocks (comme dans Sage 100c)."""

    # Ventes (Sage 100 : Traitement › Documents des ventes)
    DEVIS = "DEVIS"
    COMMANDE = "COMMANDE"
    PREPARATION = "PREPARATION"
    LIVRAISON = "LIVRAISON"
    RETOUR = "RETOUR"
    AVOIR_FINANCIER = "AVOIR_FINANCIER"
    FACTURE = "FACTURE"
    FACTURE_RETOUR = "FACTURE_RETOUR"
    AVOIR = "AVOIR"
    # Achats (Traitement › Documents des achats)
    ACHAT_DEMANDE = "ACHAT_DEMANDE"
    ACHAT_PREPARATION = "ACHAT_PREPARATION"
    ACHAT_COMMANDE = "ACHAT_COMMANDE"
    ACHAT_RECEPTION = "ACHAT_RECEPTION"
    ACHAT_RETOUR = "ACHAT_RETOUR"
    ACHAT_AVOIR_FINANCIER = "ACHAT_AVOIR_FINANCIER"
    ACHAT_FACTURE = "ACHAT_FACTURE"
    ACHAT_FACTURE_RETOUR = "ACHAT_FACTURE_RETOUR"
    ACHAT_AVOIR = "ACHAT_AVOIR"
    # Stocks (Traitement › Documents des stocks)
    STOCK_ENTREE = "STOCK_ENTREE"
    STOCK_SORTIE = "STOCK_SORTIE"
    STOCK_VIREMENT = "STOCK_VIREMENT"

    TYPES = [
        (DEVIS, "Devis"),
        (COMMANDE, "Bon de commande"),
        (PREPARATION, "Préparation de livraison"),
        (LIVRAISON, "Bon de livraison"),
        (RETOUR, "Bon de retour"),
        (AVOIR_FINANCIER, "Bon d'avoir financier"),
        (FACTURE, "Facture"),
        (FACTURE_RETOUR, "Facture de retour"),
        (AVOIR, "Facture d'avoir"),
        (ACHAT_DEMANDE, "Demande d'achat"),
        (ACHAT_PREPARATION, "Préparation de commande"),
        (ACHAT_COMMANDE, "Bon de commande fournisseur"),
        (ACHAT_RECEPTION, "Bon de livraison fournisseur"),
        (ACHAT_RETOUR, "Bon de retour fournisseur"),
        (ACHAT_AVOIR_FINANCIER, "Bon d'avoir financier fournisseur"),
        (ACHAT_FACTURE, "Facture fournisseur"),
        (ACHAT_FACTURE_RETOUR, "Facture de retour fournisseur"),
        (ACHAT_AVOIR, "Facture d'avoir fournisseur"),
        (STOCK_ENTREE, "Mouvement d'entrée"),
        (STOCK_SORTIE, "Mouvement de sortie"),
        (STOCK_VIREMENT, "Mouvement de transfert"),
    ]
    PREFIXES = {
        DEVIS: "DE", COMMANDE: "BC", PREPARATION: "PL", LIVRAISON: "BL", RETOUR: "BR", AVOIR_FINANCIER: "BA",
        FACTURE: "FA", FACTURE_RETOUR: "FR", AVOIR: "AV",
        ACHAT_DEMANDE: "DA", ACHAT_PREPARATION: "PC", ACHAT_COMMANDE: "CF", ACHAT_RECEPTION: "LF", ACHAT_RETOUR: "RT",
        ACHAT_AVOIR_FINANCIER: "AA", ACHAT_FACTURE: "FF", ACHAT_FACTURE_RETOUR: "FT", ACHAT_AVOIR: "AF",
        STOCK_ENTREE: "ME", STOCK_SORTIE: "MS", STOCK_VIREMENT: "MT",
    }
    TYPES_VENTE = (DEVIS, COMMANDE, PREPARATION, LIVRAISON, RETOUR, AVOIR_FINANCIER, FACTURE, FACTURE_RETOUR, AVOIR)
    TYPES_ACHAT = (ACHAT_DEMANDE, ACHAT_PREPARATION, ACHAT_COMMANDE, ACHAT_RECEPTION, ACHAT_RETOUR,
                   ACHAT_AVOIR_FINANCIER, ACHAT_FACTURE, ACHAT_FACTURE_RETOUR, ACHAT_AVOIR)
    TYPES_STOCK = (STOCK_ENTREE, STOCK_SORTIE, STOCK_VIREMENT)
    # Documents comptabilisés (journal des ventes / des achats)
    TYPES_FACTURATION = (FACTURE, FACTURE_RETOUR, AVOIR, ACHAT_FACTURE, ACHAT_FACTURE_RETOUR, ACHAT_AVOIR)
    TYPES_AVOIR = (FACTURE_RETOUR, AVOIR, ACHAT_FACTURE_RETOUR, ACHAT_AVOIR)
    # Documents sans mouvement de stock ni écriture, sauf indication contraire
    TYPES_SANS_DEPOT = (DEVIS, COMMANDE, AVOIR_FINANCIER, AVOIR, ACHAT_DEMANDE, ACHAT_PREPARATION, ACHAT_COMMANDE,
                        ACHAT_AVOIR_FINANCIER, ACHAT_AVOIR)
    TYPES_LIVRAISON = (LIVRAISON, ACHAT_RECEPTION)
    TYPES_RETOUR = (RETOUR, ACHAT_RETOUR)
    # Sens du mouvement de stock
    TYPES_ENTREE = (ACHAT_RECEPTION, ACHAT_FACTURE, RETOUR, FACTURE_RETOUR, STOCK_ENTREE)
    TYPES_SORTIE = (LIVRAISON, FACTURE, ACHAT_RETOUR, ACHAT_FACTURE_RETOUR, STOCK_SORTIE)
    # Entrées qui fixent un nouveau coût d'achat (recalcul du CMUP)
    TYPES_ENTREE_VALORISEE = (ACHAT_RECEPTION, ACHAT_FACTURE, STOCK_ENTREE)
    # Enchaînement des transformations (comme dans Sage 100)
    TRANSFORMATIONS = {
        DEVIS: (COMMANDE, PREPARATION, LIVRAISON, FACTURE),
        COMMANDE: (PREPARATION, LIVRAISON, FACTURE),
        PREPARATION: (LIVRAISON, FACTURE),
        LIVRAISON: (FACTURE, RETOUR),
        RETOUR: (FACTURE_RETOUR,),
        AVOIR_FINANCIER: (AVOIR,),
        FACTURE: (AVOIR, FACTURE_RETOUR),
        ACHAT_DEMANDE: (ACHAT_PREPARATION, ACHAT_COMMANDE),
        ACHAT_PREPARATION: (ACHAT_COMMANDE, ACHAT_RECEPTION),
        ACHAT_COMMANDE: (ACHAT_RECEPTION, ACHAT_FACTURE),
        ACHAT_RECEPTION: (ACHAT_FACTURE, ACHAT_RETOUR),
        ACHAT_RETOUR: (ACHAT_FACTURE_RETOUR,),
        ACHAT_AVOIR_FINANCIER: (ACHAT_AVOIR,),
        ACHAT_FACTURE: (ACHAT_AVOIR, ACHAT_FACTURE_RETOUR),
    }

    BROUILLON = "BROUILLON"
    VALIDE = "VALIDE"
    TRANSFORME = "TRANSFORME"
    ANNULE = "ANNULE"
    STATUTS = [(BROUILLON, "Brouillon"), (VALIDE, "Validé"), (TRANSFORME, "Transformé"), (ANNULE, "Annulé")]

    type_document = models.CharField("Type", max_length=30, choices=TYPES)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    date_echeance = models.DateField("Échéance", null=True, blank=True)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.PROTECT, related_name="documents")
    payeur = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.PROTECT, related_name="documents_payes",
                               verbose_name="Tiers payeur", help_text="Repris de la fiche du tiers ; vide : le tiers lui-même")
    depot = models.ForeignKey(Depot, null=True, blank=True, on_delete=models.PROTECT, related_name="documents",
                              verbose_name="Dépôt")
    depot_destination = models.ForeignKey(Depot, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                          verbose_name="Dépôt de destination")
    reference_externe = models.CharField("Référence", max_length=50, blank=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default=BROUILLON)
    origine = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents_generes")
    notes = models.TextField(blank=True)
    total_ht = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    total_tva = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    total_ttc = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="document")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le = models.DateTimeField(auto_now_add=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    annule_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    annule_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-numero"]

    def __str__(self):
        return f"{self.numero_affiche} - {self.tiers.nom if self.tiers_id else self.get_type_document_display()}"

    # --- Propriétés -----------------------------------------------------
    @property
    def domaine(self):
        if self.type_document in self.TYPES_VENTE:
            return "ventes"
        return "achats" if self.type_document in self.TYPES_ACHAT else "stocks"

    @property
    def est_vente(self):
        return self.type_document in self.TYPES_VENTE

    @property
    def est_stock(self):
        return self.type_document in self.TYPES_STOCK

    @property
    def est_virement(self):
        return self.type_document == self.STOCK_VIREMENT

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
        if self.statut != self.VALIDE:
            return []
        libelles = dict(self.TYPES)
        return [(t, libelles[t]) for t in self.TRANSFORMATIONS.get(self.type_document, ())]

    @property
    def partiellement_transforme(self):
        """Document validé dont une partie seulement a été reprise (reliquat)."""
        return self.statut == self.VALIDE and any(l.quantite_transformee > 0 for l in self.lignes.all())

    @property
    def montant_regle(self):
        return self.imputations.aggregate(s=Sum("montant"))["s"] or ZERO

    @property
    def reste_a_payer(self):
        if not self.est_facturation or self.est_avoir:
            return ZERO
        return self.total_ttc - self.montant_regle

    def _chaine_contient(self, types):
        doc = self.origine
        while doc is not None:
            if doc.type_document in types:
                return True
            doc = doc.origine
        return False

    @property
    def mouvemente_stock(self):
        """Règles Sage 100 : les factures d'avoir et bons d'avoir financiers ne touchent pas le stock ;
        une facture issue d'un bon de livraison, ou une facture de retour issue d'un bon de retour,
        ne mouvemente pas une seconde fois le stock."""
        t = self.type_document
        if t in self.TYPES_STOCK or t in self.TYPES_LIVRAISON or t in self.TYPES_RETOUR:
            return True
        if t in (self.FACTURE, self.ACHAT_FACTURE):
            return not self._chaine_contient(self.TYPES_LIVRAISON)
        if t in (self.FACTURE_RETOUR, self.ACHAT_FACTURE_RETOUR):
            return not self._chaine_contient(self.TYPES_RETOUR)
        return False

    # --- Calculs --------------------------------------------------------
    def recalculer(self, save=True):
        lignes = list(self.lignes.all())
        self.total_ht = sum((l.montant_ht for l in lignes), ZERO)
        self.total_tva = sum((l.montant_tva for l in lignes), ZERO)
        self.total_ttc = self.total_ht + self.total_tva
        if save:
            self.save(update_fields=["total_ht", "total_tva", "total_ttc"])

    # Taux TTC → taux du principal : la TVA camerounaise est un principal majoré de 10 % de CAC (CGI 2026)
    PRINCIPAL_TVA = {Decimal("19.25"): Decimal("17.5"), Decimal("11"): Decimal("10")}

    def ventilation_tva(self):
        """Bases HT et TVA regroupées par taux, avec la part principal / CAC (centimes additionnels communaux)."""
        bases = {}
        for ligne in self.lignes.all():
            base = bases.setdefault(ligne.taux_tva, {"taux": ligne.taux_tva, "base": ZERO, "tva": ZERO})
            base["base"] += ligne.montant_ht
            base["tva"] += ligne.montant_tva
        for b in bases.values():
            principal = self.PRINCIPAL_TVA.get(Decimal(b["taux"]).normalize())
            if principal is not None:
                b["taux_principal"] = principal
                b["principal"] = arrondi(b["tva"] / Decimal("1.1"))
                b["cac"] = b["tva"] - b["principal"]
        return sorted(bases.values(), key=lambda b: b["taux"])

    def mentions_manquantes(self):
        """Mentions de la facture exigées par le CGI 2026, art. 150-5, absentes des fiches (liste vide si complet)."""
        societe = Societe.get()
        if not (societe.controle_mentions_facture and self.est_vente and self.est_facturation):
            return []                  # contrôle facultatif, activé dans la fiche société
        manque = []
        if not societe.niu:
            manque.append("NIU de la société")
        if not societe.rccm:
            manque.append("N° RCCM de la société")
        if not (societe.adresse or societe.ville):
            manque.append("adresse de la société")
        if self.tiers_id and not self.tiers.niu:
            manque.append(f"NIU du client {self.tiers.nom}")
        if self.tiers_id and not (self.tiers.adresse or self.tiers.ville):
            manque.append(f"adresse du client {self.tiers.nom}")
        return manque

    @property
    def est_brouillon_numero(self):
        return self.numero.startswith("BROU-")

    # Colonne « Statut » des listes de documents, sur le modèle de Sage (« A préparer », « A facturer »,
    # « A comptabiliser »…) ; ici la facture est comptabilisée dès sa validation.
    STATUTS_LISTE = {
        DEVIS: "Accepté", COMMANDE: "A préparer", PREPARATION: "A livrer", LIVRAISON: "A facturer", RETOUR: "A facturer",
        AVOIR_FINANCIER: "A facturer", ACHAT_DEMANDE: "A commander", ACHAT_PREPARATION: "A commander",
        ACHAT_COMMANDE: "A réceptionner", ACHAT_RECEPTION: "A facturer", ACHAT_RETOUR: "A facturer",
        ACHAT_AVOIR_FINANCIER: "A facturer",
    }

    @property
    def statut_liste(self):
        if self.statut == self.BROUILLON:
            return "Saisi"
        if self.statut == self.ANNULE:
            return "Annulé"
        if self.statut == self.TRANSFORME:
            return "Transformé"
        if self.est_facturation:
            return "Comptabilisé" if self.ecriture_id else "A comptabiliser"
        return self.STATUTS_LISTE.get(self.type_document, "Validé")

    @property
    def numero_affiche(self):
        return "(brouillon)" if self.est_brouillon_numero else self.numero

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"BROU-{uuid.uuid4().hex[:12].upper()}"
        if not self.depot_id and self.type_document not in self.TYPES_SANS_DEPOT:
            self.depot = Depot.par_defaut()
        if not self.date_echeance and self.est_facturation and self.tiers_id:
            self.date_echeance = self.date + timezone.timedelta(days=self.tiers.delai_paiement)
        if self._state.adding and not self.payeur_id and self.tiers_id:
            self.payeur_id = self.tiers.payeur_id           # payeur de la fiche, figé sur la pièce
        super().save(*args, **kwargs)

    @property
    def tiers_payeur(self):
        """Tiers dont le compte porte la créance ou la dette de la pièce."""
        return self.payeur or self.tiers

    def commandes_d_origine(self):
        """Bons de commande dont la pièce est issue (en remontant livraison, préparation…)."""
        commandes, doc, vus = [], self.origine, set()
        while doc and doc.pk not in vus:
            vus.add(doc.pk)
            if doc.type_document in (self.COMMANDE, self.ACHAT_COMMANDE):
                commandes.append(doc)
            doc = doc.origine
        return commandes

    def facture_issue(self):
        """Facture validée issue de cette commande (en descendant les transformations), ou None."""
        a_voir, vus = list(self.documents_generes.all()), set()
        while a_voir:
            doc = a_voir.pop(0)
            if doc.pk in vus:
                continue
            vus.add(doc.pk)
            if doc.est_facturation and not doc.est_avoir and doc.statut == self.VALIDE:
                return doc
            a_voir.extend(doc.documents_generes.all())
        return None

    def imputer_acomptes(self):
        """Facture validée : les acomptes versés sur la commande d'origine viennent en déduction."""
        if not self.est_facturation or self.est_avoir:
            return
        for commande in self.commandes_d_origine():
            for acompte in commande.acomptes.all():
                reste, disponible = self.reste_a_payer, acompte.montant_non_impute
                if reste <= 0:
                    return
                if disponible > 0:
                    Imputation.objects.create(reglement=acompte, document=self, montant=min(reste, disponible))

    # --- Cycle de vie ---------------------------------------------------
    def clean(self):
        if self.est_stock:
            if self.est_virement:
                if not self.depot_destination_id:
                    raise ValidationError({"depot_destination": "Indiquez le dépôt de destination."})
                if self.depot_destination_id == self.depot_id:
                    raise ValidationError({"depot_destination": "Le dépôt de destination doit être différent du dépôt d'origine."})
            return
        if not self.tiers_id:
            raise ValidationError({"tiers": "Ce document requiert un tiers."})
        attendu = Tiers.CLIENT if self.type_document in self.TYPES_VENTE else Tiers.FOURNISSEUR
        if self.tiers.type_tiers != attendu:
            raise ValidationError({"tiers": f"Ce type de document requiert un tiers de type « {attendu.lower()} »."})
        if self.tiers.compte_bloque:
            raise ValidationError({"tiers": f"Le compte de {self.tiers.nom} est bloqué : aucun document ne peut être saisi."})
        if self.payeur_id:
            if self.payeur.type_tiers != self.tiers.type_tiers:
                raise ValidationError({"payeur": "Le tiers payeur doit être du même type que le tiers."})
            if self.payeur.compte_bloque:
                raise ValidationError({"payeur": f"Le compte du payeur {self.payeur.nom} est bloqué."})

    # Pièces de vente soumises au contrôle d'encours (plafond et code risque du client)
    TYPES_CONTROLE_ENCOURS = (COMMANDE, PREPARATION, LIVRAISON, FACTURE)
    # Avec le code risque « Blocage », Sage laisse saisir devis et commandes avec un message (aide Sage « encours client »)
    TYPES_RISQUE_MESSAGE = (DEVIS, COMMANDE)

    def controler_encours(self):
        """Bloque (ValidationError) ou renvoie un avertissement si la pièce fait dépasser le plafond."""
        if self.type_document not in self.TYPES_CONTROLE_ENCOURS or not self.tiers_id:
            return None
        tiers = self.tiers_payeur               # l'encours se contrôle sur le payeur, qui porte la créance
        if tiers.type_tiers == Tiers.CLIENT and not tiers.vente_credit:
            return (f"{tiers.nom} est un client au comptant : encaissez le règlement de la pièce "
                    f"(ou une avance sur la commande), sans crédit.")
        if tiers.code_risque == Tiers.RISQUE_AUCUN or not tiers.plafond_credit:
            return None
        # Une facture issue d'un BL ou d'une commande ne compte qu'une fois : seule la facture crée la créance
        depassement = tiers.depassement_encours(self.total_ttc)
        if not depassement:
            return None
        message = (f"Encours de {tiers.nom} : {tiers.encours() + self.total_ttc:,.0f} pour un plafond de "
                   f"{tiers.plafond_credit:,.0f} (dépassement de {depassement:,.0f}).").replace(",", " ")
        if tiers.code_risque == Tiers.RISQUE_BLOQUER and self.type_document not in self.TYPES_RISQUE_MESSAGE:
            raise ValidationError(f"Validation refusée. {message}")
        return message

    @transaction.atomic
    def valider(self):
        from apps.comptabilite.services import comptabiliser_document

        if self.statut != self.BROUILLON:
            raise ValidationError("Seul un document en brouillon peut être validé.")
        if not self.lignes.exists():
            raise ValidationError("Le document ne contient aucune ligne.")
        self.clean()
        self.controler_gros_detail()
        for ligne in self.lignes.all():
            ligne.save()            # réapplique le régime de TVA en vigueur à la validation
        self.recalculer(save=False)
        self.avertissement = self.controler_encours()
        if self.est_brouillon_numero:
            self.numero = Sequence.suivant(self.PREFIXES[self.type_document], self.date.year)
        from apps.core.journal import _utilisateur

        self.statut = self.VALIDE
        self.valide_par, self.valide_le = _utilisateur(), timezone.now()
        self.save()
        if self.mouvemente_stock:
            self._mouvementer_stock()
        if self.est_facturation:
            comptabiliser_document(self)
            self.imputer_acomptes()
        if self.origine_id:
            self.origine.mettre_a_jour_statut()
        self.facture_auto = self._facturer_livraison()
        return self

    TYPES_CONTROLE_DETAIL = (DEVIS, COMMANDE, PREPARATION, LIVRAISON, RETOUR, FACTURE, FACTURE_RETOUR)

    def controler_gros_detail(self):
        """Société qui réserve le détail à des dépôts désignés : hors de ces boutiques, on ne vend que par unités
        entières de l'article (pas de carton ouvert, pour ne pas « brûler » le stock du magasin de gros)."""
        from apps.core.models import Societe

        if self.type_document not in self.TYPES_CONTROLE_DETAIL or not self.depot_id or self.depot.vente_detail:
            return
        if not Societe.get().separation_gros_detail:
            return
        # Détail = quantité fractionnée, ou article de détail (bouteille issue de la conversion d'un carton)
        fractions = [l for l in self.lignes.select_related("article")
                     if l.article_id and l.article.suivi_stock
                     and (l.quantite != l.quantite.to_integral_value() or l.article.articles_gros.exists())]
        if fractions:
            boutiques = ", ".join(d.intitule for d in Depot.objects.filter(vente_detail=True, actif=True)) or "aucun dépôt désigné"
            raise ValidationError(
                f"Vente au détail impossible dans le dépôt « {self.depot.intitule} » (magasin de gros) : "
                f"{', '.join(f'{l.article.reference} ({l.quantite.normalize():f})' for l in fractions)}. "
                f"Vendez par unités entières, ou transférez la marchandise vers un dépôt de détail ({boutiques}).")

    def _facturer_livraison(self):
        """Livraison validée par le magasin (issue d'un bon de commande) : facture des quantités livrées, le jour même.

        Si la facture ne peut pas être validée (plafond d'encours bloquant…), elle reste en brouillon : la livraison,
        qui a eu lieu physiquement, reste validée."""
        from apps.core.models import Societe

        option = Societe.get().facturation_auto_livraison
        if (self.type_document != self.LIVRAISON or option == Societe.FACTURATION_AUCUNE
                or not self._chaine_contient((self.COMMANDE,))):
            return None
        facture = self.transformer(self.FACTURE)
        if option == Societe.FACTURATION_VALIDEE:
            try:
                with transaction.atomic():
                    facture.valider()
            except ValidationError as exc:
                facture.refresh_from_db()
                self.avertissement = " ".join(filter(None, [getattr(self, "avertissement", None),
                                                            f"Facture {facture.numero} laissée en brouillon : {' '.join(exc.messages)}"]))
        return facture

    def mettre_a_jour_statut(self):
        """Transformé quand toutes les lignes ont été reprises ; sinon reste validé (reliquat)."""
        if self.statut not in (self.VALIDE, self.TRANSFORME):
            return
        complet = all(l.reste_a_transformer <= 0 for l in self.lignes.all())
        statut = self.TRANSFORME if complet else self.VALIDE
        if statut != self.statut:
            self.statut = statut
            self.save(update_fields=["statut"])

    def _mouvementer_stock(self):
        from apps.core.models import Societe

        libelle = f"{self.get_type_document_display()} {self.numero}"
        lignes = [l for l in self.lignes.select_related("article") if l.article_id and l.article.suivi_stock]
        mouvements = []  # (article, depot, quantité signée, coût unitaire)
        conversions = {}  # article de détail → entrée à valoriser (CMUP) et libellé de la conversion
        for ligne in lignes:
            article = Article.objects.select_for_update().get(pk=ligne.article_id)
            if self.est_virement and self.depot_destination.vente_detail and article.article_detail_id:
                # Vers une boutique : le gros (carton) sort, le détail (bouteilles) entre ; valeur conservée
                detail = Article.objects.select_for_update().get(pk=article.article_detail_id)
                quantite_detail = ligne.quantite * article.facteur_detail
                cout_detail = (article.cout_unitaire / article.facteur_detail).quantize(Decimal("0.0001"))
                mouvements.append((article, self.depot, -ligne.quantite, article.cout_unitaire))
                mouvements.append((detail, self.depot_destination, quantite_detail, cout_detail))
                conversions[(detail.pk, self.depot_destination.pk)] = (
                    f"{ligne.quantite.normalize():f} {article.unite} {article.designation} → "
                    f"{quantite_detail.normalize():f} {detail.unite} {detail.designation}")
            elif self.est_virement:
                mouvements.append((article, self.depot, -ligne.quantite, article.cout_unitaire))
                mouvements.append((article, self.depot_destination, ligne.quantite, article.cout_unitaire))
            elif self.type_document in self.TYPES_ENTREE:
                cout = ligne.cout_entree if self.type_document in self.TYPES_ENTREE_VALORISEE else article.cout_unitaire
                mouvements.append((article, self.depot, ligne.quantite, cout))
            else:
                mouvements.append((article, self.depot, -ligne.quantite, article.cout_unitaire))

        if not Societe.get().stock_negatif_autorise:
            besoins = {}
            for article, depot, quantite, _ in mouvements:
                if quantite < 0:
                    cle = (article.pk, depot.pk)
                    besoins[cle] = besoins.get(cle, ZERO) - quantite
            for (article_pk, depot_pk), besoin in besoins.items():
                stock = StockDepot.quantite_de(article_pk, depot_pk)
                if stock < besoin:
                    article = Article.objects.get(pk=article_pk)
                    depot = Depot.objects.get(pk=depot_pk)
                    raise ValidationError(
                        f"Stock insuffisant pour « {article.designation} » dans le dépôt {depot} : "
                        f"disponible {stock.normalize():f}, demandé {besoin.normalize():f}.")

        for article, depot, quantite, cout in mouvements:
            conversion = conversions.get((article.pk, depot.pk)) if quantite > 0 else None
            if quantite > 0 and (self.type_document in self.TYPES_ENTREE_VALORISEE or conversion):
                article.recalculer_cmup(quantite, cout)
            MouvementStock.objects.create(article=article, depot=depot, date=self.date, quantite=quantite,
                                          cout_unitaire=cout, document=self,
                                          libelle=f"{libelle} (conversion {conversion})"[:200] if conversion else libelle)
            StockDepot.ajouter(article, depot, quantite)

    @transaction.atomic
    def transformer(self, type_cible, utilisateur=None):
        if type_cible not in self.TRANSFORMATIONS.get(self.type_document, ()):
            raise ValidationError("Transformation non autorisée pour ce document.")
        if self.statut != self.VALIDE:
            raise ValidationError("Seul un document validé et non entièrement transformé peut être transformé.")
        lignes = [l for l in self.lignes.all() if l.reste_a_transformer > 0]
        if not lignes:
            raise ValidationError("Toutes les lignes de ce document ont déjà été transformées.")
        nouveau = Document.objects.create(
            type_document=type_cible, tiers=self.tiers, payeur=self.payeur, origine=self, date=timezone.localdate(), depot=self.depot,
            reference_externe=self.reference_externe, notes=self.notes, cree_par=utilisateur,
        )
        for ligne in lignes:
            reste = ligne.reste_a_transformer
            ligne_origine = ligne.pk
            ligne.pk = None
            ligne.document = nouveau
            ligne.quantite = reste
            ligne.ligne_origine_id = ligne_origine
            ligne.save()
        nouveau.recalculer()
        return nouveau

    def _marquer_annule(self):
        from apps.core.journal import _utilisateur

        self.statut = self.ANNULE
        self.annule_par, self.annule_le = _utilisateur(), timezone.now()
        self.save(update_fields=["statut", "annule_par", "annule_le"])

    @transaction.atomic
    def annuler(self):
        if self.statut == self.BROUILLON:
            self._marquer_annule()
            return
        if self.est_facturation:
            raise ValidationError("Une facture validée ne s'annule pas : établissez une facture d'avoir.")
        if self.documents_generes.exclude(statut__in=(self.BROUILLON, self.ANNULE)).exists():
            raise ValidationError("Ce document a déjà été transformé : annulez d'abord les documents qui en sont issus.")
        if self.statut == self.VALIDE:
            from apps.core.models import Societe

            if not Societe.get().stock_negatif_autorise:
                # Annuler ne doit pas rendre un stock négatif (ex. bouteilles d'un transfert déjà vendues en boutique)
                for mvt in self.mouvements_stock.filter(quantite__gt=0).select_related("article", "depot"):
                    disponible = StockDepot.quantite_de(mvt.article_id, mvt.depot_id)
                    if disponible < mvt.quantite:
                        raise ValidationError(
                            f"Annulation impossible : « {mvt.article.designation} » n'a plus que {disponible.normalize():f} "
                            f"en stock dans le dépôt {mvt.depot} (le document en avait fait entrer {mvt.quantite.normalize():f}).")
            for mvt in self.mouvements_stock.select_related("article", "depot"):
                StockDepot.ajouter(mvt.article, mvt.depot, -mvt.quantite)
            self.mouvements_stock.all().delete()
        self._marquer_annule()
        if self.origine_id:
            self.origine.mettre_a_jour_statut()


class LigneDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, null=True, blank=True, on_delete=models.PROTECT)
    designation = models.CharField(max_length=200, blank=True)
    quantite = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("1"))
    prix_unitaire = models.DecimalField("P.U. HT", max_digits=18, decimal_places=2, default=ZERO)
    remise = models.DecimalField("Remise (%)", max_digits=5, decimal_places=2, default=ZERO)
    taux_tva = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, null=True, blank=True, default=None,
                                   help_text="Vide : taux de l'article (ou de la société pour une ligne libre)")
    montant_ht = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    montant_tva = models.DecimalField(max_digits=18, decimal_places=2, default=ZERO)
    ligne_origine = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="lignes_generees")

    class Meta:
        ordering = ["id"]
        verbose_name = "Ligne de document"

    def __str__(self):
        return self.designation

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva

    @property
    def prix_net(self):
        """Prix unitaire HT après remise."""
        return (self.montant_ht / self.quantite) if self.quantite else self.prix_unitaire

    @property
    def cout_entree(self):
        """Coût unitaire d'entrée en stock : HT, ou TTC si la société ne récupère pas la TVA."""
        if self.document.est_stock or Societe.get().assujettie_tva or not self.quantite:
            return self.prix_net
        return (self.montant_ht + self.montant_tva) / self.quantite

    @property
    def quantite_transformee(self):
        return self.lignes_generees.filter(
            document__statut__in=(Document.VALIDE, Document.TRANSFORME)).aggregate(s=Sum("quantite"))["s"] or ZERO

    @property
    def reste_a_transformer(self):
        return self.quantite - self.quantite_transformee

    def calculer(self):
        if self.taux_tva is None:                  # non saisi : taux de l'article, sinon celui de la société
            self.taux_tva = self.article.taux_tva if self.article_id else taux_tva_defaut()
        brut = Decimal(self.quantite) * Decimal(self.prix_unitaire)
        self.montant_ht = arrondi(brut * (1 - Decimal(self.remise) / 100))
        self.montant_tva = arrondi(self.montant_ht * Decimal(self.taux_tva) / 100)

    def save(self, *args, **kwargs):
        if self.article_id and not self.designation:
            self.designation = self.article.designation
        if self.taux_tva is None:
            self.taux_tva = self.article.taux_tva if self.article_id else taux_tva_defaut()
        if self.document_id:
            doc = self.document
            if doc.est_stock:
                # Documents des stocks : valorisés au coût, sans TVA
                self.taux_tva = ZERO
                self.remise = ZERO
                if not self.prix_unitaire and self.article_id:
                    self.prix_unitaire = arrondi(self.article.cout_unitaire, 2)
            elif doc.est_vente and not Societe.get().assujettie_tva:
                self.taux_tva = ZERO        # société non assujettie : elle ne facture pas de TVA
            elif doc.tiers_id and not doc.tiers.assujetti_tva:
                self.taux_tva = ZERO        # client exonéré ou fournisseur non assujetti
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
    commande = models.ForeignKey(
        "Document", null=True, blank=True, on_delete=models.PROTECT, related_name="acomptes",
        verbose_name="Acompte sur commande",
        help_text="Bon de commande payé d'avance : l'acompte sera imputé sur la facture issue de cette commande")
    facture = models.ForeignKey(
        "Document", null=True, blank=True, on_delete=models.PROTECT, related_name="recus",
        verbose_name="Facture réglée", help_text="Obligatoire pour un reçu de règlement de créance client")
    agence_encaissement = models.ForeignKey(
        "core.Agence", null=True, blank=True, on_delete=models.PROTECT, related_name="reglements_encaisses",
        verbose_name="Encaissé par l'agence",
        help_text="Versement reçu par une autre agence pour ce client (hors recettes chez elle) : sans mouvement de caisse ici, "
                  "passé par son compte de liaison")
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="reglement")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                 verbose_name="Créé par")
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

    MODES_HORS_ESPECES = (VIREMENT, MOBILE_MONEY)

    def controler_mode_journal(self):
        """Un virement ou un paiement Mobile Money n'entre pas dans une caisse d'espèces (compte 57)."""
        from apps.comptabilite.models import Journal

        compte = self.journal.compte_tresorerie if self.journal_id else None
        if self.mode in self.MODES_HORS_ESPECES and compte and compte.numero.startswith("57"):
            autre = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False).exclude(
                compte_tresorerie__numero__startswith="57")
            conseil = ", ".join(f"{j.code} - {j.intitule}" for j in autre[:3])
            raise ValidationError({"journal": f"Un règlement « {self.get_mode_display()} » ne peut pas entrer dans la caisse "
                                              f"espèces {self.journal.code}. Choisissez le journal correspondant"
                                              f"{' (' + conseil + ')' if conseil else ''}."})

    def _controler_facture(self, f):
        if not f.est_facturation or f.est_avoir or f.statut != Document.VALIDE:
            raise ValidationError({"factures": f"{f.numero} : choisissez une facture validée (pas un avoir)."})
        if self.tiers_id not in (f.tiers_id, f.tiers_payeur.pk):
            raise ValidationError({"factures": f"La facture {f.numero} n'est pas celle de {self.tiers.nom}."})
        if f.reste_a_payer <= 0:
            raise ValidationError({"factures": f"La facture {f.numero} est déjà soldée."})

    def controler_rattachement(self, factures=None, en_attente=False):
        """Reçu de règlement de créance client : rattaché à une ou plusieurs factures du client, réglées dans l'ordre
        (de la plus ancienne à la plus récente), totalement ou partiellement. Le reste éventuel du reçu reste en attente
        de rattachement à une prochaine facture. L'avance sur bon de commande suit son propre circuit."""
        cibles = list(factures) if factures is not None else ([self.facture] if self.facture_id else [])
        self.controler_mode_journal()
        if self.commande_id:
            if cibles and self.est_encaissement:
                raise ValidationError("Choisissez soit des factures (règlement de créance), soit un bon de commande (avance).")
            self._cibles = None
            return
        if self.est_encaissement and not cibles and not en_attente:
            raise ValidationError({"factures": "Un reçu de règlement de créance doit être rattaché à au moins une facture "
                                               "(ou enregistré « en attente de facture »)."})
        if len({f.pk for f in cibles}) != len(cibles):
            raise ValidationError({"factures": "Une même facture est choisie deux fois."})
        for f in cibles:
            self._controler_facture(f)
        cibles.sort(key=lambda f: (f.date, f.numero))
        if cibles:
            self.facture = cibles[0]                          # première facture réglée (affichage, listes)
        self._cibles = cibles or ([] if en_attente else None)     # [] : tout le reçu attend une facture
        if self.agence_encaissement_id:
            if self.agence_encaissement.locale:
                raise ValidationError({"agence_encaissement": "Choisissez l'agence qui a reçu le versement (pas celle-ci)."})
            if not self.reference:
                raise ValidationError({"reference": "Indiquez le n° du reçu établi par l'agence qui a encaissé."})
            doublon = Reglement.objects.filter(agence_encaissement=self.agence_encaissement, reference=self.reference)
            if doublon.exclude(pk=self.pk).exists():
                raise ValidationError({"reference": f"Le reçu {self.reference} de {self.agence_encaissement.nom} est déjà enregistré."})

    @transaction.atomic
    def enregistrer(self, factures=None, montants=None, en_attente=False):
        """Numérote, comptabilise et impute le règlement : sur les factures choisies (reçu client), sur la facture issue
        de la commande (avance), ou en FIFO (fournisseur sans facture désignée). Le reste non imputé reste en attente.

        montants : {facture_id: montant} saisis ligne par ligne ; à défaut, répartition de la plus ancienne à la plus
        récente. en_attente : reçu enregistré sans facture, entièrement en attente de rattachement."""
        from apps.comptabilite.services import comptabiliser_reglement

        self.controler_rattachement(factures, en_attente=en_attente)
        montants = {int(k): Decimal(v) for k, v in (montants or {}).items() if v not in (None, "")}
        if montants:
            for f in self._cibles or []:
                m = montants.get(f.pk)
                if m is not None and (m <= 0 or m > f.reste_a_payer):
                    raise ValidationError({"factures": f"{f.numero} : montant imputé incorrect (entre 0 et le reste dû "
                                                       f"{f.reste_a_payer:,.0f}).".replace(",", " ")})
            if sum((montants.get(f.pk, ZERO) for f in self._cibles or []), ZERO) > self.montant:
                raise ValidationError({"montant": "Le total imputé sur les factures dépasse le montant du règlement."})
        if self.commande_id:
            commande = self.commande
            if commande.type_document not in (Document.COMMANDE, Document.ACHAT_COMMANDE) or commande.statut == Document.ANNULE:
                raise ValidationError("Un acompte se rattache à un bon de commande non annulé.")
            if commande.tiers_payeur.pk != self.tiers_id and commande.tiers_id != self.tiers_id:
                raise ValidationError("Le tiers de l'acompte doit être celui du bon de commande (ou son payeur).")
        if not self.numero:
            prefixe = "RC" if self.est_encaissement else "RF"
            self.numero = Sequence.suivant(prefixe, self.date.year)
        self.save()
        comptabiliser_reglement(self)
        if self.commande_id:
            # Acompte : il attend la facture issue de la commande (imputé à sa validation)
            facture = self.commande.facture_issue()
            cibles = [facture] if facture else []
        elif self._cibles is not None:
            cibles = self._cibles
        else:
            types = (Document.FACTURE,) if self.est_encaissement else (Document.ACHAT_FACTURE,)
            cibles = self.tiers.factures_a_regler().filter(type_document__in=types).order_by("date", "numero")
        disponible = self.montant_non_impute
        for facture in cibles:
            if disponible <= 0:
                break
            reste = facture.reste_a_payer
            if reste <= 0:
                continue
            montant = min(reste, disponible, montants.get(facture.pk, reste))
            Imputation.objects.create(reglement=self, document=facture, montant=montant)
            disponible -= montant
        return self

    @property
    def en_attente_de_rattachement(self):
        """Reste du reçu non encore affecté à une facture (hors avance sur commande, qui attend sa propre facture)."""
        return ZERO if self.commande_id else self.montant_non_impute

    @transaction.atomic
    def rattacher(self, facture, montant=None):
        """Rattache (tout ou partie de) le reste en attente du reçu à une nouvelle facture du client."""
        reste_recu = self.en_attente_de_rattachement
        if reste_recu <= 0:
            raise ValidationError("Ce reçu n'a plus de reste à rattacher.")
        self._controler_facture(facture)
        montant = min(reste_recu, facture.reste_a_payer) if montant is None else Decimal(montant)
        if montant <= 0 or montant > reste_recu or montant > facture.reste_a_payer:
            raise ValidationError(f"Montant incorrect : au plus {min(reste_recu, facture.reste_a_payer):,.0f}.".replace(",", " "))
        return Imputation.objects.create(reglement=self, document=facture, montant=montant)


class Imputation(models.Model):
    reglement = models.ForeignKey(Reglement, on_delete=models.CASCADE, related_name="imputations")
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="imputations")
    montant = models.DecimalField(max_digits=18, decimal_places=2)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                 verbose_name="Rattaché par")
    cree_le = models.DateTimeField("Rattaché le", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Imputation de règlement"


class OperationCaisse(models.Model):
    """Entrée ou sortie de caisse qui n'est pas un règlement de facture : dépense du jour, versement hors recettes
    (reçu pour le compte d'une autre agence), sortie faite pour le compte d'une autre agence, autre mouvement.
    Comptabilisée à l'enregistrement dans le journal de caisse choisi."""

    DEPENSE = "DEPENSE"
    HORS_RECETTE = "HORS_RECETTE"
    SORTIE_AGENCE = "SORTIE_AGENCE"
    AUTRE_ENTREE = "AUTRE_ENTREE"
    AUTRE_SORTIE = "AUTRE_SORTIE"
    NATURES = [
        (DEPENSE, "Dépense"),
        (HORS_RECETTE, "Versement hors recettes (pour une autre agence)"),
        (SORTIE_AGENCE, "Sortie pour le compte d'une autre agence"),
        (AUTRE_ENTREE, "Autre entrée de caisse"),
        (AUTRE_SORTIE, "Autre sortie de caisse"),
    ]
    ENTREES = (HORS_RECETTE, AUTRE_ENTREE)
    AVEC_AGENCE = (HORS_RECETTE, SORTIE_AGENCE)

    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    nature = models.CharField(max_length=15, choices=NATURES, default=DEPENSE)
    journal = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, limit_choices_to={"type_journal": "TRESORERIE"},
                                verbose_name="Caisse")
    montant = models.DecimalField(max_digits=18, decimal_places=2)
    libelle = models.CharField("Libellé", max_length=200)
    agence = models.ForeignKey("core.Agence", null=True, blank=True, on_delete=models.PROTECT, related_name="operations_caisse",
                               help_text="Agence pour le compte de laquelle l'opération est faite")
    tiers_libre = models.CharField("Client / bénéficiaire", max_length=150, blank=True,
                                   help_text="Ex. client de l'autre agence qui a versé (code et nom)")
    compte = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               verbose_name="Compte de contrepartie",
                               help_text="Compte de charge pour une dépense (ex. 6xx) ; inutile pour une opération d'agence")
    reference = models.CharField("Pièce justificative", max_length=60, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="operation_caisse")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Opération de caisse"
        verbose_name_plural = "Opérations de caisse"

    def __str__(self):
        return f"{self.numero} - {self.libelle}"

    @property
    def est_entree(self):
        return self.nature in self.ENTREES

    def clean(self):
        if self.montant is not None and self.montant <= 0:
            raise ValidationError({"montant": "Le montant doit être positif."})
        if self.nature in self.AVEC_AGENCE:
            if not self.agence_id:
                raise ValidationError({"agence": "Indiquez l'agence pour le compte de laquelle l'opération est faite."})
            if self.agence.locale:
                raise ValidationError({"agence": "Choisissez une autre agence que celle de ce dossier."})
        elif not self.compte_id:
            raise ValidationError({"compte": "Indiquez le compte de contrepartie (ex. compte de charge pour une dépense)."})

    def contrepartie(self):
        return self.agence.compte_liaison if self.nature in self.AVEC_AGENCE else self.compte

    @transaction.atomic
    def enregistrer(self):
        """Numérote et comptabilise : entrée D caisse / C contrepartie ; sortie D contrepartie / C caisse."""
        from apps.comptabilite.services import creer_ecriture

        self.full_clean(exclude=["numero", "ecriture"])
        if not self.journal.compte_tresorerie_id:
            raise ValidationError(f"Le journal {self.journal.code} n'a pas de compte de trésorerie associé.")
        if not self.numero:
            self.numero = Sequence.suivant("OC", self.date.year)
        self.save()
        if not self.ecriture_id:
            libelle = self.libelle + (f" - {self.tiers_libre}" if self.tiers_libre else "") + (f" ({self.agence.nom})" if self.agence_id else "")
            caisse, autre = self.journal.compte_tresorerie, self.contrepartie()
            lignes = ([{"compte": caisse, "debit": self.montant}, {"compte": autre, "credit": self.montant}] if self.est_entree
                      else [{"compte": autre, "debit": self.montant}, {"compte": caisse, "credit": self.montant}])
            self.ecriture = creer_ecriture(self.journal, self.date, libelle, lignes, reference=self.reference or self.numero,
                                           origine=self.numero)
            self.save(update_fields=["ecriture"])
        return self


class TarifCategorie(models.Model):
    """Prix de vente d'un article pour une catégorie tarifaire."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="tarifs")
    categorie = models.ForeignKey(CategorieTarifaire, on_delete=models.CASCADE, related_name="tarifs")
    prix_vente = models.DecimalField("Prix de vente HT", max_digits=18, decimal_places=2)

    class Meta:
        unique_together = ("article", "categorie")
        ordering = ["categorie__code"]
        verbose_name = "Tarif par catégorie"


class StockDepot(models.Model):
    """Quantité en stock d'un article dans un dépôt, et seuils de réapprovisionnement de ce dépôt."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="stocks_depots")
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="stocks")
    quantite = models.DecimalField(max_digits=18, decimal_places=3, default=ZERO)
    stock_mini = models.DecimalField("Stock mini", max_digits=18, decimal_places=3, default=ZERO)
    stock_maxi = models.DecimalField("Stock maxi", max_digits=18, decimal_places=3, default=ZERO)

    @property
    def besoin(self):
        """Quantité à commander pour revenir au maxi lorsque le stock est sous le mini."""
        if self.stock_mini and self.quantite < self.stock_mini:
            return max((self.stock_maxi or self.stock_mini) - self.quantite, ZERO)
        return ZERO

    class Meta:
        unique_together = ("article", "depot")
        ordering = ["depot__intitule"]
        verbose_name = "Stock par dépôt"

    @classmethod
    def quantite_de(cls, article_id, depot_id):
        return cls.objects.filter(article_id=article_id, depot_id=depot_id).values_list("quantite", flat=True).first() or ZERO

    @classmethod
    def ajouter(cls, article, depot, quantite):
        ligne, _ = cls.objects.select_for_update().get_or_create(article=article, depot=depot)
        cls.objects.filter(pk=ligne.pk).update(quantite=models.F("quantite") + quantite)
        Article.objects.filter(pk=article.pk).update(stock=models.F("stock") + quantite)


class MouvementStock(models.Model):
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name="mouvements")
    depot = models.ForeignKey(Depot, null=True, on_delete=models.PROTECT, related_name="mouvements")
    date = models.DateField()
    quantite = models.DecimalField(max_digits=18, decimal_places=3, help_text="Positif = entrée, négatif = sortie")
    cout_unitaire = models.DecimalField(max_digits=18, decimal_places=4, default=ZERO)
    document = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="mouvements_stock")
    libelle = models.CharField(max_length=200)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Mouvement de stock"

    @property
    def valeur(self):
        return arrondi(self.quantite * self.cout_unitaire)


class PointageFiche(models.Model):
    """Fiche de stock numérique : le fichiste du magasin pointe chaque bon (livraison, réception, transfert…) en
    saisissant lui-même les quantités lues sur le bon papier, sans voir celles de l'ordinateur. Le rapprochement
    avec les mouvements de stock enregistrés est immédiat (au lieu du contrôle hebdomadaire des fiches papier)."""

    CONFORME = "CONFORME"
    ECART = "ECART"
    STATUTS = [(CONFORME, "Conforme"), (ECART, "Écart")]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="pointages")
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="pointages")
    date = models.DateField("Date du pointage", default=timezone.localdate)
    statut = models.CharField(max_length=10, choices=STATUTS, default=CONFORME)
    fichiste = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    observation = models.CharField(max_length=200, blank=True)
    revision = models.PositiveIntegerField(default=1)
    historique = models.JSONField(default=list, blank=True,
                                  help_text="Déclarations précédentes du fichiste (corrections) : date, auteur, motif, quantités")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        unique_together = ("document", "depot")
        verbose_name = "Pointage de fiche de stock"

    def __str__(self):
        return f"{self.numero} - {self.document.numero}"

    @staticmethod
    def quantites_machine(document, depot):
        """{article: quantité} déplacée par le bon dans ce dépôt (valeur absolue), d'après les mouvements de stock."""
        quantites = {}
        for m in document.mouvements_stock.filter(depot=depot).select_related("article"):
            quantites[m.article] = quantites.get(m.article, ZERO) + abs(m.quantite)
        return quantites

    @staticmethod
    def sens(document, depot):
        """+1 si le bon fait entrer la marchandise dans ce dépôt, -1 s'il la fait sortir."""
        total = document.mouvements_stock.filter(depot=depot).aggregate(s=Sum("quantite"))["s"] or ZERO
        return 1 if total >= 0 else -1

    @classmethod
    def controler_saisies(cls, articles, saisies):
        """Chaque article du bon doit être déclaré : vide ≠ 0 (le zéro doit être saisi), jamais négatif."""
        manquants = [a.reference for a in articles if saisies.get(a.pk) is None]
        if manquants:
            raise ValidationError(f"Quantité non saisie pour : {', '.join(manquants)}. "
                                  "Saisissez 0 si l'article n'est pas sorti.")
        for a in articles:
            q = saisies[a.pk]
            if not q.is_finite() or q < 0 or q != q.quantize(Decimal("0.001")):
                raise ValidationError(f"Quantité incorrecte pour {a.reference} : un nombre positif ou nul "
                                      "(3 décimales au plus).")

    @transaction.atomic
    def enregistrer(self, saisies, fichiste=None):
        """saisies : {article_id: quantité lue sur le bon}. Calcule les écarts ligne par ligne.
        fichiste : l'auteur de cette déclaration ; l'auteur de la déclaration remplacée reste dans l'historique."""
        machine = self.quantites_machine(self.document, self.depot)
        self.controler_saisies(machine, saisies)
        if not self.numero:
            self.numero = Sequence.suivant("PF", self.date.year)
        if self.pk and self.lignes.exists():
            if not (self.observation or "").strip():
                raise ValidationError("Bon déjà pointé : indiquez le motif de la correction.")
            precedent = PointageFiche.objects.select_related("fichiste").get(pk=self.pk)   # état enregistré, avant correction
            # Correction : la déclaration précédente est conservée, avec SON auteur ; le correcteur et le motif à part
            self.historique = self.historique + [{
                "revision": precedent.revision, "date": timezone.now().isoformat(timespec="seconds"),
                "fichiste": str(precedent.fichiste or ""), "statut": precedent.statut,
                "corrige_par": str(fichiste or self.fichiste or ""), "motif": self.observation,
                "quantites": {l.article.reference: str(l.quantite_saisie) for l in self.lignes.select_related("article")}}]
            self.revision = precedent.revision + 1
        if fichiste is not None:
            self.fichiste = fichiste
        self.save()
        self.lignes.all().delete()
        ecart = False
        for article, quantite in machine.items():
            saisie = saisies[article.pk]
            LignePointage.objects.create(pointage=self, article=article, quantite_saisie=saisie, quantite_document=quantite)
            ecart = ecart or saisie != quantite
        self.statut = self.ECART if ecart else self.CONFORME
        self.save(update_fields=["statut"])
        return self


class LignePointage(models.Model):
    pointage = models.ForeignKey(PointageFiche, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    quantite_saisie = models.DecimalField("Quantité du fichiste", max_digits=18, decimal_places=3)
    quantite_document = models.DecimalField("Quantité enregistrée", max_digits=18, decimal_places=3)

    class Meta:
        ordering = ["article__reference"]

    @property
    def ecart(self):
        return self.quantite_saisie - self.quantite_document


class Inventaire(models.Model):
    """Saisie d'inventaire physique d'un dépôt : les écarts génèrent des mouvements d'entrée / de sortie."""

    BROUILLON = "BROUILLON"
    VALIDE = "VALIDE"
    STATUTS = [(BROUILLON, "En cours de saisie"), (VALIDE, "Validé")]

    numero = models.CharField(max_length=30, unique=True)
    date = models.DateField(default=timezone.localdate)
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="inventaires")
    famille = models.ForeignKey(FamilleArticle, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Limiter l'inventaire à une famille (facultatif)")
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    notes = models.TextField(blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    mouvement_entree = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    mouvement_sortie = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-numero"]

    def __str__(self):
        return f"{self.numero} - {self.depot}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = Sequence.suivant("INV", self.date.year)
        super().save(*args, **kwargs)

    def initialiser_lignes(self):
        articles = Article.objects.filter(suivi_stock=True, actif=True)
        if self.famille_id:
            articles = articles.filter(famille=self.famille)
        LigneInventaire.objects.bulk_create([
            LigneInventaire(inventaire=self, article=a, stock_theorique=a.stock_depot(self.depot),
                            stock_reel=a.stock_depot(self.depot), cout_unitaire=a.cout_unitaire)
            for a in articles
        ])

    @property
    def ecart_valeur(self):
        return sum((l.ecart_valeur for l in self.lignes.all()), ZERO)

    @transaction.atomic
    def valider(self):
        if self.statut != self.BROUILLON:
            raise ValidationError("Cet inventaire est déjà validé.")
        entrees, sorties = [], []
        for ligne in self.lignes.select_related("article"):
            # Écart calculé sur le stock au moment de la validation
            theorique = ligne.article.stock_depot(self.depot)
            ecart = ligne.stock_reel - theorique
            if ecart > 0:
                entrees.append((ligne.article, ecart))
            elif ecart < 0:
                sorties.append((ligne.article, -ecart))
        for type_document, lignes, champ in ((Document.STOCK_ENTREE, entrees, "mouvement_entree"),
                                             (Document.STOCK_SORTIE, sorties, "mouvement_sortie")):
            if not lignes:
                continue
            doc = Document.objects.create(type_document=type_document, depot=self.depot, date=self.date,
                                          reference_externe=self.numero, notes=f"Régularisation d'inventaire {self.numero}")
            for article, quantite in lignes:
                LigneDocument.objects.create(document=doc, article=article, quantite=quantite,
                                             prix_unitaire=arrondi(article.cout_unitaire, 2))
            doc.recalculer()
            doc.valider()
            setattr(self, champ, doc)
        self.statut = self.VALIDE
        self.save()


class LigneInventaire(models.Model):
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    stock_theorique = models.DecimalField(max_digits=18, decimal_places=3, default=ZERO)
    stock_reel = models.DecimalField("Stock compté", max_digits=18, decimal_places=3, default=ZERO)
    cout_unitaire = models.DecimalField(max_digits=18, decimal_places=4, default=ZERO)

    class Meta:
        ordering = ["article__reference"]

    @property
    def ecart(self):
        return self.stock_reel - self.stock_theorique

    @property
    def ecart_valeur(self):
        return arrondi(self.ecart * self.cout_unitaire)
