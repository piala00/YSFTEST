"""Véritable parcours N -> N+1 sur les migrations Django de production.

Exécuté indépendamment du backend SQL Server de la CI : chaque dossier annuel
est un fichier SQLite migré par manage.py, sans schéma de test artificiel.
"""
import json
import os
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
from django.contrib.auth.models import User, Group
from apps.core.models import Societe, Exercice, Agence
from apps.comptabilite.models import Compte, Journal, Ecriture, LigneEcriture
from apps.transport.models import Gare, Ligne, ArretLigne, Vehicule, Chauffeur, ChangementGamme
from apps.commercial.models import Tiers
Societe.objects.create(raison_sociale='Transport Centrale', activite='TRANSPORT')
Exercice.objects.create(code='2026', date_debut=date(2026,1,1), date_fin=date(2026,12,31))
User.objects.create_user(username='controle', password='test-local-only')
Group.objects.create(name='Guichet')
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
Journal.objects.create(code='AN', intitule='A nouveaux', type_journal='AN', cloture_au=date(2026,12,31))
j = Journal.objects.create(code='OD', intitule='Divers', type_journal='OD')
e = Ecriture.objects.create(journal=j, exercice=Exercice.objects.get(code='2026'),
    numero='OD-2026-1', date=date(2026,12,31), libelle='Balance de clôture', statut='VALIDEE')
LigneEcriture.objects.create(ecriture=e, compte=c1, debit=Decimal('125.50'))
LigneEcriture.objects.create(ecriture=e, compte=c2, credit=Decimal('125.50'))
"""


class ClotureDjangoMigreeTests(unittest.TestCase):
    def test_cloture_migrations_reelles_et_balance(self):
        with tempfile.TemporaryDirectory() as temporaire:
            dossier = Path(temporaire)
            ancien, nouveau = dossier / 'n.sqlite3', dossier / 'n1.sqlite3'
            catalogue = dossier / 'catalogue.json'
            ancien.touch()
            with sqlite3.connect(ancien) as db:
                migrer_schema_django_sqlite(db)
            env = os.environ.copy()
            env.pop('DATABASE_URL', None)
            env.update(DB_ENGINE='sqlite', SQLITE_FICHIER=str(ancien),
                       MIROIR_DB_ENGINE='', ERP_ASSISTANT='0',
                       ERP_LICENCE='0', RELAIS_ACTIF='0')
            proc = subprocess.run(
                [sys.executable, str(RACINE / 'manage.py'), 'shell', '-c', SEED],
                cwd=RACINE, env=env, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
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
            with sqlite3.connect(nouveau) as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(db.execute('SELECT code FROM core_exercice').fetchone()[0], '2027')
                self.assertEqual(db.execute('SELECT username FROM auth_user').fetchone()[0], 'controle')
                self.assertEqual(db.execute('SELECT name FROM auth_group').fetchone()[0], 'Guichet')
                self.assertEqual(db.execute('SELECT cloture_au FROM comptabilite_journal WHERE code="AN"').fetchone()[0], None)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_gare').fetchone()[0], 3)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_ligne').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_vehicule').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_chauffeur').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_changementgamme').fetchone()[0], 1)
                self.assertEqual(db.execute("""SELECT tiers.code FROM transport_vehicule AS veh
                    JOIN commercial_tiers AS tiers ON veh.proprietaire_id=tiers.id
                    WHERE veh.immatriculation='CE-123-AA'""").fetchone()[0], 'PROP-01')
                self.assertEqual(db.execute("""SELECT historique.gamme, historique.debut
                    FROM transport_changementgamme AS historique
                    JOIN transport_vehicule AS veh ON historique.vehicule_id=veh.id
                    WHERE veh.immatriculation='CE-123-AA'""").fetchone(), ('CLASSIQUE', '2026-01-01'))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM transport_arretligne').fetchone()[0], 1)
                self.assertEqual(db.execute("""SELECT parent.code FROM transport_gare AS point
                    JOIN transport_gare AS parent ON point.rattachement_id=parent.id
                    WHERE point.code='PVY'""").fetchone()[0], 'YDE')
                self.assertEqual(db.execute("""SELECT depart.code, arrivee.code FROM transport_ligne AS ligne
                    JOIN transport_gare AS depart ON ligne.gare_depart_id=depart.id
                    JOIN transport_gare AS arrivee ON ligne.gare_arrivee_id=arrivee.id
                    WHERE ligne.code='YDE-DLA'""").fetchone(), ('YDE', 'DLA'))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM comptabilite_ecriture').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT date FROM comptabilite_ecriture').fetchone()[0], '2027-01-01')
                montants = db.execute('SELECT debit,credit FROM comptabilite_ligneecriture ORDER BY compte_id').fetchall()
                self.assertEqual(sum(Decimal(str(d)) for d, _ in montants),
                                 sum(Decimal(str(c)) for _, c in montants))
                self.assertEqual(sum(Decimal(str(d)) for d, _ in montants), Decimal('125.50'))
            with sqlite3.connect(ancien) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM comptabilite_ecriture').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
