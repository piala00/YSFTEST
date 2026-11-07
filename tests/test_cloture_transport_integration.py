"""Parcours complet de clôture annuelle : catalogue, référentiels, pièce AN et historique."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.core.adaptateur_cloture_transport_sqlite import preparer_dossier_transport_sqlite
from apps.core.catalogue_societes import lire_catalogue


SCHEMA = """
CREATE TABLE django_migrations (id INTEGER PRIMARY KEY);
CREATE TABLE auth_user (id INTEGER PRIMARY KEY, username TEXT);
CREATE TABLE django_content_type (id INTEGER PRIMARY KEY, app_label TEXT, model TEXT);
CREATE TABLE auth_permission (id INTEGER PRIMARY KEY, name TEXT, content_type_id INTEGER REFERENCES django_content_type(id), codename TEXT);
CREATE TABLE core_societe (id INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE core_exercice (
 id INTEGER PRIMARY KEY, code TEXT, date_debut TEXT, date_fin TEXT, cloture INTEGER
);
CREATE TABLE comptabilite_compte (id INTEGER PRIMARY KEY, numero TEXT UNIQUE);
CREATE TABLE comptabilite_journal (
 id INTEGER PRIMARY KEY, code TEXT, type_journal TEXT, cloture_au TEXT
);
CREATE TABLE commercial_tiers (id INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE comptabilite_sectionanalytique (id INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE transport_vehicule (id INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE comptabilite_ecriture (
 id INTEGER PRIMARY KEY, journal_id INTEGER, exercice_id INTEGER, numero TEXT,
 date TEXT, libelle TEXT, reference TEXT, statut TEXT, origine TEXT,
 source_cle TEXT, source_empreinte TEXT, uid TEXT, site_origine TEXT, cree_le TEXT
);
CREATE TABLE comptabilite_ligneecriture (
 id INTEGER PRIMARY KEY, ecriture_id INTEGER, compte_id INTEGER, tiers_id INTEGER,
 section_id INTEGER, vehicule_id INTEGER, libelle TEXT, debit TEXT, credit TEXT,
 lettrage TEXT, source_cle TEXT
);
"""


class ClotureTransportIntegrationTests(unittest.TestCase):
    def test_n_vers_n_plus_un_et_historique_sans_mouvements(self):
        with tempfile.TemporaryDirectory() as dossier:
            dossier = Path(dossier)
            ancien = dossier / "2026.sqlite3"
            nouveau = dossier / "2027.sqlite3"
            catalogue = dossier / "catalogue.json"
            with sqlite3.connect(ancien) as db:
                db.executescript(SCHEMA)
                db.execute("INSERT INTO core_societe VALUES (1,'Transport')")
                db.execute("INSERT INTO auth_user VALUES (1,'admin')")
                db.execute("INSERT INTO django_content_type VALUES (7,'transport','gare')")
                db.execute("INSERT INTO auth_permission VALUES (9,'Voir gare',7,'view_gare')")
                db.execute("INSERT INTO core_exercice VALUES (1,'2026','2026-01-01','2026-12-31',0)")
                db.executemany("INSERT INTO comptabilite_compte VALUES (?,?)",
                               [(1,'411000'), (2,'101000')])
                db.execute("INSERT INTO comptabilite_journal VALUES (1,'AN','AN','2026-12-31')")
                db.execute("INSERT INTO commercial_tiers VALUES (5,'Client')")
                db.execute("INSERT INTO comptabilite_sectionanalytique VALUES (3,'Agence')")
                db.execute("INSERT INTO transport_vehicule VALUES (7,'Bus VIP')")
                db.execute("""INSERT INTO comptabilite_ecriture
                    (id,journal_id,exercice_id,numero,date,statut)
                    VALUES (1,1,1,'OD-1','2026-12-31','VALIDEE')""")
                db.executemany("""INSERT INTO comptabilite_ligneecriture
                    (id,ecriture_id,compte_id,tiers_id,section_id,vehicule_id,debit,credit)
                    VALUES (?,?,?,?,?,?,?,?)""", [
                    (1,1,1,5,3,7,'125.50','0'),
                    (2,1,2,None,None,None,'0','125.50'),
                ])
            catalogue.write_text(json.dumps({"version": 1, "bases": [{
                "id": "transport_2026", "societe": "Transport", "agence": "Centre",
                "exercice": "2026", "moteur": "sqlite", "base": str(ancien),
                "cloture": False
            }]}), encoding="utf-8")

            def migrer(db):
                # Reproduit la contrainte de Django schema_editor SQLite :
                # désactivation FK impossible au sein d'une transaction.
                self.assertFalse(db.in_transaction)
                for statement in SCHEMA.split(';'):
                    if statement.strip():
                        db.execute(statement)
                # Django post_migrate creates permissions with independent IDs.
                db.execute("INSERT INTO django_content_type VALUES (1,'transport','gare')")
                db.execute("INSERT INTO auth_permission VALUES (1,'Voir gare',1,'view_gare')")

            # Schéma minimal réel : l'adaptateur utilise les mêmes services
            # de copie, report et publication que la production.
            referentiels = ("core_societe", "auth_user", "django_content_type",
                            "auth_permission", "comptabilite_compte",
                            "comptabilite_journal", "commercial_tiers",
                            "comptabilite_sectionanalytique", "transport_vehicule")
            with patch("apps.core.adaptateur_cloture_transport_sqlite.REFERENTIELS_OBLIGATOIRES",
                       referentiels):
                resultat = preparer_dossier_transport_sqlite(
                    catalogue, "transport_2026", nouveau, "transport_2027",
                    2027, migrer_cible=migrer
                )
            self.assertEqual(resultat["exercice_precedent"], "transport_2026")
            bases = lire_catalogue(catalogue)
            self.assertTrue(next(b for b in bases if b["id"] == "transport_2026")["cloture"])
            with sqlite3.connect(nouveau) as db:
                self.assertEqual(db.execute("SELECT code FROM core_exercice").fetchone()[0], "2027")
                self.assertEqual(db.execute("SELECT id FROM django_content_type").fetchone()[0], 7)
                self.assertEqual(db.execute("SELECT id, content_type_id FROM auth_permission").fetchone(), (9, 7))
                self.assertIsNone(db.execute("SELECT cloture_au FROM comptabilite_journal").fetchone()[0])
                self.assertEqual(db.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT date FROM comptabilite_ecriture").fetchone()[0], "2027-01-01")
                self.assertEqual(db.execute("""SELECT tiers_id,section_id,vehicule_id,debit
                    FROM comptabilite_ligneecriture WHERE compte_id=1""").fetchone(),
                                 (5,3,7,'125.50'))
            with sqlite3.connect(ancien) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
