"""Fenêtre de sélection avant les états (comme dans Sage 100)."""
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Depot, Document, LigneDocument, Tiers


class FenetreSelectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="automatique")
        cls.client1 = Tiers.objects.create(code="C1", nom="Alpha")
        cls.client2 = Tiers.objects.create(code="C2", nom="Bêta")
        cls.article = Article.objects.create(reference="A1", designation="Ciment", prix_vente=1000)
        cls.depot = Depot.par_defaut()
        entree = Document.objects.create(type_document=Document.STOCK_ENTREE)
        LigneDocument.objects.create(document=entree, article=cls.article, quantite=50, prix_unitaire=800)
        entree.recalculer()
        entree.valider()
        for tiers in (cls.client1, cls.client2):
            doc = Document.objects.create(type_document=Document.FACTURE, tiers=tiers)
            LigneDocument.objects.create(document=doc, article=cls.article, quantite=1, prix_unitaire=1000)
            doc.recalculer()
            doc.valider()

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("sel", "", "x"))

    def test_la_selection_s_ouvre_avant_l_etat(self):
        reponse = self.client.get(reverse("comptabilite:balance") + "?compte_debut=4&compte_fin=4")
        self.assertTemplateUsed(reponse, "core/selection.html")
        self.assertContains(reponse, 'name="compte_debut" value="4"')               # lien du menu prérempli
        self.assertContains(reponse, 'name="ok" value="1"')

    def test_resultat_avec_rappel_et_modification(self):
        url = reverse("comptabilite:balance") + "?date_debut=2026-01-01&date_fin=2026-12-31&ok=1"
        reponse = self.client.get(url)
        self.assertTemplateUsed(reponse, "comptabilite/balance.html")
        self.assertContains(reponse, "du 01/01/2026 au 31/12/2026")
        self.assertContains(reponse, "Modifier la sélection")
        self.assertContains(reponse, "export=csv")

    def test_criteres_tiers_et_depot(self):
        url = reverse("commercial:statistique", args=["palmares_clients"])
        self.assertTemplateUsed(self.client.get(url), "core/selection.html")
        reponse = self.client.get(url + f"?ok=1&tiers={self.client1.pk}")
        noms = [l["tiers"] for l in reponse.context["etat"]["lignes"]]
        self.assertEqual(noms, ["Alpha"])
        self.assertContains(reponse, "C1 - Alpha")                                    # rappel de la sélection
        agee = self.client.get(reverse("comptabilite:balance_agee") + f"?type=CLIENT&tiers={self.client2.pk}&ok=1")
        self.assertEqual([l["tiers"] for l in agee.context["data"]["lignes"]], [self.client2])
        hier = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        avant = self.client.get(reverse("comptabilite:balance_agee") + f"?type=CLIENT&date={hier}&ok=1")
        self.assertEqual(avant.context["data"]["lignes"], [])                        # factures du jour exclues

    def test_mouvements_par_periode_et_article(self):
        url = reverse("commercial:mouvements")
        demain = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        self.assertEqual(len(self.client.get(url + f"?ok=1&article={self.article.pk}").context["object_list"]), 3)
        self.assertEqual(len(self.client.get(url + f"?ok=1&date_debut={demain}").context["object_list"]), 0)

    def test_export_et_liens_internes_sans_fenetre(self):
        self.assertEqual(self.client.get(reverse("comptabilite:balance") + "?export=csv")["Content-Type"],
                         "text/csv; charset=utf-8")
        reponse = self.client.get(reverse("comptabilite:grand_livre") + f"?tiers={self.client1.pk}&ok=1")
        self.assertTemplateUsed(reponse, "comptabilite/grand_livre.html")
