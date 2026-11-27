"""Écran « Clôturer l'exercice et ouvrir le suivant » + entrées de menu Fichier multi-sociétés."""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core import navigation as nav
from apps.core import views_cloture


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
        self.client.force_login(self.admin)
        with tempfile.TemporaryDirectory() as dossier:
            catalogue = Path(dossier) / "societes.json"
            catalogue.write_text(json.dumps({"version": 1, "bases": [
                {"id": "gtc-2025", "societe": "GTC", "agence": "Bertoua", "exercice": "2025",
                 "moteur": "sqlite", "base": str(Path(dossier) / "erp-2025.sqlite3")}
            ]}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"ERP_CATALOGUE_SOCIETES": str(catalogue)}, clear=False), \
                 mock.patch("apps.core.poste.disponible", return_value=False):
                reponse = self.client.post(reverse("core:cloture_exercice_annuel"), {"confirmation": "CLOTURER"})
        self.assertEqual(reponse.status_code, 403)

    def test_base_courante_reconnue_par_identite_physique_sqlite(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / "source.sqlite3"
            alias = Path(dossier) / "alias.sqlite3"
            source.write_bytes(b"base de test")
            try:
                os.link(source, alias)
            except (OSError, NotImplementedError):
                self.skipTest("Les liens physiques ne sont pas disponibles sur ce système")

            curseur = mock.MagicMock()
            curseur.fetchall.return_value = [(0, "main", str(source))]
            connexion = mock.MagicMock()
            connexion.vendor = "sqlite"
            connexion.settings_dict = {"NAME": str(source)}
            connexion.cursor.return_value.__enter__.return_value = curseur
            entree = {"id": "n", "moteur": "sqlite", "base": str(alias), "exercice": "2026", "cloture": False}
            with mock.patch.object(views_cloture, "connection", connexion):
                self.assertIs(views_cloture._entree_courante([entree]), entree)

    def test_base_non_sqlite_ne_correspond_pas_au_catalogue_sqlite(self):
        connexion = mock.MagicMock()
        connexion.vendor = "microsoft"
        with mock.patch.object(views_cloture, "connection", connexion):
            self.assertIsNone(views_cloture._entree_courante([
                {"id": "n", "moteur": "sqlite", "base": "n.sqlite3"}
            ]))


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
