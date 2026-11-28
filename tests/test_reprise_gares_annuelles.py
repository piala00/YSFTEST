"""Régression de la reprise des gares et points de vente auto-référencés."""
import sqlite3
import unittest

from apps.core.reprise_configuration_sqlite import recopier_referentiels


class RepriseGaresTests(unittest.TestCase):
    def setUp(self):
        self.source = sqlite3.connect(":memory:")
        self.cible = sqlite3.connect(":memory:")
        for db in (self.source, self.cible):
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("""CREATE TABLE transport_gare (
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                rattachement_id INTEGER REFERENCES transport_gare(id)
            )""")

    def tearDown(self):
        self.source.close()
        self.cible.close()

    def test_enfant_avant_parent_est_repris_avec_integrite(self):
        # L'identifiant enfant précède volontairement celui de son parent.
        self.source.execute("INSERT INTO transport_gare VALUES (20,'SIEGE',NULL)")
        self.source.execute("INSERT INTO transport_gare VALUES (10,'POINT',20)")
        self.source.commit()
        with self.cible:
            self.cible.execute("BEGIN IMMEDIATE")
            recopier_referentiels(self.source, self.cible, ["transport_gare"])
        self.assertEqual(
            self.cible.execute("SELECT id,rattachement_id FROM transport_gare ORDER BY id").fetchall(),
            [(10,20),(20,None)],
        )
        self.assertEqual(self.cible.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_source_invalide_ne_laisse_aucune_ligne(self):
        self.source.execute("PRAGMA foreign_keys=OFF")
        self.source.execute("INSERT INTO transport_gare VALUES (10,'POINT',999)")
        self.source.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.cible:
                self.cible.execute("BEGIN IMMEDIATE")
                recopier_referentiels(self.source, self.cible, ["transport_gare"])
        self.assertEqual(self.cible.execute("SELECT COUNT(*) FROM transport_gare").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
