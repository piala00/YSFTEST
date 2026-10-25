import tempfile

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from . import lots, scenario


class ScenarioTroisDossiersTests(SimpleTestCase):
    """Siège, Douala et Yaoundé : trois bases distinctes qui ne communiquent que par fichiers .erpx."""

    def test_billets_colis_entre_agences_et_consolidation(self):
        with tempfile.TemporaryDirectory() as travail:
            r = scenario.executer(travail)
        self.assertEqual(r["dla_referentiels"]["gares"], 4)                    # référentiels reçus du siège
        self.assertEqual(r["dla_referentiels"]["arrets_dla_gbl"], ["DLA", "BTA", "GBL"])  # avec les arrêts des lignes
        self.assertEqual(r["dla_referentiels"]["liaisons"], ["18501", "18503", "18504"])  # même compte = même agence partout
        self.assertIn("rejetés : 0", r["siege_import1"])
        self.assertIn("déjà reçu", r["siege_rejeu"])                          # rejeu sans effet
        self.assertEqual(r["yde_remise"]["avant"], "EN_ROUTE")                 # colis relayé, car parti
        self.assertEqual(r["yde_remise"]["statut"], "LIVRE")
        self.assertEqual(r["yde_remise"]["compte_cr"], "18502")                # dû à Douala
        self.assertEqual(r["yde_remise"]["billets_ici"], 0)                    # les billets restent au siège
        self.assertEqual({k: r["dla_reversement"][k] for k in ("statut", "livre_site", "compte")},
                         {"statut": "LIVRE", "livre_site": "YDE", "compte": "18503"})
        # Correspondance à Bertoua : la part du tronçon va au car de Bertoua, qui la doit à Douala
        self.assertEqual(r["dla_vente"]["parts"], ["7333", "3667"])
        self.assertEqual(r["bta_correspondance"]["lignes"], {"18502": ["3667.00", "0.00", None],
                                                             "70611": ["0.00", "3667.00", "EN 202 BB"]})
        self.assertEqual(r["dla_reversement"]["troncon2"], ["EFFECTUE", "EN 202 BB", "BTA"])
        self.assertNotIn("manquants", r["dla_import2"])
        c = r["siege_consolide"]
        self.assertEqual(c["ecritures"], 10)                                   # + le plein de Bertoua
        self.assertEqual(c["journaux"], ["CA-BTA", "CA-DLA", "CA-YDE", "OD-BTA", "OD-DLA"])
        self.assertEqual(c["liaisons_185"], "0.00")                            # liaisons neutralisées
        self.assertEqual(c["billets_a_voyager"], "0.00")                       # tous les voyages faits
        self.assertEqual((c["recette_LT101"], c["recette_LT303"], c["recette_EN202"]), ("12000.00", "7333.00", "3667.00"))
        self.assertEqual((c["produits_70611"], c["produits_70612"], c["caisse"]), ("-23000.00", "-2000.00", "-101000.00"))
        self.assertEqual(c["billets"], 3)
        self.assertEqual(c["carburant_EN202"], "126000.00")                    # plein de Bertoua sur son car, au siège
        self.assertEqual(c["pleins"], ["150.00"])
        self.assertIn("abîmé", r["altere"])


class LotsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)

    def test_agence_non_configuree(self):
        from apps.core.models import Agence

        a = Agence.objects.create(code="X", nom="X")
        with self.assertRaisesMessage(lots.LotInvalide, "pas encore configuré"):
            lots.exporter(a)

    def test_signature_et_destination(self):
        from apps.core.models import Agence

        lots.configurer_siege("SIEGE", "Siège")
        dla = lots.ajouter_agence("DLA", "Douala")
        yde = lots.ajouter_agence("YDE", "Yaoundé")
        nom, octets = lots.exporter(dla)
        with self.assertRaisesMessage(lots.LotInvalide, "destiné à DLA"):        # au siège, un lot pour Douala est refusé
            lots.importer(octets)
        with self.assertRaisesMessage(lots.LotInvalide, "pas un lot d'échange"):
            lots.importer(b"bonjour")
        self.assertEqual(Agence.objects.get(code="YDE").compte_liaison.numero, "18503")
        with self.assertRaisesMessage(lots.LotInvalide, "fichier d'installation"):
            lots.importer(lots.fichier_installation(yde)[1])


class EcranEchangesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)

    def test_configurer_siege_declarer_agence_et_fichiers(self):
        from django.contrib.auth import get_user_model
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.urls import reverse

        from apps.core.models import Agence

        url = reverse("transport:echanges") + "?seul=1"
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        self.assertContains(self.client.get(url), "Ce poste est le siège")
        self.client.post(url, {"action": "siege", "code": "siege", "nom": "Siège"})
        self.client.post(url, {"action": "agence", "code": "dla", "nom": "Agence de Douala"})
        dla = Agence.objects.get(code="DLA")
        page = self.client.get(url)
        self.assertContains(page, "Agence de Douala")
        self.assertContains(page, "18502")
        reponse = self.client.post(url, {"action": "installation", "agence": dla.pk})
        self.assertIn("ERP-INSTALLATION-SIEGE-vers-DLA", reponse["Content-Disposition"])
        reponse = self.client.post(url, {"action": "exporter", "destination": dla.pk})
        self.assertIn(".erpx", reponse["Content-Disposition"])
        page = self.client.post(url, {"action": "importer", "fichiers": [SimpleUploadedFile("x.erpx", b"abc")]}, follow=True)
        self.assertContains(page, "refusé")
        for module in ("commercial", "comptabilite"):
            self.assertEqual(self.client.get(reverse(f"{module}:echanges")).status_code, 200)
