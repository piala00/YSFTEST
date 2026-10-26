"""Magasin : pièces, pneus, lubrifiants, fournitures de bureau, emballages (carton, ruban adhésif).

À l'achat, chaque ligne dit sa destination :
  - STOCK         : l'article entre au magasin (actif)          D 33x stock / C 401 fournisseur ou caisse
                    à l'utilisation, une sortie le fait passer en charge (au coût moyen pondéré) :
                                                                 D charge (sur le véhicule s'il y en a un) / C 33x stock
  - VEHICULE      : acheté pour un véhicule précis               D charge sur ce véhicule / C 401 ou caisse
  - IMMOBILISATION: matériel durable (imprimante, outillage)     D compte d'immobilisation (classe 2) / C 401 ou caisse
Un achat n'est donc jamais une charge tant qu'il est en stock ; une sortie n'est jamais un second achat.
Comptes proposés par catégorie, modifiables par article : à valider par l'expert-comptable.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _compte(numero, intitule):
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]


def _arrondi(v):
    return Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


class ArticleMagasin(models.Model):
    PIECE, PNEU, LUBRIFIANT, BUREAU, EMBALLAGE, AUTRE = "PIECE", "PNEU", "LUBRIFIANT", "BUREAU", "EMBALLAGE", "AUTRE"
    CATEGORIES = [(PIECE, "Pièce de rechange"), (PNEU, "Pneu"), (LUBRIFIANT, "Huile, lubrifiant"),
                  (BUREAU, "Fourniture de bureau"), (EMBALLAGE, "Emballage (carton, ruban adhésif, sac)"),
                  (AUTRE, "Autre fourniture")]
    STOCKS = {PIECE: ("338", "Autres approvisionnements (pièces, pneus, lubrifiants)"),
              PNEU: ("338", "Autres approvisionnements (pièces, pneus, lubrifiants)"),
              LUBRIFIANT: ("338", "Autres approvisionnements (pièces, pneus, lubrifiants)"),
              BUREAU: ("334", "Fournitures de bureau"), EMBALLAGE: ("335", "Emballages"),
              AUTRE: ("331", "Matières consommables")}
    CHARGES = {BUREAU: ("6047", "Fournitures de bureau"), EMBALLAGE: ("608", "Achats d'emballages"),
               AUTRE: ("6041", "Matières consommables")}            # pièces, pneus, lubrifiants : compte « pièces »

    code = models.CharField(max_length=30, unique=True)
    designation = models.CharField("Désignation", max_length=150)
    categorie = models.CharField("Catégorie", max_length=12, choices=CATEGORIES, default=PIECE)
    unite = models.CharField("Unité", max_length=20, default="pièce")
    compte_stock = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                     verbose_name="Compte de stock", help_text="Vide : proposé selon la catégorie")
    compte_charge = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                      verbose_name="Compte de charge à l'utilisation", help_text="Vide : proposé selon la catégorie")
    quantite = models.DecimalField("En stock", max_digits=14, decimal_places=2, default=ZERO, editable=False)
    cout_moyen = models.DecimalField("Coût moyen pondéré", max_digits=14, decimal_places=2, default=ZERO, editable=False)
    seuil = models.DecimalField("Stock d'alerte", max_digits=14, decimal_places=2, default=ZERO)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["categorie", "designation"]
        verbose_name = "Article du magasin"

    def __str__(self):
        return f"{self.code} - {self.designation}"

    def save(self, *args, **kwargs):
        from apps.transport.models import ParametresTransport

        if not self.compte_stock_id:
            self.compte_stock = _compte(*self.STOCKS[self.categorie])
        if not self.compte_charge_id:
            self.compte_charge = (_compte(*self.CHARGES[self.categorie]) if self.categorie in self.CHARGES
                                  else ParametresTransport.get().compte_pieces)
        super().save(*args, **kwargs)

    @property
    def valeur(self):
        return _arrondi(self.quantite * self.cout_moyen)

    @property
    def en_alerte(self):
        return self.seuil and self.quantite <= self.seuil


class AchatMagasin(models.Model):
    """Facture d'achat du magasin (pièces, fournitures, matériel), payée en caisse ou due au fournisseur."""

    BROUILLON, VALIDE = "BROUILLON", "VALIDE"
    STATUTS = [(BROUILLON, "En préparation"), (VALIDE, "Validé (comptabilisé)")]
    ESPECES, COMPTE = "ESPECES", "COMPTE"
    PAIEMENTS = [(ESPECES, "Payé en caisse"), (COMPTE, "En compte fournisseur (à payer)")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    fournisseur = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    facture = models.CharField("N° de facture du fournisseur", max_length=60, blank=True)
    paiement = models.CharField(max_length=10, choices=PAIEMENTS, default=COMPTE)
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    statut = models.CharField(max_length=10, choices=STATUTS, default=BROUILLON)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Achat du magasin"

    def __str__(self):
        return f"{self.numero} {self.fournisseur or ''}"

    def save(self, *args, **kwargs):
        self.numero = self.numero or Sequence.piece("ACM", self.date.year)
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum((l.montant for l in self.lignes.all()), ZERO)

    @transaction.atomic
    def valider(self, utilisateur=None):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.BROUILLON:
            raise ValidationError("Cet achat est déjà validé.")
        lignes = list(self.lignes.select_related("article", "vehicule", "compte"))
        if not lignes:
            raise ValidationError("Ajoutez les lignes de l'achat.")
        if self.paiement == self.COMPTE:
            if self.fournisseur is None:
                raise ValidationError("Choisissez le fournisseur (achat en compte).")
            journal, contrepartie = Journal.objects.get(code="AC"), {"compte": self.fournisseur.get_compte_collectif(),
                                                                      "tiers": self.fournisseur}
        else:
            if self.caisse is None or not self.caisse.compte_tresorerie_id:
                raise ValidationError("Choisissez la caisse qui paie.")
            journal, contrepartie = self.caisse, {"compte": self.caisse.compte_tresorerie}
        debits = []
        for l in lignes:
            l.controler()
            if l.destination == LigneAchatMagasin.STOCK:
                debits.append({"compte": l.article.compte_stock, "debit": l.montant, "libelle": f"Entrée {l.article.designation}"})
                a = ArticleMagasin.objects.select_for_update().get(pk=l.article_id)
                total = a.quantite + l.quantite                        # coût moyen pondéré
                a.cout_moyen = ((a.quantite * a.cout_moyen + l.montant) / total) if total > 0 else l.prix_unitaire
                a.quantite = total
                a.save(update_fields=["quantite", "cout_moyen"])
                MouvementMagasin.objects.create(article=a, date=self.date, sens=MouvementMagasin.ENTREE, quantite=l.quantite,
                                                cout_unitaire=l.prix_unitaire, montant=l.montant, achat=self,
                                                motif=f"Achat {self.numero}")
            elif l.destination == LigneAchatMagasin.VEHICULE:
                compte = l.compte or (l.article.compte_charge if l.article_id else _charge_pieces())
                debits.append({"compte": compte, "debit": l.montant, "vehicule": l.vehicule, "section": l.vehicule.section,
                               "libelle": f"{l.libelle()} pour {l.vehicule.immatriculation}"})
            else:
                debits.append({"compte": l.compte or _compte("244", "Matériel et mobilier"), "debit": l.montant,
                               "libelle": f"Immobilisation {l.libelle()}"})
        total = sum((d["debit"] for d in debits), ZERO)
        self.ecriture = creer_ecriture(journal, self.date, f"Achat {self.numero} {self.fournisseur or ''} {self.facture}".strip()[:200],
                                       debits + [{**contrepartie, "credit": total}], reference=self.facture or self.numero,
                                       origine=self.numero)
        self.statut, self.cree_par = self.VALIDE, self.cree_par or utilisateur
        self.save(update_fields=["ecriture", "statut", "cree_par"])
        return self


def _charge_pieces():
    from apps.transport.models import ParametresTransport

    return ParametresTransport.get().compte_pieces


class LigneAchatMagasin(models.Model):
    STOCK, VEHICULE, IMMOBILISATION = "STOCK", "VEHICULE", "IMMOBILISATION"
    DESTINATIONS = [(STOCK, "Pour le stock du magasin"), (VEHICULE, "Pour un véhicule précis (charge directe)"),
                    (IMMOBILISATION, "Matériel durable (immobilisation)")]

    achat = models.ForeignKey(AchatMagasin, on_delete=models.CASCADE, related_name="lignes")
    destination = models.CharField(max_length=15, choices=DESTINATIONS, default=STOCK)
    article = models.ForeignKey(ArticleMagasin, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    designation = models.CharField("Désignation", max_length=150, blank=True, help_text="Sans article : matériel, pièce unique…")
    quantite = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("1"))
    prix_unitaire = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO)
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    compte = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               help_text="Immobilisation : compte de classe 2 ; achat direct : compte de charge (vide : celui de l'article)")

    class Meta:
        ordering = ["pk"]

    @property
    def montant(self):
        return _arrondi(Decimal(self.quantite) * Decimal(self.prix_unitaire))

    def libelle(self):
        return self.article.designation if self.article_id else self.designation

    def controler(self):
        if self.quantite <= 0 or self.prix_unitaire < 0:
            raise ValidationError("Quantité et prix doivent être positifs.")
        if self.destination == self.STOCK and not self.article_id:
            raise ValidationError("Une entrée en stock porte sur un article du magasin.")
        if self.destination == self.VEHICULE and not self.vehicule_id:
            raise ValidationError(f"{self.libelle()} : choisissez le véhicule.")
        if self.destination == self.IMMOBILISATION and self.compte_id and not self.compte.numero.startswith("2"):
            raise ValidationError("Une immobilisation va sur un compte de classe 2.")
        if not self.libelle():
            raise ValidationError("Indiquez l'article ou la désignation.")


