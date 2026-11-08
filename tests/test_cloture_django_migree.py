"""Véritable parcours N -> N+1 sur les migrations Django de production.

Exécuté indépendamment du backend SQL Server de la CI : chaque dossier annuel
est un fichier SQLite migré par manage.py, sans schéma de test artificiel.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from apps.core.adaptateur_cloture_transport_sqlite import (
    migrer_schema_django_sqlite, preparer_dossier_transport_sqlite,
)
from apps.core.catalogue_societes import lire_catalogue


RACINE = Path(__file__).resolve().parents[1]
SEED = """
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User, Group, Permission
from apps.core.models import Societe, Exercice, Agence
from apps.comptabilite.models import Compte, Journal, Ecriture, LigneEcriture
from apps.transport.models import Gare, Ligne, ArretLigne, Vehicule, Chauffeur, ChangementGamme
from apps.commercial.models import Tiers
Societe.objects.create(raison_sociale='Transport Centrale', activite='TRANSPORT')
Exercice.objects.create(code='2026', date_debut=date(2026,1,1), date_fin=date(2026,12,31))
User.objects.create_user(username='controle', password='test-local-only')
groupe = Group.objects.create(name='Guichet')
User.objects.get(username='controle').groups.add(groupe)
permission = Permission.objects.get(codename='view_user', content_type__app_label='auth')
groupe.permissions.add(permission)
User.objects.get(username='controle').user_permissions.add(permission)
g1 = Gare.objects.create(code='YDE', nom='Yaoundé', ville='Yaoundé')
g2 = Gare.objects.create(code='DLA', nom='Douala', ville='Douala')
pv = Gare.objects.create(code='PVY', nom='Point de vente', ville='Yaoundé', type_gare='POINT_VENTE', rattachement=g1)
ligne = Ligne.objects.create(code='YDE-DLA', gare_depart=g1, gare_arrivee=g2, prix_billet=5000)
ArretLigne.objects.create(ligne=ligne, gare=pv, ordre=1)
proprietaire = Tiers.objects.create(code='PROP-01', nom='Propriétaire contrôle', type_tiers='FOURNISSEUR')
vehicule = Vehicule.objects.create(immatriculation='CE-123-AA', nombre_places=40, gamme='CLASSIQUE', proprietaire=proprietaire)
ChangementGamme.objects.create(vehicule=vehicule, gamme='CLASSIQUE', debut=date(2026,1,1))
Chauffeur.objects.create(nom='Chauffeur de contrôle', permis='TEST-2026')
c1 = Compte.objects.create(numero='411000', intitule='Clients')
c2 = Compte.objects.create(numero='101000', intitule='Capital')
Agence.objects.create(code='CTR', nom='Agence Centre', ville='Yaoundé', locale=True, compte_liaison=c2)
Journal.objects.create(code='AN', intitule='A nouveaux', type_journal='AN', cloture_au=date(2026,12,31))
j = Journal.objects.create(code='OD', intitule='Divers', type_journal='OD')
e = Ecriture.objects.create(journal=j, exercice=Exercice.objects.get(code='2026'),
    numero='OD-2026-1', date=date(2026,12,31), libelle='Balance de clôture', statut='VALIDEE')
