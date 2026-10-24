from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.comptabilite.models import Journal
from apps.comptabilite.services import constater_variation_stock, soldes_par_compte
from apps.core.models import Societe

from .models import Article, Depot, Document, Inventaire, LigneDocument, Reglement, StockDepot, Tiers


class BaseCommerciale(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.client_ = Tiers.objects.create(code="C1", nom="Client test")
        cls.fournisseur = Tiers.objects.create(code="F1", nom="Fournisseur test", type_tiers=Tiers.FOURNISSEUR)
        cls.article = Article.objects.create(reference="A1", designation="Article", prix_achat=800, prix_vente=1000)
        cls.depot = Depot.par_defaut()
        cls.agence = Depot.objects.create(code="AG", intitule="Agence")

    def setUp(self):
        # 100 unités à 800 dans le dépôt principal
        self.document(Document.STOCK_ENTREE, None, quantite=100, prix=800).valider()
        self.article.refresh_from_db()

    def document(self, type_document, tiers, quantite=10, prix=1000, **champs):
        doc = Document.objects.create(type_document=type_document, tiers=tiers, **champs)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=quantite, prix_unitaire=prix)
        doc.recalculer()
        return doc

    def stock(self, depot=None):
        self.article.refresh_from_db()
        return StockDepot.quantite_de(self.article.pk, (depot or self.depot).pk) if depot else self.article.stock


