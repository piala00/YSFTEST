"""Recette Windows du vrai EXE : clôture N→N+1 puis redémarrage sur la nouvelle base."""
import http.cookiejar
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))


class ClientHTTP:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"
        self.cookies = http.cookiejar.CookieJar()
        self.client = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPCookieProcessor(self.cookies),
        )

    def get(self, chemin, timeout=15):
        with self.client.open(self.base + chemin, timeout=timeout) as reponse:
            return reponse.read().decode("utf-8")

    def post(self, chemin, champs, timeout=300):
        csrf = next((c.value for c in self.cookies if c.name == "csrftoken"), "")
        if not csrf:
            self.get(chemin)
            csrf = next((c.value for c in self.cookies if c.name == "csrftoken"), "")
        if not csrf:
            raise RuntimeError("Cookie CSRF absente")
        donnees = {**champs, "csrfmiddlewaretoken": csrf}
        requete = urllib.request.Request(
            self.base + chemin,
            data=urllib.parse.urlencode(donnees).encode("utf-8"),
            headers={"Referer": self.base + chemin},
        )
        with self.client.open(requete, timeout=timeout) as reponse:
            return reponse.read().decode("utf-8")

    def connecter(self):
        self.get("/connexion/")
        self.post("/connexion/", {
            "username": "controle",
            "password": "test-local-only",
        })
        accueil = self.get("/")
        if 'name="username"' in accueil and 'name="password"' in accueil:
            raise RuntimeError("Authentification EXE refusée : la page d'accueil redirige encore vers la connexion")
        return accueil


def annee_presente(page, annee):
    """Accepte les séparateurs de milliers Unicode ajoutés par la localisation française Django."""
    texte = re.sub(r"[\\s\\u00a0\\u202f\\u2007]+", "", page)
    return str(annee) in texte


def port_libre():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def executer(commande, env, timeout=180):
    resultat = subprocess.run(
        commande, cwd=RACINE, env=env, capture_output=True,
        text=True, timeout=timeout, check=False,
    )
    if resultat.returncode:
        raise RuntimeError(
            f"Commande en échec ({resultat.returncode}) : {' '.join(map(str, commande))}\n"
            + resultat.stdout[-5000:] + "\n" + resultat.stderr[-5000:]
        )
    return resultat.stdout


def demarrer(exe, env, port, journal):
    environnement = dict(env)
    environnement.update(ERP_PORT=str(port), ERP_SANS_NAVIGATEUR="1", ERP_RESEAU="0")
    flux = journal.open("w", encoding="utf-8")
    processus = subprocess.Popen(
        [str(exe)], cwd=RACINE, env=environnement,
        stdout=flux, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
    )
    client = ClientHTTP(port)
    for _ in range(120):
        if processus.poll() is not None:
            flux.flush()
            detail = journal.read_text(encoding="utf-8", errors="replace")[-6000:]
            flux.close()
            raise RuntimeError("L'EXE natif s'est arrêté avant HTTP :\n" + detail)
        try:
            client.get("/connexion/", timeout=5)
            return processus, flux, client
        except (OSError, urllib.error.URLError, TimeoutError):
            time.sleep(1)
    arreter(processus, flux)
    raise RuntimeError("L'EXE natif n'a pas servi /connexion/ en 120 secondes")


def arreter(processus, flux):
    if processus is not None and processus.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(processus.pid)],
                capture_output=True, check=False,
            )
        else:
            processus.terminate()
        try:
            processus.wait(timeout=30)
        except subprocess.TimeoutExpired:
            processus.kill()
            processus.wait(timeout=10)
    if flux is not None and not flux.closed:
        flux.close()


