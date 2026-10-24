"""Régime de TVA de la société : assujettie, non assujettie, ou pas encore paramétrée."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.comptabilite.services import declaration_tva, soldes_par_compte
from apps.core.models import Societe

from .models import Article, Document, LigneDocument, Tiers


class RegimeTvaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.client_ = Tiers.objects.create(code="C1", nom="Client")
        cls.fournisseur = Tiers.objects.create(code="F1", nom="Fournisseur", type_tiers=Tiers.FOURNISSEUR)

    def regime(self, regime):
        societe = Societe.get()
        societe.regime_tva = regime
        societe.save()

    def document(self, type_document, tiers, article, quantite, prix):
        doc = Document.objects.create(type_document=type_document, tiers=tiers)
        LigneDocument.objects.create(document=doc, article=article, quantite=quantite, prix_unitaire=prix)
        doc.recalculer()
        return doc

    def achat_puis_vente(self, taux=Decimal("19.25")):
        article = Article.objects.create(reference="A1", designation="Article", prix_achat=1000, prix_vente=2000, taux_tva=taux)
        achat = self.document(Document.ACHAT_FACTURE, self.fournisseur, article, 10, 1000).valider()
        vente = self.document(Document.FACTURE, self.client_, article, 5, 2000).valider()
        article.refresh_from_db()
        return article, achat, vente

    def test_tva_desactivee_par_defaut(self):
        societe = Societe.get()
        self.assertEqual((societe.regime_tva, societe.taux_tva_defaut), (Societe.TVA_NON_PRECISEE, 0))
        article = Article.objects.create(reference="A0", designation="Article", prix_vente=2000, suivi_stock=False)
        self.assertEqual(article.taux_tva, 0)                                 # aucun taux proposé
        vente = self.document(Document.FACTURE, self.client_, article, 5, 2000).valider()
        self.assertEqual((vente.total_tva, vente.total_ttc), (0, Decimal("10000")))
        # Un article à qui l'utilisateur donne un taux le garde : rien n'est interdit, rien n'est imposé
        article, achat, vente = self.achat_puis_vente()
        self.assertEqual(vente.total_tva, Decimal("1925"))

    def test_societe_assujettie(self):
        self.regime(Societe.TVA_ASSUJETTIE)
        article, achat, vente = self.achat_puis_vente()
        self.assertEqual(achat.total_tva, Decimal("1925"))
        self.assertEqual(vente.total_tva, Decimal("1925"))
        self.assertEqual(article.cmup, Decimal("1000"))                      # coût HT
        tva = declaration_tva(vente.date, vente.date)
        self.assertEqual(tva["collectee"], Decimal("1925"))
        self.assertEqual(tva["deductible"], Decimal("1925"))

    def test_societe_non_assujettie(self):
        self.regime(Societe.TVA_NON_ASSUJETTIE)
        article, achat, vente = self.achat_puis_vente()
        # Ventes facturées sans TVA
        self.assertEqual(vente.total_tva, 0)
        self.assertEqual(vente.total_ttc, Decimal("10000"))
        # Le fournisseur facture la TVA, mais elle n'est pas récupérable : elle entre dans le coût
        self.assertEqual(achat.total_ttc, Decimal("11925"))
        self.assertEqual(article.cmup, Decimal("1192.5"))
        soldes = soldes_par_compte(vente.date)
        self.assertNotIn("4431", soldes)
        self.assertNotIn("4452", soldes)
        self.assertEqual(soldes["601"], Decimal("11925"))
        self.assertEqual(soldes["4011"], Decimal("-11925"))
        self.assertEqual(soldes["701"], Decimal("-10000"))

    def test_brouillon_saisi_avant_le_changement_de_regime(self):
        article = Article.objects.create(reference="A2", designation="Article", prix_vente=1000, suivi_stock=False,
                                         taux_tva=Decimal("19.25"))
        devis = self.document(Document.FACTURE, self.client_, article, 1, 1000)
        self.assertEqual(devis.total_tva, Decimal("193"))
        self.regime(Societe.TVA_NON_ASSUJETTIE)
        devis.valider()
        self.assertEqual(devis.total_tva, 0)
        self.assertNotIn("4431", soldes_par_compte(devis.date))

    def test_fournisseur_non_assujetti(self):
        self.regime(Societe.TVA_ASSUJETTIE)
        fournisseur = Tiers.objects.create(code="F2", nom="Artisan", type_tiers=Tiers.FOURNISSEUR, assujetti_tva=False)
        article = Article.objects.create(reference="A3", designation="Article", prix_achat=500)
        achat = self.document(Document.ACHAT_FACTURE, fournisseur, article, 2, 500).valider()
        self.assertEqual(achat.total_tva, 0)

    def test_taux_par_defaut_des_articles(self):
        societe = Societe.get()
        societe.taux_tva_defaut = Decimal("0")
        societe.save()
        self.assertEqual(Article.objects.create(reference="A4", designation="Exonéré").taux_tva, 0)

    def test_aucun_bandeau_et_impression(self):
        user = get_user_model().objects.create_superuser("tva", "", "x")
        self.client.force_login(user)
        self.assertNotContains(self.client.get("/commercial/"), "Régime de TVA")     # rien n'est imposé
        self.regime(Societe.TVA_NON_ASSUJETTIE)
        article = Article.objects.create(reference="A5", designation="Article", prix_vente=1000, suivi_stock=False)
        vente = self.document(Document.FACTURE, self.client_, article, 1, 1000).valider()
        self.assertContains(self.client.get(reverse("commercial:document_print", args=[vente.pk])), "TVA non applicable")
        self.assertContains(self.client.get("/comptabilite/tva/?ok=1"), "non assujettie")

    def test_configuration_automatique_ou_manuelle(self):
        from apps.comptabilite.models import Taxe

        self.assertFalse(Taxe.objects.exists())                                    # non précisée : aucun taux créé
        user = get_user_model().objects.create_superuser("conf", "", "x")
        self.client.force_login(user)
        donnees = {"raison_sociale": "Test", "devise": "XAF", "taux_tva_defaut": "19.25", "regime_tva": "MANUELLE",
                   "delai_pointage": 1, "facturation_auto_livraison": "VALIDEE"}
        self.client.post(reverse("commercial:societe"), donnees)
        self.assertEqual(Societe.get().taux_tva_defaut, 0)
        self.assertFalse(Taxe.objects.exists())
        self.assertEqual(Article.objects.create(reference="M1", designation="Sans TVA").taux_tva, 0)
        self.client.post(reverse("commercial:societe"), {**donnees, "taux_tva_defaut": "0", "regime_tva": "AUTOMATIQUE"})
        self.assertEqual(Societe.get().taux_tva_defaut, Decimal("19.25"))
        self.assertEqual(set(Taxe.objects.values_list("code", flat=True)), {"C19", "D19", "C11", "C0"})

    def test_init_erp_option_regime(self):
        call_command("init_erp", verbosity=0, regime_tva="non-assujettie")
        self.assertEqual(Societe.get().regime_tva, Societe.TVA_NON_ASSUJETTIE)


class FiscaliteCamerounTests(TestCase):
    """CGI 2026 (skill ohada-cameroun-fiscalite-comptable) : CAC et mentions de facture, art. 150-5."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="assujettie")
        cls.client_ = Tiers.objects.create(code="C1", nom="Client")
        cls.article = Article.objects.create(reference="A1", designation="Article", prix_vente=100000, suivi_stock=False)

    def facture(self):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=self.client_)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=1, prix_unitaire=100000)
        doc.recalculer()
        return doc

    def test_tva_principal_et_cac(self):
        v = self.facture().ventilation_tva()[0]
        self.assertEqual(v["tva"], Decimal("19250"))
        self.assertEqual((v["principal"], v["cac"]), (Decimal("17500"), Decimal("1750")))

    def test_mentions_obligatoires_seulement_si_le_controle_est_active(self):
        self.assertEqual(self.facture().mentions_manquantes(), [])                 # facultatif par défaut
        societe = Societe.get()
        societe.controle_mentions_facture = True
        societe.save()
        doc = self.facture()
        manque = doc.mentions_manquantes()
        self.assertIn("NIU de la société", manque)
        self.assertIn("NIU du client Client", manque)
        societe = Societe.get()
        societe.niu, societe.rccm, societe.ville = "M012345678901A", "RC/BTA/2026/B/001", "Bertoua"
        societe.save()
        self.client_.niu, self.client_.ville = "P098765432109Z", "Bertoua"
        self.client_.save()
        self.assertEqual(self.facture().mentions_manquantes(), [])

    def test_comptes_et_taxes_officiels(self):
        from apps.comptabilite.models import Compte, Taxe

        for numero in ("4433", "4434", "4426", "4491", "4441", "4449"):
            self.assertTrue(Compte.objects.filter(numero=numero).exists(), numero)
        self.assertEqual(Taxe.objects.get(code="C11").taux, Decimal("11"))
        self.assertEqual(Taxe.objects.get(code="C0").taux, Decimal("0"))
