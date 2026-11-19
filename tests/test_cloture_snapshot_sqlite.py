"""Régression : la clôture lit un instantané unique malgré une écriture concurrente.

Test SQLite réel, indépendant des migrations Django (couvertes séparément).
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite


class SnapshotClotureTests(unittest.TestCase):
    def test_ecriture_concurrente_ne_modifie_pas_les_reports(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            source = racine / "n.sqlite3"
            cible = racine / "n1.sqlite3"
            with sqlite3.connect(source) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("CREATE TABLE soldes (montant INTEGER NOT NULL)")
                db.execute("INSERT INTO soldes VALUES (100)")

            valeurs = {}

            def initialiser(origine, nouvelle):
                valeurs["referentiel"] = origine.execute(
                    "SELECT montant FROM soldes"
                ).fetchone()[0]
                nouvelle.execute("CREATE TABLE ouverture (montant INTEGER)")
                # WAL autorise un écrivain pendant le snapshot lecteur.
                with sqlite3.connect(source, timeout=2) as concurrent:
                    concurrent.execute("UPDATE soldes SET montant=200")

            def reporter(origine, nouvelle):
                valeurs["report"] = origine.execute(
                    "SELECT montant FROM soldes"
                ).fetchone()[0]
                nouvelle.execute("INSERT INTO ouverture VALUES (?)",
                                 (valeurs["report"],))

            catalogue = [{"id": "n", "moteur": "sqlite",
                          "cloture": False, "base": str(source)}]
            with patch("apps.core.cloture_annuelle_sqlite.lire_catalogue",
                       return_value=catalogue), patch(
                "apps.core.cloture_annuelle_sqlite.verifier_base_sqlite",
                side_effect=lambda chemin: chemin
            ), patch(
                "apps.core.cloture_annuelle_sqlite.publier_exercice_sqlite_valide",
                return_value={"id": "n1"}
            ) as publier:
                resultat = preparer_exercice_sqlite(
                    racine / "catalogue.json", "n", cible, "n1",
                    initialiser, reporter,
                )

            self.assertEqual(resultat, {"id": "n1"})
            self.assertEqual(valeurs, {"referentiel": 100, "report": 100})
            with sqlite3.connect(source) as db:
                self.assertEqual(db.execute(
                    "SELECT montant FROM soldes").fetchone()[0], 200)
            with sqlite3.connect(cible) as db:
                self.assertEqual(db.execute(
                    "SELECT montant FROM ouverture").fetchone()[0], 100)
            publier.assert_called_once()


if __name__ == "__main__":
    unittest.main()
