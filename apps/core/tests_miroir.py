"""Copie miroir (commande « miroir ») : base de travail SQLite reportée dans une seconde base.

Essai de bout en bout dans des processus séparés (la base miroir n'existe que si MIROIR_DB_ENGINE est réglé),
ici avec une base miroir SQLite ; le même essai a été fait sur SQL Server 2022.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class MiroirTests(SimpleTestCase):
    def setUp(self):
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.dossier = Path(temporaire.name)
        self.travail, self.miroir = self.dossier / "travail.sqlite3", self.dossier / "miroir.sqlite3"

    def manage(self, *args):
        env = {**os.environ, "SQLITE_FICHIER": str(self.travail), "MIROIR_DB_ENGINE": "sqlite",
               "MIROIR_SQLITE_FICHIER": str(self.miroir), "DB_ENGINE": "sqlite"}
        env.pop("DATABASE_URL", None)
        return subprocess.run([sys.executable, "manage.py", *args], cwd=settings.BASE_DIR, env=env,
                              capture_output=True, text=True, timeout=600)

    def total(self, fichier, sql):
        with sqlite3.connect(fichier) as c:
            return c.execute(sql).fetchone()

    def test_copie_complete_puis_refus_d_une_base_etrangere(self):
        self.assertEqual(self.manage("migrate", "--verbosity", "0").returncode, 0)
        self.assertEqual(self.manage("init_erp", "--verbosity", "0").returncode, 0)
        for _ in range(2):                                        # deux passages : le second remplace le premier
            r = self.manage("miroir")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Miroir à jour", r.stdout)
        for sql in ("SELECT COUNT(*) FROM comptabilite_compte", "SELECT COUNT(*), MAX(numero) FROM comptabilite_compte",
                    "SELECT COUNT(*) FROM comptabilite_journal"):
            self.assertEqual(self.total(self.travail, sql), self.total(self.miroir, sql))
        self.assertGreater(self.total(self.miroir, "SELECT COUNT(*) FROM comptabilite_compte")[0], 0)

        with sqlite3.connect(self.miroir) as c:                   # une table étrangère : ce n'est pas une base de l'ERP
            c.execute("CREATE TABLE F_COMPTET (CT_Num TEXT)")
        r = self.manage("miroir")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("autres tables", r.stderr)
