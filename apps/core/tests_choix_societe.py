"""Tests HTTP de l'écran de sélection multi-sociétés."""
import json
import tempfile
from pathlib import Path
from unittest import mock
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ChoixSocieteTests(TestCase):
    def setUp(self):
        self.url = reverse("core:choix_societe")
        self.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok")

    def test_authentification_et_autorisation(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        autre = get_user_model().objects.create_user("agent", "", "Agent-2026-ok")
        self.client.force_login(autre)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_filtre_exercices_et_aucune_credential_affichee(self):
        self.client.force_login(self.admin)
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "catalogue.json"
            chemin.write_text(json.dumps({"version": 1, "bases": [
                {"id": "a", "societe": "Transports Alpha", "agence": "Yaoundé", "exercice": "2026",
                 "moteur": "sqlite", "base": "/secret/base.sqlite3", "cloture": False},
                {"id": "b", "societe": "Transports Alpha", "agence": "Yaoundé", "exercice": "2025",
                 "moteur": "sqlite", "base": "/secret/ancienne.sqlite3", "cloture": True}
            ]}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"ERP_CATALOGUE_SOCIETES": str(chemin)}):
                page = self.client.get(self.url)
                self.assertContains(page, "Transports Alpha")
                self.assertContains(page, "2026")
                self.assertNotContains(page, "2025")
                self.assertNotContains(page, "/secret/")
                self.assertContains(self.client.get(self.url + "?clotures=1"), "2025")
                self.assertContains(self.client.get(self.url + "?q=yaound"), "Transports Alpha")
                self.assertContains(self.client.get(self.url + "?q=2025"), "Aucun exercice")