class DocumentsVentesAchatsTests(BaseCommerciale):
    def test_calcul_ligne_tva_19_25(self):
        doc = self.document(Document.FACTURE, self.client_, quantite=3, prix=1000)
        self.assertEqual(doc.total_ht, Decimal("3000"))
        self.assertEqual(doc.total_tva, Decimal("578"))  # 577,5 arrondi
        self.assertEqual(doc.total_ttc, Decimal("3578"))

    def test_validation_facture_numerote_comptabilise_et_destocke(self):
        doc = self.document(Document.FACTURE, self.client_).valider()
        self.assertTrue(doc.numero.startswith("FA"))
        self.assertTrue(doc.ecriture.equilibree)
        soldes = soldes_par_compte(doc.date)
        self.assertEqual(soldes["4111"], Decimal("11925"))
        self.assertEqual(soldes["701"], Decimal("-10000"))
        self.assertEqual(soldes["4431"], Decimal("-1925"))
        self.assertEqual(self.stock(), Decimal("90"))
        self.assertEqual(self.stock(self.depot), Decimal("90"))

    def test_facture_fournisseur(self):
        doc = self.document(Document.ACHAT_FACTURE, self.fournisseur, prix=800).valider()
        soldes = soldes_par_compte(doc.date)
        self.assertEqual(soldes["601"], Decimal("8000"))
        self.assertEqual(soldes["4452"], Decimal("1540"))
        self.assertEqual(soldes["4011"], Decimal("-9540"))
        self.assertEqual(self.stock(), Decimal("110"))

    def test_chaine_devis_commande_livraison_facture(self):
        devis = self.document(Document.DEVIS, self.client_).valider()
        self.assertIsNone(devis.ecriture)
        commande = devis.transformer(Document.COMMANDE)
        commande.valider()
        devis.refresh_from_db()
        self.assertEqual(devis.statut, Document.TRANSFORME)
        bl = commande.transformer(Document.LIVRAISON)
        bl.valider()
        facture = bl.transformer(Document.FACTURE)
        facture.valider()
        # Le stock n'est mouvementé qu'une fois (par le BL)
        self.assertEqual(self.stock(), Decimal("90"))
        self.assertIsNotNone(facture.ecriture)

    def test_livraison_partielle_et_reliquat(self):
        commande = self.document(Document.COMMANDE, self.client_, quantite=10).valider()
        bl = commande.transformer(Document.LIVRAISON)
        ligne = bl.lignes.get()
        ligne.quantite = 6
        ligne.save()
        bl.valider()
        commande.refresh_from_db()
        self.assertEqual(commande.statut, Document.VALIDE)
        self.assertTrue(commande.partiellement_transforme)
        self.assertEqual(commande.lignes.get().reste_a_transformer, Decimal("4"))
        # Le second BL reprend uniquement le reliquat
        bl2 = commande.transformer(Document.LIVRAISON)
        self.assertEqual(bl2.lignes.get().quantite, Decimal("4"))
        bl2.valider()
        commande.refresh_from_db()
        self.assertEqual(commande.statut, Document.TRANSFORME)
        with self.assertRaises(ValidationError):
            commande.transformer(Document.LIVRAISON)
        self.assertEqual(self.stock(), Decimal("90"))

    def test_annulation_bl_remet_le_stock_et_le_reliquat(self):
        commande = self.document(Document.COMMANDE, self.client_, quantite=10).valider()
        bl = commande.transformer(Document.LIVRAISON)
        bl.valider()
        self.assertEqual(self.stock(), Decimal("90"))
        bl.annuler()
        commande.refresh_from_db()
        self.assertEqual(self.stock(), Decimal("100"))
        self.assertEqual(commande.statut, Document.VALIDE)
        self.assertEqual(commande.lignes.get().reste_a_transformer, Decimal("10"))

    def test_transformation_interdite(self):
        devis = self.document(Document.DEVIS, self.client_).valider()
        with self.assertRaises(ValidationError):
            devis.transformer(Document.AVOIR)

    def test_tiers_incompatible(self):
        doc = Document(type_document=Document.FACTURE, tiers=self.fournisseur)
        with self.assertRaises(ValidationError):
            doc.clean()

    def test_reglement_impute_et_comptabilise(self):
        f1 = self.document(Document.FACTURE, self.client_).valider()
        f2 = self.document(Document.FACTURE, self.client_).valider()
        caisse = Journal.objects.get(code="CA")
        with self.assertRaises(ValidationError):                       # reçu de créance sans facture : refusé
            Reglement(tiers=self.client_, journal=caisse, montant=Decimal("15000")).enregistrer()
        with self.assertRaises(ValidationError):                       # plus que le reste dû : refusé
            Reglement(tiers=self.client_, journal=caisse, montant=Decimal("15000"), facture=f1).enregistrer()
        # Un versement de 15 000 pour deux factures : un reçu par facture
        Reglement(tiers=self.client_, journal=caisse, montant=Decimal("11925"), facture=f1).enregistrer()
        reglement = Reglement(tiers=self.client_, journal=caisse, montant=Decimal("3075"), facture=f2).enregistrer()
        f1.refresh_from_db(); f2.refresh_from_db()
        self.assertEqual(f1.reste_a_payer, 0)
        self.assertEqual(f2.reste_a_payer, Decimal("11925") * 2 - Decimal("15000"))
        soldes = soldes_par_compte(reglement.date)
        self.assertEqual(soldes["5711"], Decimal("15000"))
        self.assertEqual(self.client_.solde_comptable(), Decimal("11925") * 2 - Decimal("15000"))

    def test_reglement_partiel_et_facture_d_un_autre_client(self):
        f = self.document(Document.FACTURE, self.client_).valider()
        caisse = Journal.objects.get(code="CA")
        autre = Tiers.objects.create(code="CAUTRE", nom="Autre client")
        with self.assertRaisesMessage(ValidationError, "n'est pas celle de"):          # facture d'un autre client
            Reglement(tiers=autre, journal=caisse, montant=Decimal("100"), facture=f).enregistrer()
        Reglement(tiers=self.client_, journal=caisse, montant=Decimal("10000"), facture=f).enregistrer()
        Reglement(tiers=self.client_, journal=caisse, montant=f.total_ttc - Decimal("10000"), facture=f).enregistrer()
        f.refresh_from_db()
        self.assertEqual((f.reste_a_payer, f.recus.count()), (0, 2))                  # deux reçus, facture soldée
        with self.assertRaises(ValidationError):                                       # facture déjà soldée
            Reglement(tiers=self.client_, journal=caisse, montant=Decimal("1"), facture=f).enregistrer()

    def test_facture_de_retour_remet_le_stock(self):
        facture = self.document(Document.FACTURE, self.client_).valider()
        retour = facture.transformer(Document.FACTURE_RETOUR)
        retour.valider()
        self.assertEqual(self.client_.solde_comptable(), 0)
        self.assertEqual(self.stock(), Decimal("100"))

    def test_facture_d_avoir_financiere_ne_touche_pas_le_stock(self):
        facture = self.document(Document.FACTURE, self.client_).valider()
        avoir = facture.transformer(Document.AVOIR)
        avoir.valider()
        self.assertEqual(self.client_.solde_comptable(), 0)
        self.assertEqual(self.stock(), Decimal("90"))

    def test_bon_de_retour_puis_facture_de_retour(self):
        bl = self.document(Document.LIVRAISON, self.client_).valider()
        retour = bl.transformer(Document.RETOUR)
        retour.valider()
        self.assertEqual(self.stock(), Decimal("100"))
        facture_retour = retour.transformer(Document.FACTURE_RETOUR)
        facture_retour.valider()
        self.assertEqual(self.stock(), Decimal("100"))   # pas de second mouvement
        self.assertEqual(self.client_.solde_comptable(), Decimal("-11925"))

    def test_facture_validee_non_annulable(self):
        facture = self.document(Document.FACTURE, self.client_).valider()
        with self.assertRaises(ValidationError):
            facture.annuler()


