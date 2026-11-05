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

    def test_dependances_copie_parent_avant_enfant(self):
        for db in (self.source, self.cible):
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY)')
            db.execute('CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
        self.source.execute('INSERT INTO parent VALUES (1)')
        self.source.execute('INSERT INTO enfant VALUES (2, 1)')
        recopier_referentiels(self.source, self.cible, ['enfant', 'parent'])
        self.assertEqual(self.cible.execute('SELECT * FROM enfant').fetchall(), [(2, 1)])

    def test_dependances_circulaires_refusees_avant_copie(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY, enfant_id INTEGER REFERENCES enfant(id))')
            db.execute('CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
        self.source.execute('INSERT INTO parent VALUES (1, NULL)')
        with self.assertRaisesRegex(ValueError, 'circulaires'):
            recopier_referentiels(self.source, self.cible, ['parent', 'enfant'])
        self.assertEqual(self.cible.execute('SELECT * FROM parent').fetchall(), [])

    def test_refus_cible_fk_modifiee_avant_toute_copie(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY)')
            db.execute('CREATE TABLE autre (id INTEGER PRIMARY KEY)')
        self.source.execute(
            'CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))'
        )
        self.cible.execute(
            'CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES autre(id))'
        )
        with self.assertRaisesRegex(ValueError, 'clés étrangères'):
            recopier_referentiels(self.source, self.cible, ['referentiel', 'enfant'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])

    def test_erreur_insertion_annule_toutes_les_tables(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE autre (id INTEGER PRIMARY KEY, valeur TEXT)')
        self.source.execute("INSERT INTO autre VALUES (1, 'ok')")
        self.source.execute("INSERT INTO autre VALUES (2, 'erreur')")
        self.cible.execute("""
            CREATE TRIGGER rejeter_seconde_ligne BEFORE INSERT ON autre
            WHEN NEW.id = 2 BEGIN SELECT RAISE(ABORT, 'insertion refusee'); END
        """)
        with self.assertRaises(sqlite3.IntegrityError):
            recopier_referentiels(self.source, self.cible, ['referentiel', 'autre'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])
        self.assertEqual(self.cible.execute('SELECT * FROM autre').fetchall(), [])

    def test_contrainte_unique_absente_refusee_avant_copie(self):
        self.source.execute('CREATE UNIQUE INDEX ref_nom_unique ON referentiel(nom)')
        with self.assertRaisesRegex(ValueError, 'contraintes uniques'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])

    def test_contrainte_unique_equivalente_acceptee(self):
        self.source.execute('CREATE UNIQUE INDEX source_nom_unique ON referentiel(nom)')
        self.cible.execute('CREATE UNIQUE INDEX cible_nom_unique ON referentiel(nom)')
        recopier_referentiels(self.source, self.cible, ['referentiel'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [(1, 'A')])

    def test_index_unique_partiel_refuse_avant_copie(self):
        self.source.execute('CREATE UNIQUE INDEX unique_partiel ON referentiel(nom) WHERE id > 0')
        with self.assertRaisesRegex(ValueError, 'complexes'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])

    def test_index_unique_expression_refuse_avant_copie(self):
        self.source.execute('CREATE UNIQUE INDEX unique_expression ON referentiel(lower(nom))')
        with self.assertRaisesRegex(ValueError, 'complexes'):
            recopier_referentiels(self.source, self.cible, ['referentiel'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])

    def test_fk_invalide_controle_desactive_annule_toutes_les_tables(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY)')
            db.execute('CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
            db.execute('PRAGMA foreign_keys=OFF')
        self.source.execute('INSERT INTO enfant VALUES (2, 999)')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'références étrangères invalides'):
            recopier_referentiels(self.source, self.cible, ['referentiel', 'enfant'])
        self.assertEqual(self.cible.execute('SELECT * FROM referentiel').fetchall(), [])
        self.assertEqual(self.cible.execute('SELECT * FROM enfant').fetchall(), [])

    def test_fk_valide_controle_desactive_accepte(self):
        for db in (self.source, self.cible):
            db.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY)')
            db.execute('CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
            db.execute('PRAGMA foreign_keys=OFF')
        self.source.execute('INSERT INTO parent VALUES (7)')
        self.source.execute('INSERT INTO enfant VALUES (8, 7)')
        recopier_referentiels(self.source, self.cible, ['enfant', 'parent'])
        self.assertEqual(self.cible.execute('SELECT * FROM enfant').fetchall(), [(8, 7)])
        self.assertEqual(self.cible.execute('PRAGMA foreign_key_check').fetchall(), [])
