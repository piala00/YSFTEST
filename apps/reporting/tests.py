from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.commercial.models import Article, Document, Reglement, Tiers
from apps.comptabilite.models import Ecriture


class PagesEtApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--demo", verbosity=0)
        cls.user = get_user_model().objects.create_superuser("test", "", "pwd")

    def setUp(self):
        self.client.force_login(self.user)

    def test_toutes_les_pages_repondent(self):
        doc = Document.objects.filter(type_document=Document.FACTURE).first()
        urls = [
            reverse("reporting:dashboard"), reverse("reporting:ventes"), reverse("reporting:balance_agee"),
            reverse("reporting:balance_agee") + "?type=FOURNISSEUR",
            reverse("commercial:clients"), reverse("commercial:fournisseurs"), reverse("commercial:articles"),
            reverse("commercial:stock"), reverse("commercial:familles"), reverse("commercial:reglements"),
            reverse("commercial:documents", args=["ventes"]), reverse("commercial:documents", args=["achats"]),
            reverse("commercial:document_create", args=["FACTURE"]), reverse("commercial:document_create", args=["ACHAT_COMMANDE"]),
            reverse("commercial:document_detail", args=[doc.pk]), reverse("commercial:document_print", args=[doc.pk]),
            reverse("commercial:tiers_detail", args=[doc.tiers_id]), reverse("commercial:tiers_create"),
            reverse("commercial:article_detail", args=[Article.objects.first().pk]), reverse("commercial:article_create"),
            reverse("commercial:reglement_create"), reverse("commercial:reglement_create") + f"?document={doc.pk}",
            reverse("commercial:reglement_detail", args=[Reglement.objects.first().pk]),
            reverse("comptabilite:comptes"), reverse("comptabilite:journaux"), reverse("comptabilite:ecritures"),
            reverse("comptabilite:ecriture_create"), reverse("comptabilite:ecriture_detail", args=[Ecriture.objects.first().pk]),
            reverse("comptabilite:journal"), reverse("comptabilite:grand_livre"), reverse("comptabilite:balance"),
            reverse("comptabilite:bilan"), reverse("comptabilite:compte_resultat"), reverse("comptabilite:tva"),
            reverse("comptabilite:lettrage") + "?compte=" + str(doc.ecriture.lignes.first().compte_id),
            reverse("core:societe"), reverse("core:exercices"),
            reverse("comptabilite:balance") + "?export=csv", reverse("comptabilite:grand_livre") + "?export=csv",
            reverse("reporting:ventes") + "?export=clients", reverse("reporting:ventes") + "?export=articles",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_saisie_facture_par_formulaire(self):
        tiers = Tiers.objects.filter(type_tiers=Tiers.CLIENT).first()
        article = Article.objects.first()
        data = {
            "tiers": tiers.pk, "date": "2026-03-01", "date_echeance": "", "reference_externe": "", "notes": "",
            "lignes-TOTAL_FORMS": "1", "lignes-INITIAL_FORMS": "0", "lignes-MIN_NUM_FORMS": "1", "lignes-MAX_NUM_FORMS": "1000",
            "lignes-0-article": article.pk, "lignes-0-designation": "", "lignes-0-quantite": "2",
            "lignes-0-prix_unitaire": "1000", "lignes-0-remise": "0", "lignes-0-taux_tva": "19.25", "valider": "1",
        }
        response = self.client.post(reverse("commercial:document_create", args=["FACTURE"]), data)
        self.assertEqual(response.status_code, 302)
        doc = Document.objects.latest("id")
        self.assertEqual(doc.statut, Document.VALIDE)
        self.assertEqual(doc.total_ttc, 2385)

    def test_connexion_requise(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("reporting:dashboard")).status_code, 302)

    def test_api(self):
        api = APIClient()
        token = api.post("/api/token/", {"username": "test", "password": "pwd"}).json()["token"]
        self.assertEqual(token, Token.objects.get(user=self.user).key)
        api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        for url in ("/api/tiers/", "/api/articles/", "/api/documents/?domaine=ventes", "/api/reglements/",
                    "/api/comptes/", "/api/journaux/", "/api/ecritures/", "/api/reporting/dashboard/",
                    "/api/reporting/balance/", "/api/reporting/bilan/", "/api/reporting/compte-resultat/",
                    "/api/reporting/balance-agee/"):
            with self.subTest(url=url):
                self.assertEqual(api.get(url).status_code, 200)

        tiers = Tiers.objects.filter(type_tiers=Tiers.CLIENT).first()
        article = Article.objects.first()
        r = api.post("/api/documents/", {
            "type_document": "FACTURE", "tiers": tiers.pk, "date": "2026-04-01",
            "lignes": [{"article": article.pk, "designation": "x", "quantite": 1, "prix_unitaire": 1000, "taux_tva": 19.25}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        r = api.post(f"/api/documents/{r.json()['id']}/valider/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["statut"], "VALIDE")
        self.assertEqual(APIClient().get("/api/tiers/").status_code, 401)