class MouvementMagasin(models.Model):
    ENTREE, SORTIE = "ENTREE", "SORTIE"
    SENS = [(ENTREE, "Entrée"), (SORTIE, "Sortie")]

    article = models.ForeignKey(ArticleMagasin, on_delete=models.PROTECT, related_name="mouvements")
    date = models.DateField(default=timezone.localdate)
    sens = models.CharField(max_length=6, choices=SENS)
    quantite = models.DecimalField(max_digits=14, decimal_places=2)
    cout_unitaire = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO)
    montant = models.DecimalField(max_digits=14, decimal_places=0, default=ZERO)
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    ordre = models.ForeignKey("garage.OrdreReparation", null=True, blank=True, on_delete=models.PROTECT, related_name="sorties")
    achat = models.ForeignKey(AchatMagasin, null=True, blank=True, on_delete=models.PROTECT, related_name="mouvements")
    motif = models.CharField(max_length=150, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-pk"]
        verbose_name = "Mouvement du magasin"


@transaction.atomic
def sortir(article, quantite, vehicule=None, motif="", date=None, ordre=None, utilisateur=None):
    """Utilisation d'un article du stock : il passe en charge (sur le véhicule s'il y en a un) au coût moyen."""
    from apps.comptabilite.models import Journal
    from apps.comptabilite.services import creer_ecriture

    quantite = Decimal(quantite)
    if quantite <= 0:
        raise ValidationError("La quantité doit être positive.")
    a = ArticleMagasin.objects.select_for_update().get(pk=article.pk)
    if quantite > a.quantite:
        raise ValidationError(f"{a.designation} : {a.quantite.normalize()} en stock, sortie de {quantite.normalize()} impossible.")
    montant = _arrondi(quantite * a.cout_moyen)
    date = date or timezone.localdate()
    m = MouvementMagasin.objects.create(article=a, date=date, sens=MouvementMagasin.SORTIE, quantite=quantite,
                                        cout_unitaire=a.cout_moyen, montant=montant, vehicule=vehicule, ordre=ordre,
                                        motif=motif or (f"Réparation {ordre.numero}" if ordre else ""), cree_par=utilisateur)
    if montant:
        charge = {"compte": a.compte_charge, "debit": montant}
        if vehicule is not None:
            charge.update(vehicule=vehicule, section=vehicule.section)
        m.ecriture = creer_ecriture(Journal.objects.get(code="OD"), date,
                                    f"Sortie magasin {a.designation} x{quantite.normalize()}"
                                    + (f" pour {vehicule.immatriculation}" if vehicule else ""),
                                    [charge, {"compte": a.compte_stock, "credit": montant}],
                                    reference=ordre.numero if ordre else f"SM{m.pk}", origine=ordre.numero if ordre else "")
        m.save(update_fields=["ecriture"])
    a.quantite -= quantite
    a.save(update_fields=["quantite"])
    return m
