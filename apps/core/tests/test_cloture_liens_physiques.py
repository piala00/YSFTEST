"""Regression: a hard link is not a separate annual database."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from apps.core.catalogue_societes import publier_exercice_sqlite_valide, lire_catalogue


class TestAnnualHardLink(unittest.TestCase):
    def test_hard_link_cannot_be_published_as_new_year(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "2026.sqlite3"
            alias = root / "2027.sqlite3"
            with sqlite3.connect(original) as db:
                for table in ("django_migrations", "auth_user", "core_societe"):
                    db.execute(f'CREATE TABLE "{table}" (id integer primary key)')
            try:
                os.link(original, alias)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Hard links unavailable: {exc}")
            catalogue = root / "societes.json"
            catalogue.write_text(json.dumps({"version": 1, "bases": [{
                "id": "s_2026", "societe": "S", "agence": "A",
                "exercice": "2026", "moteur": "sqlite",
                "base": str(original), "cloture": False,
            }]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "base physique déjà enregistrée"):
                publier_exercice_sqlite_valide(catalogue, "s_2026", str(alias), "s_2027")
            bases = lire_catalogue(catalogue)
            self.assertEqual(len(bases), 1)
            self.assertFalse(bases[0]["cloture"])
