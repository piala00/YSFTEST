"""Régression : publication directe N+1 et alias de base physique."""
import json
import os
import tempfile
from pathlib import Path
from django.test import SimpleTestCase

from apps.core.catalogue_societes import enregistrer_exercice_suivant


class PublicationDirecteAliasTests(SimpleTestCase):
    def test_chemin_equivalent_refuse_sans_modifier_catalogue(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            base = racine / "societe_2026.sqlite3"
            base.touch()
            catalogue = racine / "catalogue.json"
            initial = {"version": 1, "bases": [{
                "id": "soc-2026", "societe": "Transport", "agence": "Centre",
                "exercice": "2026", "moteur": "sqlite",
                "base": str(base), "cloture": False,
            }]}
            catalogue.write_text(json.dumps(initial), encoding="utf-8")
            avant = catalogue.read_bytes()
            with self.assertRaisesRegex(ValueError, "base physique déjà enregistrée"):
                enregistrer_exercice_suivant(
                    catalogue, "soc-2026",
                    str(racine / "." / "societe_2026.sqlite3"), "soc-2027")
            self.assertEqual(catalogue.read_bytes(), avant)

    def test_lien_physique_refuse_sans_modifier_catalogue(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            base = racine / "2026.sqlite3"
            alias = racine / "2027.sqlite3"
            base.touch()
            try:
                os.link(base, alias)
            except OSError:
                self.skipTest("liens physiques non disponibles")
            catalogue = racine / "catalogue.json"
            catalogue.write_text(json.dumps({"version": 1, "bases": [{
                "id": "soc-2026", "societe": "Transport", "agence": "Centre",
                "exercice": "2026", "moteur": "sqlite",
                "base": str(base), "cloture": False,
            }]}), encoding="utf-8")
            avant = catalogue.read_bytes()
            with self.assertRaisesRegex(ValueError, "base physique déjà enregistrée"):
                enregistrer_exercice_suivant(catalogue, "soc-2026", str(alias), "soc-2027")
            self.assertEqual(catalogue.read_bytes(), avant)