LigneEcriture.objects.create(ecriture=e, compte=c1, tiers=proprietaire, section=g1.section, vehicule=vehicule, debit=Decimal('125.50'))
LigneEcriture.objects.create(ecriture=e, compte=c2, credit=Decimal('125.50'))
"""


class ClotureDjangoMigreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # La source Django migrée et peuplée est immuable : la préparer une
        # seule fois, puis isoler chaque scénario dans sa propre copie SQLite.
        # Chaque N+1 continue d'être migrée réellement par le code métier.
        cls._fixture_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._fixture_temp.cleanup)
        cls._fixture_source = Path(cls._fixture_temp.name) / 'source.sqlite3'
        cls._fixture_source.touch()
        with sqlite3.connect(cls._fixture_source) as db:
            migrer_schema_django_sqlite(db)
        env = os.environ.copy()
        env.pop('DATABASE_URL', None)
        env.update(DB_ENGINE='sqlite', SQLITE_FICHIER=str(cls._fixture_source),
                   MIROIR_DB_ENGINE='', ERP_ASSISTANT='0',
                   ERP_LICENCE='0', RELAIS_ACTIF='0')
        proc = subprocess.run(
            [sys.executable, str(RACINE / 'manage.py'), 'shell', '-c', SEED],
            cwd=RACINE, env=env, capture_output=True, text=True, timeout=120,
        )
        if proc.returncode:
            raise RuntimeError(proc.stdout + proc.stderr)

    def _copier_source(self, chemin):
        shutil.copy2(self._fixture_source, chemin)

    def test_cloture_migrations_reelles_et_balance(self):
        with tempfile.TemporaryDirectory() as temporaire:
            dossier = Path(temporaire)
            ancien, nouveau = dossier / 'n.sqlite3', dossier / 'n1.sqlite3'
            catalogue = dossier / 'catalogue.json'
            self._copier_source(ancien)
            catalogue.write_text(json.dumps({'version': 1, 'bases': [{
                'id': 'n', 'societe': 'Transport Centrale', 'agence': 'Centre',
                'exercice': '2026', 'moteur': 'sqlite', 'base': str(ancien),
                'cloture': False,
            }]}), encoding='utf-8')
            resultat = preparer_dossier_transport_sqlite(
                catalogue, 'n', nouveau, 'n1', 2027,
            )
            self.assertEqual(resultat['exercice_precedent'], 'n')
            self.assertTrue(next(b for b in lire_catalogue(catalogue) if b['id'] == 'n')['cloture'])
            with sqlite3.connect(ancien) as source_db:
                historique_source = source_db.execute('''SELECT gamme, debut FROM transport_changementgamme ORDER BY id''').fetchall()
            with sqlite3.connect(nouveau) as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(db.execute('SELECT code FROM core_exercice').fetchone()[0], '2027')
                self.assertEqual(db.execute('SELECT username FROM auth_user').fetchone()[0], 'controle')
                self.assertEqual(db.execute('SELECT name FROM auth_group').fetchone()[0], 'Guichet')
                self.assertEqual(db.execute("""SELECT u.username, g.name FROM auth_user_groups AS ug
                    JOIN auth_user AS u ON ug.user_id=u.id
                    JOIN auth_group AS g ON ug.group_id=g.id""").fetchall(), [('controle', 'Guichet')])
                self.assertEqual(db.execute('SELECT cloture_au FROM comptabilite_journal WHERE code="AN"').fetchone()[0], None)
                self.assertEqual(db.execute("""SELECT COUNT(*) FROM auth_user_user_permissions AS up
                    JOIN auth_permission AS p ON p.id=up.permission_id
                    JOIN auth_user AS u ON u.id=up.user_id
                    WHERE u.username='controle' AND p.codename='view_user'""").fetchone()[0], 1)
                self.assertEqual(db.execute("""SELECT COUNT(*) FROM auth_group_permissions AS gp
                    JOIN auth_permission AS p ON p.id=gp.permission_id
                    JOIN auth_group AS g ON g.id=gp.group_id
                    WHERE g.name='Guichet' AND p.codename='view_user'""").fetchone()[0], 1)
                self.assertEqual(db.execute("""SELECT c.numero FROM core_agence AS a
                    JOIN comptabilite_compte AS c ON c.id=a.compte_liaison_id
                    WHERE a.code='CTR'""").fetchone()[0], '101000')
                self.assertEqual(db.execute("SELECT code, nom, ville, locale, compte_liaison_id IS NOT NULL FROM core_agence").fetchall(), [('CTR', 'Agence Centre', 'Yaoundé', 1, 1)])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_gare').fetchone()[0], 3)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_ligne').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_vehicule').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_chauffeur').fetchone()[0], 1)
                self.assertEqual(db.execute('''SELECT gamme, debut FROM transport_changementgamme ORDER BY id''').fetchall(), historique_source)
                self.assertEqual(db.execute("""SELECT tiers.code FROM transport_vehicule AS veh
                    JOIN commercial_tiers AS tiers ON veh.proprietaire_id=tiers.id
                    WHERE veh.immatriculation='CE-123-AA'""").fetchone()[0], 'PROP-01')
                self.assertIn(('CLASSIQUE', '2026-01-01'), db.execute("""SELECT historique.gamme, historique.debut
                    FROM transport_changementgamme AS historique
                    JOIN transport_vehicule AS veh ON historique.vehicule_id=veh.id
                    WHERE veh.immatriculation='CE-123-AA'""").fetchall())
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_arretligne').fetchone()[0], 1)
                self.assertEqual(db.execute("""SELECT ligne.code, gare.code, arret.ordre
                    FROM transport_arretligne AS arret
                    JOIN transport_ligne AS ligne ON ligne.id=arret.ligne_id
                    JOIN transport_gare AS gare ON gare.id=arret.gare_id""").fetchall(),
                    [('YDE-DLA', 'PVY', 1)])
                self.assertEqual(db.execute("""SELECT section.code FROM transport_gare AS gare
                    JOIN comptabilite_sectionanalytique AS section ON section.id=gare.section_id
                    WHERE gare.code='YDE'""").fetchone()[0], 'G-YDE')
                self.assertEqual(db.execute("""SELECT parent.code FROM transport_gare AS point
                    JOIN transport_gare AS parent ON point.rattachement_id=parent.id
                    WHERE point.code='PVY'""").fetchone()[0], 'YDE')
                self.assertEqual(db.execute("""SELECT depart.code, arrivee.code FROM transport_ligne AS ligne
                    JOIN transport_gare AS depart ON ligne.gare_depart_id=depart.id
                    JOIN transport_gare AS arrivee ON ligne.gare_arrivee_id=arrivee.id
                    WHERE ligne.code='YDE-DLA'""").fetchone(), ('YDE', 'DLA'))
                # N+1 conserve les référentiels, jamais les mouvements de N.
                # Les écritures copiées doivent être uniquement les à-nouveaux.
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM comptabilite_ecriture WHERE origine='CLOTURE_ANNUELLE'"
                ).fetchone()[0], 1)
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM comptabilite_ecriture WHERE numero='OD-2026-1'"
                ).fetchone()[0], 0)
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM comptabilite_ecriture WHERE exercice_id NOT IN "
                    "(SELECT id FROM core_exercice)"
                ).fetchone()[0], 0)
                self.assertEqual(db.execute(
                    "SELECT code FROM comptabilite_journal ORDER BY code"
                ).fetchall(), [('AN',), ('OD',)])
                self.assertEqual(db.execute(
                    "SELECT numero FROM comptabilite_compte ORDER BY numero"
                ).fetchall(), [('101000',), ('411000',)])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM comptabilite_ecriture').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT date FROM comptabilite_ecriture').fetchone()[0], '2027-01-01')
                montants = db.execute('SELECT debit,credit FROM comptabilite_ligneecriture ORDER BY compte_id').fetchall()
                self.assertEqual(sum(Decimal(str(d)) for d, _ in montants),
                                 sum(Decimal(str(c)) for _, c in montants))
                self.assertEqual(sum(Decimal(str(d)) for d, _ in montants), Decimal('125.50'))
                # Les axes comptables de bilan doivent survivre à la reprise AN,
                # pas seulement le total débit/crédit.
                axes = db.execute("""SELECT t.code, s.code, v.immatriculation
                    FROM comptabilite_ligneecriture AS l
                    JOIN comptabilite_compte AS c ON c.id=l.compte_id
                    LEFT JOIN commercial_tiers AS t ON t.id=l.tiers_id
                    LEFT JOIN comptabilite_sectionanalytique AS s ON s.id=l.section_id
                    LEFT JOIN transport_vehicule AS v ON v.id=l.vehicule_id
                    WHERE c.numero='411000'""").fetchone()
                self.assertEqual(axes, ('PROP-01', 'G-YDE', 'CE-123-AA'))
                self.assertEqual(db.execute("""SELECT COUNT(*) FROM comptabilite_ligneecriture
                    WHERE tiers_id IS NOT NULL AND section_id IS NOT NULL
                      AND vehicule_id IS NOT NULL""").fetchone()[0], 1)
            # N reste intact et N+1 doit conserver le lien de provenance.
            entrees = {b['id']: b for b in lire_catalogue(catalogue)}
            self.assertEqual(set(entrees), {'n', 'n1'})
            self.assertTrue(entrees['n']['cloture'])
            self.assertEqual(str(entrees['n']['exercice']), '2026')
            self.assertEqual(str(entrees['n1']['exercice']), '2027')
            self.assertEqual(entrees['n1']['exercice_precedent'], 'n')
            self.assertEqual(entrees['n1']['societe'], entrees['n']['societe'])
            self.assertEqual(entrees['n1']['agence'], entrees['n']['agence'])
            self.assertEqual(Path(entrees['n1']['base']).resolve(), nouveau.resolve())
            self.assertFalse(entrees['n1']['cloture'])
            with sqlite3.connect(ancien) as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM comptabilite_ecriture').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT date FROM comptabilite_ecriture').fetchone()[0], '2026-12-31')
                self.assertEqual(db.execute('SELECT code FROM core_exercice').fetchone()[0], '2026')
                self.assertEqual(db.execute('SELECT cloture_au FROM comptabilite_journal WHERE code="AN"').fetchone()[0], '2026-12-31')


    def test_echec_balance_ne_publie_pas_n_plus_un(self):
        """Une pièce validée déséquilibrée doit laisser N et le catalogue intacts."""
        with tempfile.TemporaryDirectory() as temporaire:
            dossier = Path(temporaire)
            ancien, nouveau = dossier / 'n.sqlite3', dossier / 'n1.sqlite3'
            catalogue = dossier / 'catalogue.json'
            self._copier_source(ancien)
            # Dégrader volontairement une pièce validée, sans désactiver les FK.
            with sqlite3.connect(ancien) as db:
                db.execute("""UPDATE comptabilite_ligneecriture
                              SET credit='124.50' WHERE credit>0""")
                db.commit()
            original = {'version': 1, 'bases': [{
                'id': 'n', 'societe': 'Transport Centrale', 'agence': 'Centre',
                'exercice': '2026', 'moteur': 'sqlite', 'base': str(ancien),
                'cloture': False,
            }]}
            catalogue.write_text(json.dumps(original), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'pièce validée déséquilibrée'):
                preparer_dossier_transport_sqlite(catalogue, 'n', nouveau, 'n1', 2027)
            self.assertFalse(nouveau.exists(), 'la base N+1 échouée doit être supprimée')
            self.assertEqual(json.loads(catalogue.read_text(encoding='utf-8')), original)
            with sqlite3.connect(ancien) as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(db.execute(
                    'SELECT credit FROM comptabilite_ligneecriture WHERE credit>0'
                ).fetchone()[0], 124.5)
                self.assertEqual(db.execute('SELECT code FROM core_exercice').fetchone()[0], '2026')


if __name__ == '__main__':
    unittest.main()
