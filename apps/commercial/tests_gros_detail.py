"""Vente au détail réservée à des dépôts désignés (boutiques) : les magasins de gros ne vendent que par unités entières."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Depot, Document, LigneDocument, StockDepot, Tiers
from apps.core.models import Societe


class GrosDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="manuelle")
        cls.magasin = Depot.par_defaut()
        cls.boutique = Depot.objects.create(code="BOUT", intitule="Boutique centre-ville")
        cls.huile = Article.objects.create(reference="HUILE15", designation="Huile carton 15 L", prix_vente=15000)
        cls.client_ = Tiers.objects.create(code="CGD", nom="Client gros détail")
        cls.piece(Document.STOCK_ENTREE, cls.magasin, 20, tiers=None)

    @classmethod
    def piece(cls, type_document, depot, quantite, tiers="client", valider=True, **extra):
        doc = Document.objects.create(type_document=type_document, depot=depot,
                                      tiers=cls.client_ if tiers == "client" else tiers, **extra)
        LigneDocument.objects.create(document=doc, article=cls.huile, quantite=Decimal(quantite), prix_unitaire=15000, taux_tva=0)
        doc.recalculer()
        return doc.valider() if valider else doc

    def separer(self, actif=True):
        Societe.objects.update(separation_gros_detail=actif)
        self.boutique.vente_detail = actif
        self.boutique.save()

    def test_sans_separation_aucune_contrainte(self):
        self.piece(Document.FACTURE, self.magasin, "0.5")                         # rien n'est imposé par défaut

    def test_magasin_de_gros_refuse_le_detail(self):
        self.separer()
        self.piece(Document.FACTURE, self.magasin, "2")                           # unités entières : accepté
        with self.assertRaisesMessage(ValidationError, "Vente au détail impossible dans le dépôt"):
            self.piece(Document.FACTURE, self.magasin, "0.5")
        with self.assertRaisesMessage(ValidationError, "Boutique centre-ville"):    # le message indique la boutique
            self.piece(Document.LIVRAISON, self.magasin, "1.5")

    def test_transfert_puis_vente_au_detail_en_boutique(self):
        self.separer()
        self.piece(Document.STOCK_VIREMENT, self.magasin, "2", tiers=None, depot_destination=self.boutique)
        self.piece(Document.FACTURE, self.boutique, "0.5")                        # la boutique vend au détail
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.boutique.pk), Decimal("1.5"))
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.magasin.pk), Decimal("18"))

    def test_parametrage_dans_la_fiche_societe(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))
        societe = Societe.get()
        donnees = {"raison_sociale": "Test", "devise": "XAF", "taux_tva_defaut": "0", "regime_tva": societe.regime_tva,
                   "delai_pointage": 1, "facturation_auto_livraison": "VALIDEE", "separation_gros_detail": "on"}
        reponse = self.client.post(reverse("commercial:societe"), donnees)
        self.assertContains(reponse, "Désignez au moins un dépôt de vente au détail")
        self.client.post(reverse("commercial:societe"), {**donnees, "depots_detail": [self.boutique.pk]})
        self.assertTrue(Societe.get().separation_gros_detail)
        self.assertEqual(list(Depot.objects.filter(vente_detail=True)), [self.boutique])
