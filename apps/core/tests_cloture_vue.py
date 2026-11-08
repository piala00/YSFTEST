"""Écran « Clôturer l'exercice et ouvrir le suivant » + entrées de menu Fichier multi-sociétés.

Le moteur de clôture est couvert ailleurs (apps.core.test_cloture_annuelle_sqlite,
tests/test_cloture_django_migree). Ici : droits, garde-fous et dégradation propre hors poste
compilé / sans catalogue, et présence des commandes dans les menus.
"""
import json
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core import navigation as nav


class ClotureVueTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026")
        self.agent = get_user_model().objects.create_user("agent", "", "x")

    def test_reservee_administrateur(self):
        self.client.force_login(self.agent)
        self.assertEqual(self.client.get(reverse("core:cloture_exercice_annuel")).status_code, 403)

    def test_sans_catalogue_message_clair_sans_modification(self):
        self.client.force_login(self.admin)
        with mock.patch.dict("os.environ", {"ERP_CATALOGUE_SOCIETES": ""}, clear=False):
            reponse = self.client.get(reverse("core:cloture_exercice_annuel"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "non configuré")

    def test_post_hors_poste_compile_refuse(self):
        # Catalogue configuré mais pas de poste serveur compilé : la clôture est refusée (moteur non exécuté).
        self.client.force_login(self.admin)
        with tempfile.TemporaryDirectory() as dossier:
            catalogue = Path(dossier) / "societes.json"
            catalogue.write_text(json.dumps({"version": 1, "bases": [
                {"id": "gtc-2025", "societe": "GTC", "agence": "Bertoua", "exercice": "2025",
                 "moteur": "sqlite", "base": str(Path(dossier) / "erp-2025.sqlite3")}]}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"ERP_CATALOGUE_SOCIETES": str(catalogue)}, clear=False), \
                 mock.patch("apps.core.poste.disponible", return_value=False):
                reponse = self.client.post(reverse("core:cloture_exercice_annuel"), {"confirmation": "CLOTURER"})
        self.assertEqual(reponse.status_code, 403)


class MenuSocieteTests(TestCase):
    def _fichier(self, module):
        return next(o for o in module.onglets if o.code == "fichier")

    def test_ouvrir_societe_et_cloture_dans_les_menus(self):
        for module in (nav.GESTION_COMMERCIALE, nav.COMPTABILITE, nav.TRANSPORT):
            codes = {e.code for e in self._fichier(module).elements}
            self.assertIn("fichier.ouvrir_societe", codes, f"{module.code} : « Ouvrir une société » attendu")
            self.assertIn("fichier.cloture_annuelle", codes, f"{module.code} : clôture annuelle attendue")

    def test_ouvrir_societe_pointe_vers_le_choix(self):
        fichier = self._fichier(nav.TRANSPORT)
        ouvrir = next(e for e in fichier.elements if e.code == "fichier.ouvrir_societe")
        self.assertEqual(ouvrir.url, "core:choix_societe")
