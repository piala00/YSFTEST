"""Programme compilé (deploy/executable/erp_ohada.py) : dossier des données, sauvegardes, base disparue."""
import importlib.util
import os
import sqlite3
import stat
import tempfile
import time
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

_spec = importlib.util.spec_from_file_location("erp_ohada", settings.BASE_DIR / "deploy" / "executable" / "erp_ohada.py")
lanceur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lanceur)


class ProgrammeCompileTests(SimpleTestCase):
    def setUp(self):
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.addCleanup(lambda: [os.chmod(f, stat.S_IREAD | stat.S_IWRITE) for f in Path(temporaire.name).rglob("*") if f.is_file()])
        self.donnees = Path(temporaire.name)
        self.base = self.donnees / "erp.sqlite3"
        with sqlite3.connect(self.base) as c:
            c.execute("CREATE TABLE t (n INTEGER)")
            c.execute("INSERT INTO t VALUES (1)")
        env = {"ERP_DONNEES": str(self.donnees), "SQLITE_FICHIER": str(self.base), "ERP_SAUVEGARDE_GARDER": "2",
               "ERP_SAUVEGARDE_COPIE": str(self.donnees / "copie")}
        for patch in (mock.patch.dict(os.environ, env), mock.patch("builtins.print")):
            patch.start()
            self.addCleanup(patch.stop)

    def valeur(self, fichier):
        with sqlite3.connect(fichier) as c:
            return c.execute("SELECT MAX(n) FROM t").fetchone()[0]

    def test_donnees_hors_du_dossier_du_programme(self):
        with mock.patch.dict(os.environ, {"ERP_DONNEES": ""}):
            self.assertNotEqual(lanceur.dossier_donnees().parent.parent, lanceur.dossier_programme())
            self.assertEqual(lanceur.dossier_donnees().parent.name, "ERP-OHADA")

    def test_sauvegardes_controlees_en_lecture_seule_et_rotation(self):
        faites = []
        for n in (2, 3, 4):
            with sqlite3.connect(self.base) as c:
                c.execute("INSERT INTO t VALUES (?)", [n])
            fichier = lanceur.sauvegarder(self.base, self.donnees)
            os.utime(fichier, (time.time() + n, time.time() + n))   # dates distinctes
            faites.append(fichier)
            time.sleep(1.1)                                          # noms distincts (à la seconde)
        gardees = lanceur.sauvegardes(self.donnees)
        self.assertEqual(gardees, faites[1:])                          # les 2 plus récentes
        self.assertEqual(len(list((self.donnees / "copie").glob("erp-*.sqlite3"))), 2)
        self.assertFalse(os.stat(gardees[-1]).st_mode & stat.S_IWRITE)
        self.assertEqual(self.valeur(gardees[-1]), 4)

    def test_base_disparue_jamais_remplacee_par_une_base_vide(self):
        lanceur.sauvegarder(self.base, self.donnees)
        (self.donnees / "base-creee.txt").write_text("x")
        self.base.unlink()
        with mock.patch.dict(os.environ, {"DB_ENGINE": "sqlite"}), mock.patch("builtins.input", return_value="N"):
            self.assertFalse(lanceur.controler_base(self.donnees))
        self.assertFalse(self.base.exists())
        with mock.patch.dict(os.environ, {"DB_ENGINE": "sqlite"}), mock.patch("builtins.input", return_value="O"):
            self.assertTrue(lanceur.controler_base(self.donnees))
        self.assertEqual(self.valeur(self.base), 1)

    def test_restaurer_met_la_base_actuelle_de_cote(self):
        lanceur.sauvegarder(self.base, self.donnees)
        with sqlite3.connect(self.base) as c:
            c.execute("INSERT INTO t VALUES (9)")
        self.assertEqual(lanceur.restaurer(self.donnees), 0)
        self.assertEqual(self.valeur(self.base), 1)
        de_cote = list(self.donnees.glob("erp-avant-restauration-*.sqlite3"))
        self.assertEqual(len(de_cote), 1)
        self.assertEqual(self.valeur(de_cote[0]), 9)

    def test_deux_sauvegardes_dans_la_meme_seconde(self):
        import datetime as vrai

        instant = vrai.datetime(2026, 10, 27, 7, 51, 5)
        with mock.patch.object(lanceur.datetime, "datetime") as horloge:
            horloge.now.return_value = instant
            premiere = lanceur.sauvegarder(self.base, self.donnees)
            seconde = lanceur.sauvegarder(self.base, self.donnees)
        self.assertNotEqual(premiere, seconde)
        self.assertTrue(premiere.exists() and seconde.exists())
        self.assertEqual(seconde.name, "erp-20261027-075105-2.sqlite3")


class OuvertureInterfaceTests(SimpleTestCase):
    """L'interface doit s'ouvrir de la même manière quel que soit le navigateur par défaut
    du poste (Windows 10, 11, Server) : sur Windows on force un Chromium récent en mode
    application, sinon on retombe sur le navigateur par défaut du système."""

    def test_hors_windows_pas_de_chromium_force(self):
        with mock.patch.object(lanceur.os, "name", "posix"):
            self.assertIsNone(lanceur._navigateur_chromium())

    def test_ouvre_chromium_en_mode_application(self):
        edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
        with mock.patch.object(lanceur, "_navigateur_chromium", return_value=edge), \
             mock.patch.object(lanceur.subprocess, "Popen") as popen, \
             mock.patch.object(lanceur.webbrowser, "open") as defaut:
            lanceur.ouvrir_interface("http://127.0.0.1:8100")
        self.assertFalse(defaut.called)                       # jamais le navigateur par défaut quand un Chromium existe
        arguments = popen.call_args[0][0]
        self.assertEqual(arguments[0], str(edge))
        self.assertIn("--app=http://127.0.0.1:8100", arguments)

    def test_windows_sans_chromium_retombe_sur_le_defaut(self):
        with mock.patch.object(lanceur, "_navigateur_chromium", return_value=None), \
             mock.patch.object(lanceur.webbrowser, "open") as defaut:
            lanceur.ouvrir_interface("http://127.0.0.1:8100")
        defaut.assert_called_once_with("http://127.0.0.1:8100")