def verifier_reports(base_n1, env):
    controle = r'''
from decimal import Decimal
from django.contrib.auth.models import User
from apps.core.models import Exercice, Agence
from apps.transport.models import Gare, Ligne, ArretLigne, Vehicule, ChangementGamme, ParametresTransport
from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal, Ecriture, LigneEcriture
exercice = Exercice.objects.get(code="2027")
utilisateur = User.objects.get(username="controle")
assert utilisateur.is_superuser and utilisateur.groups.filter(name="Guichet").exists()
assert utilisateur.user_permissions.filter(codename="view_user", content_type__app_label="auth").exists()
assert utilisateur.groups.get(name="Guichet").permissions.filter(codename="view_user", content_type__app_label="auth").exists()
assert Journal.objects.get(code="AN").cloture_au is None
assert set(Compte.objects.values_list("numero", flat=True)) == {"101000", "411000"}
assert ArretLigne.objects.get(ligne__code="YDE-DLA").gare.code == "PVY"
assert ChangementGamme.objects.filter(vehicule__immatriculation="CE-123-AA", gamme="CLASSIQUE").exists()
assert Agence.objects.get(code="CTR").compte_liaison.numero == "101000"
assert Gare.objects.get(code="PVY").rattachement.code == "YDE"
assert Ligne.objects.get(code="YDE-DLA").gare_arrivee.code == "DLA"
assert Vehicule.objects.get(immatriculation="CE-123-AA").proprietaire.code == "PROP-01"
parametres = ParametresTransport.objects.get()
assert parametres.compte_billets.numero == "411000"
assert parametres.compte_proprietaires.numero == "101000"
assert parametres.sessions_caisse_obligatoires and parametres.report_absent_automatique
piece = Ecriture.objects.get(exercice=exercice, origine="CLOTURE_ANNUELLE")
lignes = list(LigneEcriture.objects.filter(ecriture=piece))
assert len(lignes) == 2
assert sum((l.debit for l in lignes), Decimal("0")) == Decimal("125.50")
assert sum((l.credit for l in lignes), Decimal("0")) == Decimal("125.50")
assert any(l.tiers_id and l.section_id and l.vehicule_id for l in lignes)
assert not Ecriture.objects.filter(numero="OD-2026-1").exists()
print("N+1 ORM OK : référentiels, relations, utilisateur, journal AN et balance équilibrée")
'''
    environnement = dict(env)
    environnement.update(
        DB_ENGINE="sqlite", SQLITE_FICHIER=str(base_n1),
        ERP_ASSISTANT="0", ERP_LICENCE="0", MIROIR_DB_ENGINE="",
    )
    executer(
        [sys.executable, str(RACINE / "manage.py"), "shell", "-c", controle],
        environnement, timeout=180,
    )


