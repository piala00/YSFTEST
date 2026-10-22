"""Liaison Gestion commerciale → Comptabilité : scénarios du dossier « liaisons comptabilité » (T13 à T44)."""
import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Depot, Document, LigneDocument, Reglement, StockDepot, Tiers
from apps.comptabilite import services
from apps.comptabilite.models import Ecriture, Journal
from apps.core.models import Exercice


class LiaisonComptableTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="automatique")
        cls.client_ = Tiers.objects.create(code="CLIA", nom="Client liaison")
        cls.article = Article.objects.create(reference="ALIA", designation="Ciment", prix_vente=1000, suivi_stock=False)
        cls.jour = datetime.date.today()
        cls.exercice = Exercice.courant()

    def facture(self, valider=True):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=self.client_)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=2, prix_unitaire=1000)
        doc.recalculer()
        if valider:
            doc.valider()
        return doc

    def controle(self):
        return services.controle_liaison(self.exercice.date_debut, self.exercice.date_fin)

    def test_flux_conforme(self):
        doc = self.facture()
        Reglement(tiers=self.client_, journal=Journal.objects.get(code="CA"), montant=doc.total_ttc).enregistrer()
        resultat = self.controle()
        self.assertEqual(resultat["anomalies"], [])
        ventes, _, reglements = resultat["flux"]
        self.assertEqual((ventes["nombre"], ventes["conformes"], ventes["ttc"]), (1, 1, doc.total_ttc))
        self.assertEqual((reglements["nombre"], reglements["conformes"]), (1, 1))

    def test_T21_facture_non_validee_jamais_comptabilisee(self):
        doc = self.facture(valider=False)
        self.assertIsNone(doc.ecriture)
        self.assertEqual(self.controle()["flux"][0]["nombre"], 0)                  # le brouillon n'est pas un flux attendu

    def test_T25_periode_fermee_refus_sans_validation_partielle(self):
        Journal.objects.filter(code="VT").update(cloture_au=self.jour)
        doc = self.facture(valider=False)
        with self.assertRaises(ValidationError):
            doc.valider()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, doc.ecriture_id), (Document.BROUILLON, None))  # tout ou rien

    def test_T25_stock_non_mouvemente_si_comptabilisation_refusee(self):
        depot = Depot.par_defaut()
        article = Article.objects.create(reference="ASTK", designation="Tôle", prix_vente=500)
        StockDepot.ajouter(article, depot, 10)
        Journal.objects.filter(code="VT").update(cloture_au=self.jour)
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=self.client_, depot=depot)
        LigneDocument.objects.create(document=doc, article=article, quantite=3, prix_unitaire=500)
        doc.recalculer()
        with self.assertRaises(ValidationError):
            doc.valider()
        self.assertEqual(article.stock_depot(depot), 10)
        self.assertFalse(doc.mouvements_stock.exists())

    def test_T28_rejeu_sans_doublon(self):
        doc = self.facture()
        avant = Ecriture.objects.count()
        self.assertEqual(services.comptabiliser_document(doc), doc.ecriture)
        self.assertEqual(Ecriture.objects.count(), avant)

    def test_T44_anomalies_detectees_et_cloture_bloquee(self):
        oubliee = self.facture()
        Document.objects.filter(pk=oubliee.pk).update(ecriture=None)               # facture sans écriture
        ecart = self.facture()
        Document.objects.filter(pk=ecart.pk).update(total_ttc=ecart.total_ttc + 100)  # montant divergent
        problemes = {a["probleme"].split(" (")[0] for a in self.controle()["anomalies"]}
        self.assertEqual(problemes, {"Aucune écriture comptable", "Montant du tiers en comptabilité différent",
                                     "Pièce commerciale introuvable : écriture passée en double ou pièce supprimée"})
        self.assertTrue(any("liaison commerciale" in e for e in services.controles_cloture(self.exercice)))
        with self.assertRaises(ValidationError):
            services.cloturer_exercice(self.exercice)

    def test_T13_code_tiers_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Tiers.objects.create(code="CLIA", nom="Autre client homonyme de code")

    def test_T19_tiers_utilise_non_supprimable(self):
        self.facture()
        with self.assertRaises(ProtectedError):
            self.client_.delete()

    def test_ecran_controle_liaison(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))
        url = reverse("comptabilite:controle_liaison")
        self.assertTemplateUsed(self.client.get(url), "core/selection.html")      # fenêtre de sélection d'abord
        self.facture()
        reponse = self.client.get(url + "?ok=1")
        self.assertContains(reponse, "Aucune anomalie")
