"""Tests de l'orchestration annuelle sans accès SQL Server."""
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from apps.core.catalogue_societes import lire_catalogue
from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite


class ClotureAnnuelleSQLiteTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        racine = Path(self.temp.name)
        self.source = racine / "2026.sqlite3"
        self.cible = racine / "2027.sqlite3"
        self.catalogue = racine / "societes.json"
        with sqlite3.connect(self.source) as base:
            for table in ("django_migrations", "auth_user", "core_societe"):
                base.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
            base.execute("CREATE TABLE mouvement (id INTEGER PRIMARY KEY)")
            base.execute("INSERT INTO mouvement VALUES (1)")
        self.catalogue.write_text(json.dumps({"version": 1, "bases": [{
            "id": "n", "societe": "Transport", "agence": "Centre",
            "exercice": "2026", "moteur": "sqlite",
            "base": str(self.source), "cloture": False,
        }]}), encoding="utf-8")

    def initialiser(self, origine, nouvelle):
        for table in ("django_migrations", "auth_user", "core_societe"):
            nouvelle.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
        nouvelle.execute("CREATE TABLE report (montant INTEGER)")

    def reporter(self, origine, nouvelle):
        nouvelle.execute("INSERT INTO report VALUES (120)")

    def test_creation_reports_et_lien_historique_sans_mouvements(self):
        entree = preparer_exercice_sqlite(
            self.catalogue, "n", str(self.cible), "n1",
            self.initialiser, self.reporter,
        )
        self.assertEqual(entree["exercice_precedent"], "n")
        with sqlite3.connect(self.cible) as base:
            self.assertEqual(base.execute("SELECT montant FROM report").fetchone(), (120,))
            self.assertNotIn("mouvement", {
                row[0] for row in base.execute("SELECT name FROM sqlite_master")
            })
        self.assertTrue(lire_catalogue(self.catalogue)[0]["cloture"])

    def test_echec_reports_ne_publie_pas(self):
        def echec(origine, nouvelle):
            raise RuntimeError("échec des reports")
        avant = self.catalogue.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "reports"):
            preparer_exercice_sqlite(
                self.catalogue, "n", str(self.cible), "n1",
                self.initialiser, echec,
            )
        self.assertFalse(self.cible.exists())
        self.assertEqual(self.catalogue.read_bytes(), avant)

    def test_destination_existante_jamais_ecrasee(self):
        self.cible.write_bytes(b"sentinelle")
        with self.assertRaises(FileExistsError):
            preparer_exercice_sqlite(
                self.catalogue, "n", str(self.cible), "n1",
                self.initialiser, self.reporter,
            )
        self.assertEqual(self.cible.read_bytes(), b"sentinelle")

    def test_references_invalides_bloquent_publication(self):
        def initialiser_invalide(origine, nouvelle):
            self.initialiser(origine, nouvelle)
            nouvelle.execute(
                "CREATE TABLE detail (id INTEGER PRIMARY KEY, "
                "societe_id INTEGER REFERENCES core_societe(id))"
            )

        def reporter_invalide(origine, nouvelle):
            nouvelle.execute("INSERT INTO detail VALUES (1, 999)")

        avant = self.catalogue.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):
            preparer_exercice_sqlite(
                self.catalogue, "n", str(self.cible), "n1",
                initialiser_invalide, reporter_invalide,
            )
        self.assertFalse(self.cible.exists())
        self.assertEqual(self.catalogue.read_bytes(), avant)

    def test_reports_voient_configuration_non_encore_validee(self):
        def initialiser_config(origine, nouvelle):
            self.initialiser(origine, nouvelle)
            nouvelle.execute("CREATE TABLE configuration (valeur TEXT)")
            nouvelle.execute("INSERT INTO configuration VALUES ('active')")

        def reporter_config(origine, nouvelle):
            self.assertEqual(
                nouvelle.execute("SELECT valeur FROM configuration").fetchone(),
                ("active",),
            )
            nouvelle.execute("INSERT INTO report VALUES (250)")

        preparer_exercice_sqlite(
            self.catalogue, "n", str(self.cible), "n1",
            initialiser_config, reporter_config,
        )
        with sqlite3.connect(self.cible) as base:
            self.assertEqual(base.execute("SELECT montant FROM report").fetchone(), (250,))
