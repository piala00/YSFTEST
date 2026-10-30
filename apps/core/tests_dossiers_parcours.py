"""Dossiers fictifs : droits HTTP et génération réellement exécutée dans un processus séparé."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import dossiers_simulation as ds, poste
from .tests_premier_demarrage import Navigateur, _port_libre, arreter_programmes


class DossiersHTTPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("admin-dossiers", "", "Essai-2030-ok")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_ouverture_exige_serveur_et_confirmation(self):
        ouvrir, redemarrer = mock.Mock(), mock.Mock()
        with mock.patch.dict(poste.ACTIONS, {"dossier_ouvrir": ouvrir, "redemarrer": redemarrer}):
            for donnees, ip in (({"action": "dossier_ouvrir", "dossier": "a" * 32}, "127.0.0.1"),
                                ({"action": "dossier_ouvrir", "dossier": "a" * 32, "confirmation": "OUVRIR"}, "192.0.2.10")):
                self.client.post(reverse("core:poste"), donnees, REMOTE_ADDR=ip)
        ouvrir.assert_not_called()
        redemarrer.assert_not_called()

    def test_ouverture_confirmee_prepare_dossier_et_redemarre_meme_serveur(self):
        appels = []
        with mock.patch.dict(poste.ACTIONS, {"dossier_ouvrir": lambda ident, user: appels.append((ident, user[0])),
                                             "redemarrer": lambda: appels.append("redemarrage")}):
            page = self.client.post(reverse("core:poste"), {"action": "dossier_ouvrir", "dossier": "a" * 32,
                                    "confirmation": "OUVRIR"}, REMOTE_ADDR="127.0.0.1")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(appels, [("a" * 32, "admin-dossiers"), "redemarrage"])

    def test_import_demande_un_fichier_et_n_ouvre_pas_automatiquement(self):
        importer, ouvrir = mock.Mock(), mock.Mock()
        with mock.patch.dict(poste.ACTIONS, {"dossier_importer": importer, "dossier_ouvrir": ouvrir}):
            self.client.post(reverse("core:poste"), {"action": "dossier_importer"})
            importer.assert_not_called()
            self.client.post(reverse("core:poste"), {"action": "dossier_importer",
                             "fichier": SimpleUploadedFile("simulation.erpsim", b"archive fictive")})
            self.assertEqual(importer.call_count, 1)
        ouvrir.assert_not_called()


class DossierGenereReelTests(SimpleTestCase):
    def test_generation_rapide_export_import_et_ouverture_meme_adresse(self):
        """Une journée réduite est jouée par la vraie commande ; aucun taux de production ni base réelle."""
        import time
        import urllib.error
        from django.contrib.auth.hashers import make_password
        from django.db.migrations.loader import MigrationLoader

        with tempfile.TemporaryDirectory() as travail:
            racine = Path(travail)
            identifiant, dossier = ds.creer(racine, "2026-09", "1")
            env = {k: v for k, v in os.environ.items() if not k.startswith(("DB_", "ERP_", "SQLITE_", "MIROIR_", "ECHANGES_", "DJANGO_")) and k != "SECRET_KEY"}
            env.update(ERP_DONNEES=str(dossier), ERP_EDITION="transport", ERP_SANS_NAVIGATEUR="1", ERP_SOUS_PROCESSUS="1")
            programme = [sys.executable, str(settings.BASE_DIR / "deploy/executable/erp_ohada.py")]
            generation = subprocess.run(programme + ["simulation-dossier", "2026-09", "1", "--essai-rapide"],
                                        env=env, capture_output=True, text=True, timeout=240)
            self.assertEqual(generation.returncode, 0, generation.stdout[-4000:] + generation.stderr[-4000:])
            self.assertEqual(ds.lire_json(dossier / ds.MANIFESTE)["etat"], "prete")
            with ds.ouvrir_base(dossier / ds.BASE) as c:
                self.assertGreater(c.execute("SELECT count(*) FROM transport_depart").fetchone()[0], 0)
            with ds.exporter(racine, identifiant) as archive:
                ident_importe = ds.importer(racine, archive, ("essai", make_password("Essai-2030-ok")),
                                           MigrationLoader(None).disk_migrations)
            # On crée un vrai dossier société indépendant avec un témoin, puis on ouvre la copie fictive.
            env.update(ERP_DONNEES=str(racine), ERP_ADMIN="essai", ERP_ADMIN_MDP="Essai-2030-ok", ERP_RESEAU="0")
            env.pop("ERP_SOUS_PROCESSUS", None)
            env["ERP_PORT"] = str(_port_libre())
            initialisation = subprocess.run(programme + ["manage", "migrate", "--noinput"], env=env,
                                            capture_output=True, text=True, timeout=120)
            self.assertEqual(initialisation.returncode, 0, initialisation.stderr)
            racine_base = racine / "erp.sqlite3"
            avant = ds.empreinte(racine_base)
            ds.prevoir_ouverture(racine, ident_importe, lambda: "sauvegarde-test-confirmee")
            sortie = (racine / "serveur-test.log").open("w")
            serveur = subprocess.Popen(programme, env=env, stdout=sortie, stderr=subprocess.STDOUT)
            try:
                nav = Navigateur(f"http://127.0.0.1:{env['ERP_PORT']}")
                for _ in range(120):
                    try:
                        adresse, page = nav.get("/connexion/")
                        break
                    except (urllib.error.URLError, OSError):
                        self.assertIsNone(serveur.poll(), (racine / "serveur-test.log").read_text())
                        time.sleep(0.5)
                self.assertIn("SIMULATION", page)
                nav.post("/connexion/", {"username": "essai", "password": "Essai-2030-ok"})
                adresse, page = nav.get("/poste/?onglet=simulation")
                self.assertIn("Revenir au dossier de la société", page)
                self.assertIn(f":{env['ERP_PORT']}/", adresse)
                self.assertNotIn(f":{int(env['ERP_PORT']) + 1}/", page)
                self.assertEqual(ds.empreinte(racine_base), avant)
                # Retour réel : même adresse, société conservée ; l'UI programme sauvegarde et redémarrage.
                nav.post("/poste/?onglet=simulation", {"action": "dossier_revenir", "confirmation": "OUVRIR"})
                serveur.wait(30)
                self.assertEqual(ds.identifiant_actif(racine), "")
            finally:
                arreter_programmes(racine)
                if serveur.poll() is None:
                    serveur.terminate()
                serveur.wait(30)
                sortie.close()