def main():
    if os.name != "nt":
        raise RuntimeError("Cette recette exige un runner Windows réel")
    if len(sys.argv) != 2:
        raise RuntimeError("Usage : cloture_natif_windows.py chemin-vers-ERP-OHADA-Transport.exe")
    exe = Path(sys.argv[1]).resolve()
    if not exe.is_file():
        raise FileNotFoundError(exe)
    dossier_rapport = Path(os.environ["RUNNER_TEMP"]) / "cloture-natif"
    donnees = dossier_rapport / "donnees"
    donnees.mkdir(parents=True, exist_ok=True)
    source = donnees / "2026.sqlite3"
    catalogue = donnees / "societes.json"
    port1, port2 = port_libre(), port_libre()
    rapport = {
        "executable": str(exe),
        "edition": "transport",
        "migration_schema_n_plus_1": "non vérifiée",
        "cloture_http": "non vérifiée",
        "redemarrage_sur_n_plus_1": "non vérifié",
        "resultats": [],
    }
    processus1 = flux1 = processus2 = flux2 = None
    try:
        environnement = {
            k: v for k, v in os.environ.items()
            if not k.startswith(("DB_", "SQLITE_", "ERP_", "DJANGO_", "MIROIR_", "ECHANGES_"))
            and k != "DATABASE_URL"
        }
        environnement.update(
            DB_ENGINE="sqlite",
            SQLITE_FICHIER=str(source),
            ERP_DONNEES=str(donnees),
            ERP_DOSSIER_DONNEES=str(donnees),
            ERP_CATALOGUE_SOCIETES=str(catalogue),
            ERP_TEST_CLOTURE_NATIVE="1",
            ERP_EDITION="transport",
            ERP_PORT=str(port1),
            ERP_SANS_NAVIGATEUR="1",
            ERP_RESEAU="0",
            ERP_ADMIN="controle",
            ERP_ADMIN_MDP="test-local-only",
            ERP_ASSISTANT="0",
            ERP_LICENCE="0",
            MIROIR_DB_ENGINE="",
            RELAIS_ACTIF="0",
            ECHANGES_RELAIS_URL="",
            ECHANGES_DOSSIER_PARTAGE="",
            DJANGO_SETTINGS_MODULE="erp.settings",
            PYTHONUTF8="1",
        )
        os.environ.update(environnement)

        # Source N : mêmes migrations Django que la version livrée, puis données métier réelles de test.
        with closing(sqlite3.connect(source)) as connexion:
            from apps.core.adaptateur_cloture_transport_sqlite import migrer_schema_django_sqlite
            migrer_schema_django_sqlite(connexion)
        graine = runpy.run_path(str(RACINE / "tests" / "test_cloture_django_migree.py"))["SEED"]
        graine += '''
from django.contrib.auth.models import User
from apps.core.models import Societe
User.objects.filter(username="controle").update(is_superuser=True, is_staff=True)
Societe.objects.update(assistant_termine=True)
'''
        executer(
            [sys.executable, str(RACINE / "manage.py"), "shell", "-c", graine],
            environnement, timeout=180,
        )
        catalogue.write_text(json.dumps({
            "version": 1,
            "bases": [{
                "id": "n", "societe": "Transport Centrale", "agence": "Centre",
                "exercice": "2026", "moteur": "sqlite",
                "base": str(source.resolve()), "cloture": False,
            }],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        rapport["resultats"].append("Base N migrée par Django et semée avec référentiels, relations et écriture équilibrée")

        # Premier démarrage du véritable EXE, authentification super-administrateur et clôture par HTTP local.
        processus1, flux1, client1 = demarrer(
            exe, environnement, port1, dossier_rapport / "serveur-cloture.log"
        )
        accueil = client1.connecter()
        (dossier_rapport / "accueil-apres-auth.html").write_text(accueil, encoding="utf-8")
        page = client1.get("/cloture-annuelle/")
        (dossier_rapport / "ecran-cloture-initial.html").write_text(page, encoding="utf-8")
        if not annee_presente(page, 2027) or "Clôturer" not in page:
            extrait = " ".join(page.split())[:1800]
            raise AssertionError(
                "L'écran compilé ne présente pas l'exercice N+1 attendu. "
                "Consulter CLOTURE-NATIVE-DIAG et ecran-cloture-initial.html. "
                f"Extrait HTML: {extrait}"
            )
        resultat = client1.post(
            "/cloture-annuelle/", {"confirmation": "CLOTURER"}, timeout=300
        )
        if "Exercice 2027 créé" not in resultat or "Clôture impossible" in resultat:
            raise AssertionError("La clôture HTTP de l'EXE a échoué : " + resultat[-2500:])
        rapport["cloture_http"] = "réussie"
        rapport["migration_schema_n_plus_1"] = "réussie via le sous-processus EXE natif"
        rapport["resultats"].append("POST /cloture-annuelle/ exécuté par l'EXE compilé")

        arreter(processus1, flux1)
        processus1 = flux1 = None
        catalogue_data = json.loads(catalogue.read_text(encoding="utf-8"))
        entrees = {b["id"]: b for b in catalogue_data["bases"]}
        if set(entrees) != {"n", "transport-centrale-centre-2027"}:
            raise AssertionError("Le catalogue ne contient pas exactement N et N+1 : " + repr(list(entrees)))
        if not entrees["n"]["cloture"] or entrees["transport-centrale-centre-2027"]["exercice_precedent"] != "n":
            raise AssertionError("Lien historique N→N+1 ou clôture de N absent")
        base_n1 = Path(entrees["transport-centrale-centre-2027"]["base"])
        if not base_n1.is_file():
            raise AssertionError("Fichier physique N+1 absent")
        with closing(sqlite3.connect(source)) as db:
            if db.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0] != 1:
                raise AssertionError("L'historique comptable de N a été modifié")
            if db.execute("SELECT cloture_au FROM comptabilite_journal WHERE code='AN'").fetchone()[0] != "2026-12-31":
                raise AssertionError("Le journal AN historique de N a été modifié")
        verifier_reports(base_n1, environnement)
        rapport["resultats"].append("N intacte ; N+1 vérifiée par ORM : gares, relations, comptes, tiers, véhicule, utilisateur et AN équilibrés")

        # Second démarrage : l'EXE doit réellement ouvrir N+1, retrouver son administrateur et son catalogue.
        environnement_n1 = dict(environnement)
        environnement_n1.update(SQLITE_FICHIER=str(base_n1), ERP_PORT=str(port2))
        processus2, flux2, client2 = demarrer(
            exe, environnement_n1, port2, dossier_rapport / "serveur-redemarrage-n1.log"
        )
        client2.connecter()
        page_n1 = client2.get("/cloture-annuelle/")
        (dossier_rapport / "ecran-cloture-n1.html").write_text(page_n1, encoding="utf-8")
        if not annee_presente(page_n1, 2028) or not annee_presente(page_n1, 2027):
            extrait = " ".join(page_n1.split())[:1800]
            raise AssertionError(
                "Après redémarrage, l'EXE ne reconnaît pas l'exercice N+1. "
                f"Extrait HTML: {extrait}"
            )
        rapport["redemarrage_sur_n_plus_1"] = "réussi"
        rapport["resultats"].append("Deuxième processus EXE : authentification et écran annuel sur N+1 (prochain exercice 2028)")
        arreter(processus2, flux2)
        processus2 = flux2 = None
        rapport["etat"] = "SUCCES"
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    except Exception as exc:
        rapport["etat"] = "ECHEC"
        rapport["erreur"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        arreter(processus1, flux1)
        arreter(processus2, flux2)
        dossier_rapport.mkdir(parents=True, exist_ok=True)
        (dossier_rapport / "RESULTATS.json").write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
