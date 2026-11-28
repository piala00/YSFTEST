"""Dossiers portables : tests SQLite réels, exécutables sans Django, y compris sous Windows."""
import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from . import dossiers_simulation as ds


class DossiersSimulationTests(unittest.TestCase):
    def setUp(self):
        travail = tempfile.TemporaryDirectory()
        self.addCleanup(travail.cleanup)
        self.racine = Path(travail.name)
        self.production = self.racine / "erp.sqlite3"
        self.production.write_bytes(b"societe reelle fictive du test : ne pas modifier")
        self.avant = self.production.read_bytes()
        self.id, self.dossier = ds.creer(self.racine, "2026-09", "1")
        self.base = self.dossier / ds.BASE
        with contextlib.closing(sqlite3.connect(self.base)) as c, c:
            c.executescript("""
            CREATE TABLE core_societe (id INTEGER PRIMARY KEY, raison_sociale TEXT, activite TEXT, assistant_termine INTEGER);
            INSERT INTO core_societe VALUES (1,'Transports Fictifs','TRANSPORT',1);
            CREATE TABLE django_migrations (app TEXT, name TEXT);
            INSERT INTO django_migrations VALUES ('core','0001_initial');
            CREATE TABLE auth_user (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT,
              first_name TEXT, last_name TEXT, is_active INTEGER, is_staff INTEGER, is_superuser INTEGER,
              last_login TEXT, date_joined TEXT);
            INSERT INTO auth_user VALUES (1,'ancien','hash-original-a-retirer','email@exemple.test','Nom','Ancien',1,1,1,NULL,'2026-01-01');
            CREATE TABLE django_session (session_key TEXT, session_data TEXT);
            INSERT INTO django_session VALUES ('session-fictive','contenu-confidentiel');
            CREATE TABLE authtoken_token (key TEXT); INSERT INTO authtoken_token VALUES ('ancien-token');
            CREATE TABLE licences_etatlicence (cle_installation TEXT); INSERT INTO licences_etatlicence VALUES ('ancienne-reference');
            CREATE TABLE licences_licencedeposee (contenu TEXT); INSERT INTO licences_licencedeposee VALUES ('ancienne-licence');
            CREATE TABLE transport_depart (id INTEGER); INSERT INTO transport_depart VALUES (1);
            CREATE TABLE transport_billet (id INTEGER, voyageur TEXT); INSERT INTO transport_billet VALUES (1,'Passager Fictif');
            """)
        ds.terminer(self.dossier)
        self.connues = {("core", "0001_initial")}

    def archive(self, modifier=None):
        with ds.exporter(self.racine, self.id) as f:
            brut = f.read()
        if not modifier:
            return io.BytesIO(brut)
        original, sortie = zipfile.ZipFile(io.BytesIO(brut)), io.BytesIO()
        with original, zipfile.ZipFile(sortie, "w") as z:
            for info in original.infolist():
                contenu = original.read(info.filename)
                if info.filename == ds.MANIFESTE:
                    d = json.loads(contenu)
                    modifier(d)
                    contenu = json.dumps(d).encode()
                z.writestr(info.filename, contenu)
        sortie.seek(0)
        return sortie

    def test_export_import_puis_ouverture_sans_modifier_la_societe(self):
        avant_simulation = ds.empreinte(self.base)
        archive = self.archive()
        identifiant = ds.importer(self.racine, archive, ("nouveau", "hash-local"), self.connues)
        autre = ds.emplacement(self.racine, identifiant) / ds.BASE
        with ds.ouvrir_base(autre) as c:
            self.assertEqual(c.execute("SELECT voyageur FROM transport_billet").fetchone()[0], "Passager Fictif")
            self.assertEqual(c.execute("SELECT username,password FROM auth_user WHERE is_superuser=1").fetchone(), ("nouveau", "hash-local"))
        self.assertEqual(ds.empreinte(self.base), avant_simulation)
        sauvegarde = mock.Mock(return_value="sauvegarde-confirmee.sqlite3")
        ds.prevoir_ouverture(self.racine, identifiant, sauvegarde)
        self.assertEqual(ds.identifiant_actif(self.racine), identifiant)
        env = {"DB_ENGINE": "mssql", "DB_PASSWORD": "secret-sql", "MIROIR_DB_HOST": "reel",
               "ECHANGES_RELAIS_JETON": "secret-agence", "ERP_SAUVEGARDE_COPIE": "disque-reel"}
        self.assertEqual(ds.environnement_actif(self.racine, env), autre.parent)
        self.assertEqual(env["DB_ENGINE"], "sqlite")
        for cle in ("DB_PASSWORD", "MIROIR_DB_HOST", "ECHANGES_RELAIS_JETON", "ERP_SAUVEGARDE_COPIE"):
            self.assertNotIn(cle, env)
        ds.prevoir_ouverture(self.racine, "", sauvegarde)
        self.assertEqual(ds.identifiant_actif(self.racine), "")
        self.assertEqual(self.production.read_bytes(), self.avant)

    def test_archive_sans_anciens_secrets_meme_dans_pages_libres(self):
        with zipfile.ZipFile(self.archive()) as z:
            self.assertEqual(set(z.namelist()), {ds.BASE, ds.MANIFESTE, "LISEZ-MOI.txt"})
            brut = z.read(ds.BASE)
            for secret in (b"hash-original-a-retirer", b"contenu-confidentiel", b"ancien-token", b"ancienne-reference", b"ancienne-licence"):
                self.assertNotIn(secret, brut)
        self.assertIn(b"hash-original-a-retirer", self.base.read_bytes())

    def test_dossier_courant_non_remplace_si_sauvegarde_echoue(self):
        with self.assertRaises(OSError):
            ds.prevoir_ouverture(self.racine, self.id, mock.Mock(side_effect=OSError("disque plein")))
        self.assertFalse((self.racine / "dossier-actif.json").exists())
        self.assertEqual(self.production.read_bytes(), self.avant)

    def test_dossier_actif_non_supprimable(self):
        ds.prevoir_ouverture(self.racine, self.id, lambda: "sauvegarde")
        with self.assertRaisesRegex(ValueError, "Revenez"):
            ds.supprimer(self.racine, self.id)
        self.assertTrue(self.base.exists())

    def test_chemins_arbitraires_et_liens_refuses(self):
        for identifiant in ("../erp.sqlite3", "C:/Windows", "", "..", self.id + "/.."):
            with self.assertRaises(ValueError):
                ds.emplacement(self.racine, identifiant)

    def test_archive_traversee_chemin_refusee_sans_fichier_cree(self):
        mauvais = io.BytesIO()
        with zipfile.ZipFile(mauvais, "w") as z:
            z.writestr("../sortie.txt", "interdit")
        mauvais.seek(0)
        with self.assertRaisesRegex(ValueError, "Import refusé"):
            ds.importer(self.racine, mauvais, ("nouveau", "hash"), self.connues)
        self.assertFalse((self.racine / "sortie.txt").exists())
        self.assertEqual(len(ds.lister(self.racine)), 1)

    def test_sceau_archive_et_nature_fictive_obligatoires(self):
        for modifier in (lambda d: d.update(sha256="0" * 64), lambda d: d.update(fictif=False), lambda d: d.update(version=999)):
            with self.assertRaises(ValueError):
                ds.importer(self.racine, self.archive(modifier), ("nouveau", "hash"), self.connues)
        self.assertEqual(len(ds.lister(self.racine)), 1)

    def test_version_de_base_plus_recente_refusee(self):
        with contextlib.closing(sqlite3.connect(self.base)) as c, c:
            c.execute("INSERT INTO django_migrations VALUES ('transport','9999_inconnue')")
        with self.assertRaisesRegex(ValueError, "plus récente"):
            ds.importer(self.racine, self.archive(), ("nouveau", "hash"), self.connues)

    def test_vue_sql_importee_refusee(self):
        with contextlib.closing(sqlite3.connect(self.base)) as c, c:
            c.execute("CREATE VIEW vue_interdite AS SELECT * FROM auth_user")
        with self.assertRaisesRegex(ValueError, "vues"):
            ds.verifier_base(self.base)

    def test_verrou_generation_empeche_suppression(self):
        with ds.verrou_generation(self.dossier):
            self.assertTrue(ds.generation_active(self.dossier))
            with self.assertRaisesRegex(ValueError, "génération"):
                ds.supprimer(self.racine, self.id)
        self.assertFalse(ds.generation_active(self.dossier))
        ds.supprimer(self.racine, self.id)
        self.assertFalse(self.dossier.exists())

    def test_criteres_volume_et_scenarios_sont_valides(self):
        self.assertEqual(ds.normaliser_criteres({'departs_jour':250,'echelle':1,'scenarios_complets':True})['departs_jour'],250)
        for c in ({'departs_jour':-1},{'departs_jour':2501},{'echelle':float('nan')},{'echelle':0},{'commande':'effacer'},
                  {'departs_jour':1,'scenarios_complets':True}):
            with self.assertRaises(ValueError):
                ds.normaliser_criteres(c)

    def test_rapports_exportes_importes_et_integrite_verifiee(self):
        for nom in ds.RAPPORTS:
            (self.dossier/nom).write_text('Scénario fictif et écritures de test',encoding='utf-8')
        archive=self.archive()
        identifiant=ds.importer(self.racine,archive,('local','hash-local'),self.connues)
        for nom in ds.RAPPORTS:
            self.assertEqual((ds.emplacement(self.racine,identifiant)/nom).read_text(encoding='utf-8'),'Scénario fictif et écritures de test')
        with self.assertRaisesRegex(ValueError,'Rapport altéré'):
            ds.importer(self.racine,self.archive(lambda d:d.update(rapports_sha256={})),('local','hash-local'),self.connues)
