from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.comptabilite.models import Journal
from apps.comptabilite.services import soldes_par_compte

from .models import Article, Document, LigneDocument, Reglement, Tiers


class FluxCommercialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.client_ = Tiers.objects.create(code="C1", nom="Client test")
        cls.fournisseur = Tiers.objects.create(code="F1", nom="Fournisseur test", type_tiers=Tiers.FOURNISSEUR)
        cls.article = Article.objects.create(reference="A1", designation="Article", prix_achat=800, prix_vente=1000, stock=100)

    def _document(self, type_document, tiers, quantite=10, prix=1000):
        doc = Document.objects.create(type_document=type_document, tiers=tiers)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=quantite, prix_unitaire=prix)
        doc.recalculer()
        return doc

    def test_calcul_ligne_tva_19_25(self):
        doc = self._document(Document.FACTURE, self.client_, quantite=3, prix=1000)
        self.assertEqual(doc.total_ht, Decimal("3000"))
        self.assertEqual(doc.total_tva, Decimal("578"))  # 577,5 arrondi
        self.assertEqual(doc.total_ttc, Decimal("3578"))

    def test_validation_facture_numerote_comptabilise_et_destocke(self):
        doc = self._document(Document.FACTURE, self.client_).valider()
        self.assertTrue(doc.numero.startswith("FA"))
        self.assertTrue(doc.ecriture.equilibree)
        soldes = soldes_par_compte(doc.date)
        self.assertEqual(soldes["4111"], Decimal("11925"))
        self.assertEqual(soldes["701"], Decimal("-10000"))
        self.assertEqual(soldes["4431"], Decimal("-1925"))
        self.article.refresh_from_db()
        self.assertEqual(self.article.stock, Decimal("90"))

    def test_facture_fournisseur(self):
        doc = self._document(Document.ACHAT_FACTURE, self.fournisseur, prix=800).valider()
        soldes = soldes_par_compte(doc.date)
        self.assertEqual(soldes["601"], Decimal("8000"))
        self.assertEqual(soldes["4452"], Decimal("1540"))
        self.assertEqual(soldes["4011"], Decimal("-9540"))
        self.article.refresh_from_db()
        self.assertEqual(self.article.stock, Decimal("110"))

    def test_chaine_devis_commande_livraison_facture(self):
        devis = self._document(Document.DEVIS, self.client_).valider()
        self.assertIsNone(devis.ecriture)
        commande = devis.transformer(Document.COMMANDE)
        commande.valider()
        devis.refresh_from_db()
        self.assertEqual(devis.statut, Document.TRANSFORME)
        bl = commande.transformer(Document.LIVRAISON)
        bl.valider()
        facture = bl.transformer(Document.FACTURE)
        facture.valider()
        self.article.refresh_from_db()
        # Le stock n'est mouvementé qu'une fois (par le BL)
        self.assertEqual(self.article.stock, Decimal("90"))
        self.assertIsNotNone(facture.ecriture)

    def test_transformation_interdite(self):
        devis = self._document(Document.DEVIS, self.client_).valider()
        with self.assertRaises(ValidationError):
            devis.transformer(Document.AVOIR)

    def test_tiers_incompatible(self):
        doc = Document(type_document=Document.FACTURE, tiers=self.fournisseur)
        with self.assertRaises(ValidationError):
            doc.clean()

    def test_reglement_impute_et_comptabilise(self):
        f1 = self._document(Document.FACTURE, self.client_).valider()
        f2 = self._document(Document.FACTURE, self.client_).valider()
        reglement = Reglement(tiers=self.client_, journal=Journal.objects.get(code="CA"), montant=Decimal("15000"))
        reglement.enregistrer()
        f1.refresh_from_db(); f2.refresh_from_db()
        self.assertEqual(f1.reste_a_payer, 0)
        self.assertEqual(f2.reste_a_payer, Decimal("11925") * 2 - Decimal("15000"))
        soldes = soldes_par_compte(reglement.date)
        self.assertEqual(soldes["5711"], Decimal("15000"))
        self.assertEqual(self.client_.solde_comptable(), Decimal("11925") * 2 - Decimal("15000"))

    def test_avoir_contrepasse(self):
        facture = self._document(Document.FACTURE, self.client_).valider()
        avoir = facture.transformer(Document.AVOIR)
        avoir.valider()
        self.assertEqual(self.client_.solde_comptable(), 0)
        self.article.refresh_from_db()
        self.assertEqual(self.article.stock, Decimal("100"))

    def test_variation_stock(self):
        from apps.comptabilite.services import constater_variation_stock
        from django.utils import timezone

        constater_variation_stock(timezone.localdate())
        soldes = soldes_par_compte(timezone.localdate())
        self.assertEqual(soldes["311"], Decimal("80000"))   # 100 x 800
        self.assertEqual(soldes["6031"], Decimal("-80000"))
        with self.assertRaises(ValidationError):
            constater_variation_stock(timezone.localdate())

    def test_facture_validee_non_annulable(self):
        facture = self._document(Document.FACTURE, self.client_).valider()
        with self.assertRaises(ValidationError):
            facture.annuler()
