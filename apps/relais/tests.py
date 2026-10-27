"""Relais Internet : jetons, chaque site ne lit que sa boîte, noms et tailles contrôlés, retrait après intégration."""
import io
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import LotDepose, SiteRelais

NOM = "ERP-LOT-DLA-vers-SIEGE-20261027-1000-1-5.erpx.chiffre"


class RelaisTests(TestCase):
    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        reglages = override_settings(RELAIS_ACTIF=True, RELAIS_DOSSIER=dossier.name)
        reglages.enable()
        self.addCleanup(reglages.disable)
        self.jetons = {}
        for code in ("SIEGE", "DLA", "YDE"):
            sortie = io.StringIO()
            call_command("relais_site", code=code, stdout=sortie)
            self.jetons[code] = sortie.getvalue().strip().splitlines()[-1]

    def appel(self, methode, chemin, code=None, **kw):
        entetes = {"HTTP_AUTHORIZATION": f"Bearer {self.jetons[code]}"} if code else {}
        return getattr(self.client, methode)(f"/relais/v1/{chemin}", **entetes, **kw)

    def deposer(self, code, destination, nom=NOM, corps=b"chiffre"):
        return self.appel("post", f"boites/{destination}/", code, data=corps, content_type="application/octet-stream",
                          HTTP_X_NOM_LOT=nom)

    def test_depot_lecture_retrait(self):
        self.assertEqual(self.deposer("DLA", "SIEGE").status_code, 201)
        self.assertEqual(self.appel("get", "boites/SIEGE/", "SIEGE").json(), {"lots": [NOM]})
        self.assertEqual(b"".join(self.appel("get", f"boites/SIEGE/{NOM}", "SIEGE").streaming_content), b"chiffre")
        self.assertEqual(self.appel("delete", f"boites/SIEGE/{NOM}", "SIEGE").status_code, 200)
        self.assertEqual(self.appel("get", "boites/SIEGE/", "SIEGE").json(), {"lots": []})

    def test_securite(self):
        self.assertEqual(self.appel("get", "boites/SIEGE/").status_code, 401)                  # sans jeton
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer faux"
        self.assertEqual(self.client.get("/relais/v1/boites/SIEGE/").status_code, 401)
        del self.client.defaults["HTTP_AUTHORIZATION"]
        self.deposer("DLA", "SIEGE")
        self.assertEqual(self.appel("get", "boites/SIEGE/", "YDE").status_code, 403)          # la boîte d'un autre
        self.assertEqual(self.appel("get", f"boites/SIEGE/{NOM}", "YDE").status_code, 403)
        self.assertEqual(self.appel("delete", f"boites/SIEGE/{NOM}", "YDE").status_code, 403)
        self.assertEqual(self.deposer("YDE", "SIEGE").status_code, 400)                       # se faire passer pour DLA
        self.assertEqual(self.deposer("DLA", "SIEGE", nom="../../etc.erpx.chiffre").status_code, 400)
        self.assertEqual(self.deposer("DLA", "SIEGE", corps=b"").status_code, 413)
        self.assertEqual(self.deposer("DLA", "XXX").status_code, 404)
        call_command("relais_site", code="DLA", desactiver=True, stdout=io.StringIO())
        self.assertEqual(self.deposer("DLA", "SIEGE").status_code, 401)
        self.assertEqual(LotDepose.objects.count(), 1)

    @override_settings(RELAIS_ACTIF=False)
    def test_inactif_par_defaut(self):
        self.assertEqual(self.appel("get", "boites/SIEGE/", "SIEGE").status_code, 404)

    def test_jeton_jamais_stocke_en_clair(self):
        self.assertFalse(SiteRelais.objects.filter(empreinte_jeton=self.jetons["DLA"]).exists())
