"""Contrôles du catalogue de bases, sans modification des bases existantes."""
import json
import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from apps.core.catalogue_societes import lire_catalogue, regrouper


class CatalogueSocietesTests(SimpleTestCase):
    def setUp(self):
        self.bases = [
            {"id": "a", "societe": "Transport A", "agence": "Yaoundé", "exercice": "2026", "moteur": "sqlite", "base": "a.sqlite3", "cloture": False},
            {"id": "b", "societe": "Transport A", "agence": "Yaoundé", "exercice": "2025", "moteur": "sqlite", "base": "b.sqlite3", "cloture": True},
            {"id": "c", "societe": "Transport B", "agence": "Douala", "exercice": "2026", "moteur": "mssql", "base": "ERP_B", "cloture": False},
        ]

    def test_regroupement_et_cloture(self):
        self.assertEqual([g["societe"] for g in regrouper(self.bases)], ["Transport A", "Transport B"])
        self.assertEqual([b["id"] for b in regrouper(self.bases)[0]["agences"][0]["exercices"]], ["a"])
        self.assertEqual([b["id"] for b in regrouper(self.bases, afficher_clotures=True)[0]["agences"][0]["exercices"]], ["a", "b"])

    def test_recherche(self):
        self.assertEqual([g["societe"] for g in regrouper(self.bases, "DOUALA")], ["Transport B"])
        self.assertEqual(regrouper(self.bases, "2025"), [])
        self.assertEqual(len(regrouper(self.bases, "2025", afficher_clotures=True)), 1)

    def test_lecture_et_validation(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            self.assertEqual(lire_catalogue(fichier), [])
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases}), encoding="utf-8")
            self.assertEqual(len(lire_catalogue(fichier)), 3)
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases * 2}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dupliqué"):
                lire_catalogue(fichier)
