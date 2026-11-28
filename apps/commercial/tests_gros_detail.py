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

    def piece_article(self, type_document, depot, article, quantite):
        doc = Document.objects.create(type_document=type_document, depot=depot, tiers=self.client_)
        LigneDocument.objects.create(document=doc, article=article, quantite=Decimal(quantite), prix_unitaire=1300, taux_tva=0)
        doc.recalculer()
        return doc.valider()

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

    def test_conversion_automatique_au_transfert_vers_la_boutique(self):
        self.separer()
        bouteille = Article.objects.create(reference="HUILE1L", designation="Huile bouteille 1 L", unite="BTL", prix_vente=1300)
        self.huile.article_detail, self.huile.facteur_detail, self.huile.unite = bouteille, Decimal("15"), "CTN"
        self.huile.full_clean()
        self.huile.save()
        self.huile.refresh_from_db()
        cout_carton = self.huile.cout_unitaire
        transfert = self.piece(Document.STOCK_VIREMENT, self.magasin, "2", tiers=None, depot_destination=self.boutique)
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.magasin.pk), Decimal("18"))   # 2 cartons sortis
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.boutique.pk), 0)              # pas de carton en boutique
        self.assertEqual(StockDepot.quantite_de(bouteille.pk, self.boutique.pk), Decimal("30"))   # 30 bouteilles entrées
        bouteille.refresh_from_db()
        self.assertEqual(bouteille.cmup, (cout_carton / 15).quantize(Decimal("0.0001")))           # valeur conservée
        self.assertIn("conversion", transfert.mouvements_stock.get(article=bouteille).libelle)
        vente = Document.objects.create(type_document=Document.FACTURE, depot=self.boutique, tiers=self.client_)
        LigneDocument.objects.create(document=vente, article=bouteille, quantite=Decimal("3"), prix_unitaire=1300, taux_tva=0)
        vente.recalculer()
        vente.valider()                                                           # la boutique vend à la bouteille
        self.assertEqual(StockDepot.quantite_de(bouteille.pk, self.boutique.pk), Decimal("27"))
        with self.assertRaisesMessage(ValidationError, "Annulation impossible"):  # 3 bouteilles déjà vendues
            transfert.annuler()
        with self.assertRaisesMessage(ValidationError, "Vente au détail impossible"):   # bouteille vendue au magasin de gros
            self.piece_article(Document.FACTURE, self.magasin, bouteille, "1")
        vente_retour = Document.objects.create(type_document=Document.STOCK_ENTREE, depot=self.boutique)
        LigneDocument.objects.create(document=vente_retour, article=bouteille, quantite=Decimal("3"), prix_unitaire=0, taux_tva=0)
        vente_retour.recalculer()
        vente_retour.valider()
        transfert.annuler()                                                       # l'annulation défait la conversion
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.magasin.pk), Decimal("20"))
        self.assertEqual(StockDepot.quantite_de(bouteille.pk, self.boutique.pk), 0)

    def test_regles_de_l_article_de_detail(self):
        bouteille = Article.objects.create(reference="B1", designation="Bouteille")
        for detail, facteur in ((bouteille, None), (None, Decimal("15")), (bouteille, Decimal("0")), (self.huile, Decimal("15"))):
            self.huile.article_detail, self.huile.facteur_detail = detail, facteur
            with self.assertRaises(ValidationError):
                self.huile.clean()

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
