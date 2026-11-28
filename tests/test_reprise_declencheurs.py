"""Protection de la reprise des référentiels contre les effets de bord SQL."""
import sqlite3
import unittest

from apps.core.reprise_configuration_sqlite import recopier_referentiels


class RepriseDeclencheursTests(unittest.TestCase):
    def test_refuse_trigger_qui_copierait_des_mouvements(self):
        source = sqlite3.connect(":memory:")
        cible = sqlite3.connect(":memory:")
        self.addCleanup(source.close)
        self.addCleanup(cible.close)
        for db in (source, cible):
            db.execute("CREATE TABLE tiers (id INTEGER PRIMARY KEY, nom TEXT)")
            db.execute("CREATE TABLE mouvements (id INTEGER PRIMARY KEY, tiers_id INTEGER)")
        source.execute("INSERT INTO tiers VALUES (1, 'Client')")
        cible.execute("""CREATE TRIGGER mouvement_indirect AFTER INSERT ON tiers
                         BEGIN INSERT INTO mouvements(tiers_id) VALUES (NEW.id); END""")
        with self.assertRaisesRegex(ValueError, "déclencheur"):
            recopier_referentiels(source, cible, ["tiers"])
        self.assertEqual(cible.execute("SELECT count(*) FROM tiers").fetchone()[0], 0)
        self.assertEqual(cible.execute("SELECT count(*) FROM mouvements").fetchone()[0], 0)

    def test_reprise_sans_trigger_conserve_les_mouvements_vides(self):
        source = sqlite3.connect(":memory:")
        cible = sqlite3.connect(":memory:")
        self.addCleanup(source.close)
        self.addCleanup(cible.close)
        for db in (source, cible):
            db.execute("CREATE TABLE tiers (id INTEGER PRIMARY KEY, nom TEXT)")
            db.execute("CREATE TABLE mouvements (id INTEGER PRIMARY KEY, tiers_id INTEGER)")
        source.execute("INSERT INTO tiers VALUES (1, 'Client')")
        recopier_referentiels(source, cible, ["tiers"])
        self.assertEqual(cible.execute("SELECT nom FROM tiers").fetchone()[0], "Client")
        self.assertEqual(cible.execute("SELECT count(*) FROM mouvements").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
