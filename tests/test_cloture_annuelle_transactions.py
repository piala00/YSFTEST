"""Régressions de clôture : pas de publication après échec des callbacks."""
import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite


class ClotureTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dossier = Path(self.temp.name)
        self.source = self.dossier / '2026.sqlite3'
        self.cible = self.dossier / '2027.sqlite3'
        self.catalogue = self.dossier / 'societes.json'
        with closing(sqlite3.connect(self.source)) as db, db:
            for table in ('django_migrations', 'auth_user', 'core_societe'):
                db.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)')
        self.catalogue.write_text(json.dumps({'version': 1, 'bases': [{
            'id': 'annee2026', 'societe': 'Transport', 'agence': 'Siege',
            'exercice': '2026', 'moteur': 'sqlite', 'base': str(self.source),
            'cloture': False,
        }]}), encoding='utf-8')

    @staticmethod
    def initialiser(source, destination):
        destination.execute('CREATE TABLE report (montant INTEGER NOT NULL)')
        destination.execute('CREATE TABLE django_migrations (id INTEGER PRIMARY KEY)')
        destination.execute('CREATE TABLE auth_user (id INTEGER PRIMARY KEY)')
        destination.execute('CREATE TABLE core_societe (id INTEGER PRIMARY KEY)')

    def test_echec_report_annule_base_et_conserve_exercice_ouvert(self):
        def reporter(source, destination):
            destination.execute('INSERT INTO report VALUES (100)')
            raise RuntimeError('échec du report')

        with self.assertRaisesRegex(RuntimeError, 'échec du report'):
            preparer_exercice_sqlite(self.catalogue, 'annee2026', self.cible,
                                     'annee2027', self.initialiser, reporter)
        self.assertFalse(self.cible.exists())
        donnees = json.loads(self.catalogue.read_text(encoding='utf-8'))
        self.assertEqual(len(donnees['bases']), 1)
        self.assertFalse(donnees['bases'][0]['cloture'])

    def test_echec_publication_supprime_base_et_ne_modifie_pas_catalogue(self):
        with patch('apps.core.cloture_annuelle_sqlite.publier_exercice_sqlite_valide',
                   side_effect=RuntimeError('publication impossible')):
            with self.assertRaisesRegex(RuntimeError, 'publication impossible'):
                preparer_exercice_sqlite(self.catalogue, 'annee2026', self.cible,
                                         'annee2027', self.initialiser,
                                         lambda source, destination: destination.execute(
                                             'INSERT INTO report VALUES (200)'))
        self.assertFalse(self.cible.exists())
        self.assertFalse(json.loads(self.catalogue.read_text(encoding='utf-8'))
                         ['bases'][0]['cloture'])


    def test_source_reste_lecture_seule_si_initialisation_tente_une_ecriture(self):
        """Même un callback fautif ne peut pas modifier la base de l'année N."""
        def initialiser_interdit(source, destination):
            self.initialiser(source, destination)
            source.execute('INSERT INTO core_societe(id) VALUES (99)')

        with self.assertRaises(sqlite3.OperationalError):
            preparer_exercice_sqlite(self.catalogue, 'annee2026', self.cible,
                                     'annee2027', initialiser_interdit,
                                     lambda source, destination: None)
        self.assertFalse(self.cible.exists())
        with closing(sqlite3.connect(self.source)) as db, db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM core_societe').fetchone()[0], 0)
        donnees = json.loads(self.catalogue.read_text(encoding='utf-8'))
        self.assertEqual(len(donnees['bases']), 1)
        self.assertFalse(donnees['bases'][0]['cloture'])

if __name__ == '__main__':
    unittest.main()
