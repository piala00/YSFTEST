"""Régression : la validation du catalogue ferme ses connexions SQLite."""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.core.catalogue_societes import verifier_base_sqlite


class ConnexionTracee:
    def __init__(self, connexion):
        self.connexion = connexion
        self.fermee = False

    def execute(self, *args, **kwargs):
        return self.connexion.execute(*args, **kwargs)

    def close(self):
        self.fermee = True
        self.connexion.close()


class FermetureCatalogueTests(unittest.TestCase):
    def test_connexion_fermee_apres_validation_et_rejet(self):
        connect_reel = sqlite3.connect
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "erp.sqlite3"
            with closing(connect_reel(chemin)) as db:
                for table in ("django_migrations", "auth_user", "core_societe"):
                    db.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
            connexions = []

            def connecter(*args, **kwargs):
                connexion = ConnexionTracee(connect_reel(*args, **kwargs))
                connexions.append(connexion)
                return connexion

            with patch("sqlite3.connect", side_effect=connecter):
                self.assertEqual(verifier_base_sqlite(str(chemin)), str(chemin.resolve()))
                with closing(connect_reel(chemin)) as db:
                    db.execute("DROP TABLE core_societe")
                with self.assertRaisesRegex(ValueError, "compatible"):
                    verifier_base_sqlite(str(chemin))

            self.assertEqual(len(connexions), 2)
            self.assertTrue(all(c.fermee for c in connexions))


if __name__ == "__main__":
    unittest.main()
