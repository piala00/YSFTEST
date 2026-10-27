"""Premier démarrage du programme compilé (assistant dans le navigateur) et Fichier › Administration du poste."""
import http.cookiejar
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from . import poste
from .models import Societe


@override_settings(ERP_ASSISTANT=True)
class AssistantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        Societe.objects.update(assistant_termine=False)

    def test_compte_puis_societe_puis_role(self):
        self.assertRedirects(self.client.get("/"), reverse("core:installation_compte"), fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/connexion/"), reverse("core:installation_compte"), fetch_redirect_response=False)
        url = reverse("core:installation_compte")
        # Depuis un autre poste du réseau : refusé
        self.assertEqual(self.client.get(url, REMOTE_ADDR="192.168.1.20").status_code, 403)
        self.client.post(url, {"identifiant": "chef", "mot_de_passe": "court", "confirmation": "court"})
        self.assertFalse(get_user_model().objects.exists())
        reponse = self.client.post(url, {"identifiant": "chef", "mot_de_passe": "Chef-2026-ok", "confirmation": "Chef-2026-ok"})
        self.assertRedirects(reponse, reverse("core:installation"), fetch_redirect_response=False)
        self.assertTrue(get_user_model().objects.get(username="chef").is_superuser)
        # Tant que l'assistant n'est pas fini, l'administrateur y revient
        self.assertRedirects(self.client.get("/"), reverse("core:installation"), fetch_redirect_response=False)
        page = self.client.post(reverse("core:installation"), {"raison_sociale": "Transports Essai SA", "pays": "Cameroun"})
        self.assertRedirects(page, reverse("core:installation") + "?etape=role", fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse("core:installation") + "?etape=role"), "Direction (siège)")
        self.client.post(reverse("core:installation") + "?etape=role", {"role": "siege", "code": "si ege"})   # code refusé
        self.assertFalse(Societe.get().assistant_termine)
        self.client.post(reverse("core:installation") + "?etape=role", {"role": "siege", "code": "SIEGE", "nom": "Direction"})
        societe = Societe.get()
        self.assertTrue(societe.assistant_termine)
        self.assertEqual(societe.raison_sociale, "Transports Essai SA")
        from apps.echanges.publication import site_local

        self.assertEqual(site_local().code, "SIEGE")
        self.assertContains(self.client.get("/"), "Administration du poste")

    def test_un_seul_site(self):
        get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok")
        self.client.login(username="chef", password="Chef-2026-ok")
        self.client.post(reverse("core:installation") + "?etape=role", {"role": "seul"})
        self.assertTrue(Societe.get().assistant_termine)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_role_choisi_dans_l_installateur(self):
        get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok")
        self.client.login(username="chef", password="Chef-2026-ok")
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier, "installation-agence.erpx")
            fichier.write_bytes(b"pas un vrai fichier")
            with mock.patch.dict(poste.ACTIONS, {"installation_prevue": lambda: {"role": "agence", "fichier_agence": fichier}}):
                page = self.client.get(reverse("core:installation") + "?etape=role")
                self.assertContains(page, "Choisi à l'installation : <strong>Agence</strong>")
                self.assertContains(page, "installation-agence.erpx")
                page = self.client.post(reverse("core:installation") + "?etape=role", {"role": "agence", "fichier_prevu": "1"},
                                        follow=True)
                self.assertContains(page, "Impossible")                  # le fichier préparé a bien été lu (et refusé)
        self.assertFalse(Societe.get().assistant_termine)

    @override_settings(ERP_ASSISTANT=False)
    def test_hors_programme_compile_rien_ne_change(self):
        self.assertRedirects(self.client.get("/"), "/connexion/?next=/", fetch_redirect_response=False)


class AdministrationPosteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok")

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("core:poste") + "?seul=1"

    def test_sans_programme_compile(self):
        self.assertContains(self.client.get(self.url), "programme")

    def test_reserve_a_l_administrateur(self):
        self.client.force_login(get_user_model().objects.create_user("caissier", "", "Caisse-2026-ok"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_actions(self):
        appels = []
        etat = {"edition": "transport", "port": 8100, "donnees": "C:/ProgramData/ERP-OHADA/Transport", "base": "erp.sqlite3",
                "taille_base": 1024, "windows": True, "demarrage_auto": False, "sauvegarde_heures": "4",
                "sauvegarde_garder": "60", "sauvegarde_copie": "", "restauration_prevue": "", "mois_courant": "2026-10",
                "sauvegardes": [{"nom": "erp-20261027-100000.sqlite3", "taille": 1024, "date": None}],
                "simulation": {"etat": "absente", "port": 8101, "journal": ""}}
        actions = {"etat": lambda: etat, "sauvegarder": lambda: appels.append("sauvegarder") or "erp-x.sqlite3",
                   "restaurer_au_demarrage": lambda nom: appels.append(("restaurer", nom)),
                   "simulation_creer": lambda debut, duree: appels.append(("simulation", debut, duree)),
                   "simulation_supprimer": lambda: appels.append("supprimer"),
                   "demarrage_auto_basculer": lambda: appels.append("auto") or "ok"}
        with mock.patch.dict(poste.ACTIONS, actions):
            page = self.client.get(self.url)
            for texte in ("Sauvegarder maintenant", "Créer la simulation", "Démarrer le logiciel à l'ouverture de session"):
                self.assertContains(page, texte)
            self.client.post(self.url, {"action": "sauvegarder"})
            self.client.post(self.url, {"action": "restaurer", "fichier": "erp-20261027-100000.sqlite3", "confirmation": "non"})
            self.client.post(self.url, {"action": "restaurer", "fichier": "erp-20261027-100000.sqlite3", "confirmation": "RESTAURER"})
            self.client.post(self.url, {"action": "simulation_creer", "debut": "2026-13", "duree": "2"})          # refusé
            self.client.post(self.url, {"action": "simulation_creer", "debut": "2026-01", "duree": "aujourdhui"})
            self.client.post(self.url, {"action": "simulation_supprimer", "confirmation": "SUPPRIMER"})
            self.client.post(self.url, {"action": "demarrage_auto"})
            etat["simulation"] = {"etat": "prete", "port": 8101, "journal": ""}
            self.assertContains(self.client.get(self.url), "http://testserver:8101/")
        self.assertEqual(appels, ["sauvegarder", ("restaurer", "erp-20261027-100000.sqlite3"),
                                  ("simulation", "2026-01", "aujourdhui"), "supprimer", "auto"])


def _port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Navigateur:
    def __init__(self, base):
        self.base = base
        self.ouvreur = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(self, chemin):
        with self.ouvreur.open(self.base + chemin, timeout=30) as r:
            return r.geturl(), r.read().decode()

    def post(self, chemin, champs):
        _, page = self.get(chemin)
        jeton = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)[1]
        corps = urllib.parse.urlencode({"csrfmiddlewaretoken": jeton, **champs}).encode()
        requete = urllib.request.Request(self.base + chemin, data=corps, headers={"Referer": self.base + chemin})
        with self.ouvreur.open(requete, timeout=60) as r:
            return r.geturl(), r.read().decode()


class ProgrammeLanceTests(SimpleTestCase):
    """Le programme (erp_ohada.py, comme l'exe) lancé pour de vrai, piloté comme depuis le navigateur."""

    def test_premier_demarrage_et_administration(self):
        with tempfile.TemporaryDirectory() as donnees:
            port = _port_libre()
            env = {k: v for k, v in os.environ.items() if not k.startswith(("SQLITE_", "DB_", "ERP_", "DJANGO_"))}
            env.update(ERP_DONNEES=donnees, ERP_PORT=str(port), ERP_SANS_NAVIGATEUR="1", ERP_RESEAU="0", ERP_EDITION="transport")
            programme = [sys.executable, str(settings.BASE_DIR / "deploy" / "executable" / "erp_ohada.py")]
            serveur = subprocess.Popen(programme, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                nav = Navigateur(f"http://127.0.0.1:{port}")
                for _ in range(300):
                    try:
                        adresse, _ = nav.get("/")
                        break
                    except (urllib.error.URLError, OSError):
                        self.assertIsNone(serveur.poll(), serveur.stdout.read() if serveur.poll() is not None else "")
                        time.sleep(0.5)
                self.assertTrue(adresse.endswith("/installation/compte/"))
                adresse, _ = nav.post("/installation/compte/", {"identifiant": "chef", "mot_de_passe": "Chef-2026-ok",
                                                                "confirmation": "Chef-2026-ok"})
                self.assertTrue(adresse.endswith("/installation/"))
                nav.post("/installation/", {"raison_sociale": "Transports Essai SA", "pays": "Cameroun"})
                adresse, page = nav.post("/installation/?etape=role", {"role": "seul"})
                self.assertTrue(adresse.endswith("/installation/?etape=base"), adresse)
                self.assertIn("SQL Server", page)
                adresse, page = nav.post("/installation/?etape=base", {"action": "sqlite"})
                self.assertTrue(adresse.endswith(f":{port}/"), adresse)
                self.assertIn("Configuration terminée", page)

                _, page = nav.post("/poste/?seul=1", {"action": "sauvegarder"})
                self.assertIn("Sauvegarde faite", page)
                sauvegarde = next(Path(donnees, "sauvegardes").glob("erp-*.sqlite3")).name
                self.assertIn("Créer la simulation", page)
                _, page = nav.post("/poste/?seul=1", {"action": "restaurer", "fichier": sauvegarde, "confirmation": "RESTAURER"})
                self.assertIn("Restauration prévue", page)
                self.assertEqual(Path(donnees, "restaurer-au-demarrage.txt").read_text(), sauvegarde)
                nav.post("/poste/?seul=1", {"action": "annuler_restauration"})
                self.assertFalse(Path(donnees, "restaurer-au-demarrage.txt").exists())

                _, page = nav.post("/poste/?seul=1", {"action": "simulation_creer", "debut": "2026-09", "duree": "1"})
                self.assertIn("en préparation", page)
                for _ in range(60):                                       # le journal de la simulation se remplit
                    if Path(donnees, "simulation.sqlite3").exists():
                        break
                    time.sleep(1)
                self.assertTrue(Path(donnees, "simulation.sqlite3").exists())
                _, page = nav.post("/poste/?seul=1", {"action": "simulation_supprimer", "confirmation": "SUPPRIMER"})
                self.assertIn("Simulation supprimée", page)
                self.assertFalse(Path(donnees, "simulation.sqlite3").exists())
                self.assertIn("Créer la simulation", page)

                # Base de données : état, vérification, sauvegarde, puis redémarrage depuis l'écran
                _, page = nav.get("/poste/base/?seul=1")
                self.assertIn("SQLite", page)
                _, page = nav.post("/poste/base/?seul=1", {"action": "verifier"})
                self.assertIn("Vérification de l", page)
                self.assertIn("aucune erreur", page)
                _, page = nav.post("/poste/base/?seul=1", {"action": "sauvegarder"})
                self.assertIn("Sauvegarde faite", page)
                _, page = nav.post("/poste/base/?seul=1", {"action": "redemarrer"})
                self.assertIn("Redémarrage du logiciel", page)
                serveur.wait(30)                                          # l'ancien programme s'arrête…
                for _ in range(240):                                      # … et le nouveau répond sur le même port
                    try:
                        _, page = nav.get("/poste/base/?seul=1")
                        break
                    except (urllib.error.URLError, OSError):
                        time.sleep(0.5)
                self.assertIn("Base de données", page)
            finally:
                for environ in Path("/proc").glob("[0-9]*/environ"):     # le programme relancé (même dossier de données)
                    try:
                        if f"ERP_DONNEES={donnees}\0".encode() in environ.read_bytes():
                            os.kill(int(environ.parent.name), 15)
                    except (OSError, ValueError):
                        pass
                serveur.terminate()
                serveur.wait(30)
