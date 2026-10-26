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
        self.addCleanup(lambda: [os.chmod(f, stat.S_IREAD | stat.S_IWRITE) for f in Path(temporaire.name).rglob("*")])
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
