"""Tiers payeur (siège, centrale qui règle les factures d'un client) et alerte de doublon à la création d'un tiers."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Document, LigneDocument, Reglement, Tiers
from apps.comptabilite import services
from apps.comptabilite.models import Journal
from apps.core.models import Exercice
from apps.reporting import services as reporting


class TiersPayeurTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="automatique")
        cls.siege = Tiers.objects.create(code="CSIEGE", nom="Siège Douala", plafond_credit=Decimal("3000"),
                                         code_risque=Tiers.RISQUE_BLOQUER)
        cls.agence = Tiers.objects.create(code="CAGENCE", nom="Agence Bertoua", payeur=cls.siege)
        cls.article = Article.objects.create(reference="APAY", designation="Ciment", prix_vente=1000, suivi_stock=False)

    def facture(self, tiers, quantite=1):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=tiers)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=quantite, prix_unitaire=1000, taux_tva=0)
        doc.recalculer()
        return doc

    def test_creance_portee_par_le_payeur(self):
        doc = self.facture(self.agence)
        self.assertEqual(doc.payeur, self.siege)                                  # repris de la fiche à la création
        doc.valider()
        ligne = doc.ecriture.lignes.get(tiers__isnull=False)
        self.assertEqual((ligne.tiers, ligne.debit), (self.siege, Decimal("1000")))
        self.assertIn("Agence Bertoua", doc.ecriture.libelle)                    # le client reste visible
        self.assertEqual(self.siege.encours(), Decimal("1000"))
        self.assertEqual(services.controle_liaison(Exercice.courant().date_debut, Exercice.courant().date_fin)["anomalies"], [])

    def test_reglement_du_payeur_solde_la_facture_de_l_agence(self):
        doc = self.facture(self.agence)
        doc.valider()
        Reglement(tiers=self.siege, journal=Journal.objects.get(code="CA"), montant=Decimal("1000"), facture=doc).enregistrer()
        doc.refresh_from_db()
        self.assertEqual(doc.reste_a_payer, 0)

    def test_encours_controle_sur_le_payeur(self):
        self.facture(self.siege, quantite=2).valider()
        with self.assertRaises(ValidationError):                                  # 2 000 + 2 000 > plafond 3 000
            self.facture(self.agence, quantite=2).valider()

    def test_balance_agee_chez_le_payeur(self):
        self.facture(self.agence).valider()
        lignes = reporting.balance_agee(Tiers.CLIENT)["lignes"]
        self.assertEqual([l["tiers"] for l in lignes], [self.siege])

    def test_regles_de_la_fiche(self):
        fournisseur = Tiers.objects.create(code="FPAY", nom="Fournisseur", type_tiers=Tiers.FOURNISSEUR)
        for payeur, erreur in ((fournisseur, "même type"), (self.agence, "a lui-même un tiers payeur")):
            tiers = Tiers(code="CNEW", nom="Nouveau", payeur=payeur)
            with self.assertRaisesMessage(ValidationError, erreur):
                tiers.clean()

    def test_transformation_garde_le_payeur(self):
        commande = Document.objects.create(type_document=Document.COMMANDE, tiers=self.agence)
        LigneDocument.objects.create(document=commande, article=self.article, quantite=1, prix_unitaire=1000)
        commande.recalculer()
        commande.valider()
        self.assertEqual(commande.transformer(Document.LIVRAISON).payeur, self.siege)


class DoublonTiersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        Tiers.objects.create(code="C0001", nom="Quincaillerie  du Centre")

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))

    def creer(self, **extra):
        return self.client.post(reverse("commercial:tiers_create") + "?type=CLIENT", {
            "type_tiers": "CLIENT", "code": "C0002", "nom": "quincaillerie du centre", "delai_paiement": 30,
            "plafond_credit": 0, "code_risque": "AVERTIR", "assujetti_tva": "on", "actif": "on", **extra})

    def test_meme_nom_demande_confirmation(self):
        reponse = self.creer()
        self.assertContains(reponse, "Un tiers porte déjà ce nom")
        self.assertContains(reponse, "Créer quand même ce tiers")
        self.assertFalse(Tiers.objects.filter(code="C0002").exists())
        self.creer(confirmer_doublon="on")
        self.assertTrue(Tiers.objects.filter(code="C0002").exists())
