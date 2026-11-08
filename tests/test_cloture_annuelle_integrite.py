"""Tests d'intégrité de la création de la base annuelle N+1."""
import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite


class ClotureAnnuelleIntegriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        dossier = Path(self.tmp.name)
        self.n = dossier / "2026.sqlite3"
        self.n1 = dossier / "2027.sqlite3"
        self.catalogue = dossier / "societes.json"
        with closing(sqlite3.connect(self.n)) as db, db:
            db.execute("CREATE TABLE django_migrations (id INTEGER PRIMARY KEY)")
            db.execute("CREATE TABLE auth_user (id INTEGER PRIMARY KEY)")
            db.execute("CREATE TABLE core_societe (id INTEGER PRIMARY KEY)")
            db.execute("CREATE TABLE balance (compte TEXT PRIMARY KEY, solde INTEGER NOT NULL)")
            db.execute("INSERT INTO balance VALUES ('411', 12500)")
        self.catalogue.write_text(json.dumps({"version": 1, "bases": [{
            "id": "transport-2026", "societe": "Transport", "agence": "Siege",
            "exercice": "2026", "moteur": "sqlite", "base": str(self.n),
            "cloture": False,
        }]}), encoding="utf-8")

    @staticmethod
    def initialiser(source, cible):
        for table in ("django_migrations", "auth_user", "core_societe"):
            cible.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
        cible.execute("CREATE TABLE report (compte TEXT PRIMARY KEY, solde INTEGER NOT NULL)")

    def test_cloture_valide_publie_lien_et_report_sans_copier_mouvements(self):
        def reporter(source, cible):
            cible.executemany("INSERT INTO report VALUES (?, ?)",
                              source.execute("SELECT compte, solde FROM balance"))

        resultat = preparer_exercice_sqlite(
            self.catalogue, "transport-2026", self.n1,
            "transport-2027", self.initialiser, reporter)
        self.assertEqual(resultat["exercice_precedent"], "transport-2026")
        self.assertEqual(resultat["exercice"], "2027")
        with closing(sqlite3.connect(self.n1)) as db, db:
            self.assertEqual(db.execute("SELECT * FROM report").fetchall(), [("411", 12500)])
            self.assertIsNone(db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='balance'").fetchone())
        bases = json.loads(self.catalogue.read_text(encoding="utf-8"))["bases"]
        self.assertEqual(len(bases), 2)
        self.assertTrue(bases[0]["cloture"])
        self.assertFalse(bases[1]["cloture"])
        self.assertEqual(bases[1]["exercice_precedent"], bases[0]["id"])

    def test_reference_invalide_annule_creation_et_catalogue(self):
        def initialiser(source, cible):
            self.initialiser(source, cible)
            cible.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            cible.execute("CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))")

        def reporter(source, cible):
            cible.execute("INSERT INTO enfant VALUES (1, 999)")

        with self.assertRaises(sqlite3.IntegrityError):
            preparer_exercice_sqlite(self.catalogue, "transport-2026", self.n1,
                                     "transport-2027", initialiser, reporter)
        self.assertFalse(self.n1.exists())
        bases = json.loads(self.catalogue.read_text(encoding="utf-8"))["bases"]
        self.assertEqual(len(bases), 1)
        self.assertFalse(bases[0]["cloture"])


if __name__ == "__main__":
    unittest.main()
