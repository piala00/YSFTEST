"""Tests isolés de la copie des référentiels annuels SQLite."""
import sqlite3
import unittest

from apps.core.reprise_configuration_sqlite import recopier_referentiels


class RepriseConfigurationSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.source = sqlite3.connect(':memory:')
        self.cible = sqlite3.connect(':memory:')
        self.addCleanup(self.source.close)
        self.addCleanup(self.cible.close)
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE referentiel (id INTEGER PRIMARY KEY, nom TEXT)')
            db.execute('CREATE TABLE mouvement (id INTEGER PRIMARY KEY)')
        self.source.execute("INSERT INTO referentiel VALUES (1, 'A')")
        self.source.execute('INSERT INTO mouvement VALUES (10)')

    def test_referentiels_uniquement(self):
        recopier_referentiels(self.source, self.cible, ['referentiel'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [(1, 'A')])
        self.assertEqual(self.cible.execute('SELECT * FROM mouvement').fetchall(), [])

    def test_refus_liste_vide_et_doublons(self):
        for tables in ([], ['referentiel', 'referentiel'], ['mauvaise-table']):
            with self.subTest(tables=tables), self.assertRaises(ValueError):
                recopier_referentiels(self.source, self.cible, tables)

    def test_refus_schema_incompatible(self):
        self.cible.execute('ALTER TABLE referentiel ADD COLUMN supplement TEXT')
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])

    def test_refus_table_destination_non_vide(self):
        self.cible.execute("INSERT INTO referentiel VALUES (2, 'B')")
        with self.assertRaisesRegex(ValueError, 'non vide'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])

    def test_prevalidation_ne_copie_rien_si_deuxieme_table_incompatible(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE autre (id INTEGER PRIMARY KEY, nom TEXT)')
        self.cible.execute('ALTER TABLE autre ADD COLUMN supplement TEXT')
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            recopier_referentiels(self.source, self.cible, ['referentiel', 'autre'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])

    def test_types_de_colonnes_incompatibles_refuses(self):
        self.cible.execute('DROP TABLE referentiel')
        self.cible.execute('CREATE TABLE referentiel (id INTEGER PRIMARY KEY, nom INTEGER)')
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])