class StocksTests(BaseCommerciale):
    def test_cmup_recalcule_aux_entrees(self):
        self.assertEqual(self.article.cmup, Decimal("800"))
        self.document(Document.ACHAT_RECEPTION, self.fournisseur, quantite=100, prix=1000).valider()
        self.article.refresh_from_db()
        self.assertEqual(self.article.cmup, Decimal("900"))          # (100×800 + 100×1000) / 200
        self.assertEqual(self.article.valeur_stock, Decimal("180000"))
        # Une sortie ne modifie pas le CMUP
        self.document(Document.LIVRAISON, self.client_, quantite=50).valider()
        self.article.refresh_from_db()
        self.assertEqual(self.article.cmup, Decimal("900"))

    def test_stock_negatif_refuse(self):
        with self.assertRaises(ValidationError):
            self.document(Document.LIVRAISON, self.client_, quantite=150).valider()
        self.assertEqual(self.stock(), Decimal("100"))
        societe = Societe.get()
        societe.stock_negatif_autorise = True
        societe.save()
        self.document(Document.LIVRAISON, self.client_, quantite=150).valider()
        self.assertEqual(self.stock(), Decimal("-50"))

    def test_stock_controle_par_depot(self):
        with self.assertRaises(ValidationError):
            self.document(Document.LIVRAISON, self.client_, quantite=5, depot=self.agence).valider()

    def test_mouvement_de_transfert(self):
        self.document(Document.STOCK_VIREMENT, None, quantite=30, depot=self.depot, depot_destination=self.agence).valider()
        self.assertEqual(self.stock(self.depot), Decimal("70"))
        self.assertEqual(self.stock(self.agence), Decimal("30"))
        self.assertEqual(self.stock(), Decimal("100"))
        self.document(Document.LIVRAISON, self.client_, quantite=5, depot=self.agence).valider()
        self.assertEqual(self.stock(self.agence), Decimal("25"))

    def test_transfert_vers_le_meme_depot_refuse(self):
        doc = self.document(Document.STOCK_VIREMENT, None, depot=self.depot, depot_destination=self.depot)
        with self.assertRaises(ValidationError):
            doc.valider()

    def test_mouvement_de_sortie_sans_ecriture(self):
        doc = self.document(Document.STOCK_SORTIE, None, quantite=10, prix=0).valider()
        self.assertIsNone(doc.ecriture)
        self.assertEqual(doc.total_ht, Decimal("8000"))     # valorisé au CMUP
        self.assertEqual(self.stock(), Decimal("90"))

    def test_saisie_inventaire_genere_les_ecarts(self):
        inventaire = Inventaire.objects.create(depot=self.depot)
        inventaire.initialiser_lignes()
        ligne = inventaire.lignes.get(article=self.article)
        self.assertEqual(ligne.stock_theorique, Decimal("100"))
        ligne.stock_reel = Decimal("97")
        ligne.save()
        inventaire.valider()
        self.assertEqual(self.stock(), Decimal("97"))
        self.assertIsNotNone(inventaire.mouvement_sortie)
        self.assertIsNone(inventaire.mouvement_entree)
        self.assertEqual(inventaire.mouvement_sortie.type_document, Document.STOCK_SORTIE)
        with self.assertRaises(ValidationError):
            inventaire.valider()

    def test_variation_stock_comptabilisee_au_cmup(self):
        constater_variation_stock(timezone.localdate())
        soldes = soldes_par_compte(timezone.localdate())
        self.assertEqual(soldes["311"], Decimal("80000"))   # 100 × 800
        self.assertEqual(soldes["6031"], Decimal("-80000"))
        with self.assertRaises(ValidationError):
            constater_variation_stock(timezone.localdate())
