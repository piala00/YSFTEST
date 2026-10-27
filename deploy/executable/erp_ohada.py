"""ERP OHADA en un seul programme (ERP-OHADA-Transport.exe ou ERP-OHADA-Commerce.exe).

Le programme contient le logiciel, Python, le serveur et la documentation. Un double-clic démarre tout ce que les
anciens fichiers .bat lançaient un par un :
  - le serveur, ouvert aux postes du réseau local (les autres ordinateurs n'installent rien) ;
  - les sauvegardes automatiques de la base (au démarrage puis toutes les ERP_SAUVEGARDE_HEURES heures) ;
  - la copie miroir vers SQL Server, si elle est configurée (toutes les MIROIR_INTERVALLE_MINUTES minutes) ;
  - la synchronisation du dossier d'origine pendant la transition (toutes les heures, si elle est commencée) ;
  - le serveur de simulation (port suivant), si un dossier de simulation existe.

Les données ne sont PAS dans le dossier du programme (on peut le remplacer ou l'effacer sans rien perdre) :
  Windows : C:\\ProgramData\\ERP-OHADA\\<Édition>     (autre emplacement : ERP_DONNEES=…)
  configuration.env, erp.sqlite3 (créée au premier démarrage), sauvegardes\\, journal.txt

    ERP-OHADA-Transport.exe                     démarre tout et ouvre le navigateur
    ERP-OHADA-Transport.exe local               ce poste seulement (pas d'accès réseau)
    ERP-OHADA-Transport.exe simulation 3        dossier de simulation séparé (3 mois fictifs dès 09/2026), puis démarrage
    ERP-OHADA-Transport.exe simulation 2026-01  simulation de janvier 2026 jusqu'à aujourd'hui (2026-01 6 : six mois)
    ERP-OHADA-Transport.exe sauvegarder         sauvegarde immédiate
    ERP-OHADA-Transport.exe restaurer [fichier] remet la dernière sauvegarde (ou le fichier indiqué)
    ERP-OHADA-Transport.exe demarrage-auto      démarrage à l'ouverture de session Windows (relancer pour retirer)
    ERP-OHADA-Transport.exe dossier             affiche l'emplacement des données
    ERP-OHADA-Transport.exe manage <commande>   commande d'administration (miroir, longueur_comptes, echanges…)
"""
import datetime
import os
import secrets
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

PORTS = {"commerce": 8000, "transport": 8100}
MODELE_SAUVEGARDE = "erp-????????-??????.sqlite3"


def dossier_programme():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]                    # exécution depuis le dépôt (essais)


if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(dossier_programme()))


def edition():
    """Commerce ou Transport : fixée à la compilation (edition.txt dans le programme), sinon ERP_EDITION."""
    fichier = Path(getattr(sys, "_MEIPASS", dossier_programme())) / "edition.txt"
    if fichier.exists():
        return fichier.read_text(encoding="utf-8").strip().lower()
    return os.environ.get("ERP_EDITION", "transport").lower()


def dossier_donnees():
    """Hors du dossier du programme : effacer ou remplacer le programme ne touche pas aux données."""
    if os.environ.get("ERP_DONNEES"):
        return Path(os.environ["ERP_DONNEES"])
    ancien = dossier_programme() / "donnees"                       # programmes compilés avant ce changement
    if (ancien / "configuration.env").exists():
        return ancien
    if os.name == "nt":
        base = Path(os.environ.get("PROGRAMDATA") or "C:\\ProgramData")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "ERP-OHADA" / edition().capitalize()


def journal(message):
    ligne = f"{datetime.datetime.now():%d/%m/%Y %H:%M} {message}"
    print(ligne, flush=True)
    try:
        with open(dossier_donnees() / "journal.txt", "a", encoding="utf-8") as f:
            f.write(ligne + "\n")
    except OSError:
        pass


def preparer_environnement(base="erp.sqlite3"):
    """Configuration du dossier des données ; les réglages déjà présents (ex. SQL Server, miroir) sont respectés."""
    donnees = dossier_donnees()
    donnees.mkdir(parents=True, exist_ok=True)
    config = donnees / "configuration.env"
    if not config.exists():
        config.write_text("\n".join([
            f"SECRET_KEY={secrets.token_urlsafe(50)}", "DEBUG=False",
            "ALLOWED_HOSTS=*",                       # les postes du réseau local ouvrent l'adresse du serveur
            "TIME_ZONE=Africa/Douala", "DB_ENGINE=sqlite",
            "# Accès depuis les autres postes du réseau local (0 : ce poste seulement)",
            "ERP_RESEAU=1",
            "# Sauvegardes automatiques : toutes les N heures, nombre gardé, copie dans un second dossier (clé USB, NAS…)",
            "ERP_SAUVEGARDE_HEURES=4", "ERP_SAUVEGARDE_GARDER=60", "# ERP_SAUVEGARDE_COPIE=D:\\Sauvegardes-ERP",
            "# Copie miroir automatique dans SQL Server (la société continue de travailler sur SQLite)",
            "# MIROIR_DB_ENGINE=mssql", "# MIROIR_DB_HOST=SERVEUR\\INSTANCE", "# MIROIR_DB_NAME=ERP_MIROIR",
            "# MIROIR_DB_USER=            (vide : compte Windows)", "# MIROIR_DB_PASSWORD=",
            "# MIROIR_DB_PYTHON_DRIVER=mssql_python", "# MIROIR_INTERVALLE_MINUTES=60", ""]), encoding="utf-8")
    for ligne in config.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())
    os.environ.setdefault("SQLITE_FICHIER", str(donnees / base))   # chemin absolu, dans le dossier des données
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
    return donnees


def base_sqlite():
    return Path(os.environ["SQLITE_FICHIER"]) if os.environ.get("DB_ENGINE", "sqlite") == "sqlite" else None


# ---------------------------------------------------------------- Sauvegardes de la base SQLite
def _retirer(fichier):
    os.chmod(fichier, stat.S_IREAD | stat.S_IWRITE)              # les sauvegardes sont en lecture seule
    fichier.unlink()


def sauvegarder(base, donnees):
    """Copie à chaud (API de sauvegarde SQLite, cohérente même pendant l'utilisation), contrôlée, en lecture seule,
    puis rotation ; éventuellement recopiée dans ERP_SAUVEGARDE_COPIE. Renvoie le fichier créé."""
    dossier = donnees / "sauvegardes"
    dossier.mkdir(parents=True, exist_ok=True)
    for interrompue in dossier.glob("erp-*.partiel"):            # sauvegarde coupée par un arrêt du programme
        interrompue.unlink()
    fichier = dossier / f"erp-{datetime.datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    partiel = fichier.with_suffix(".partiel")
    source, copie = sqlite3.connect(base), sqlite3.connect(partiel)
    try:
        source.backup(copie)
        controle = copie.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        source.close()
        copie.close()
    if controle != "ok":
        partiel.unlink()
        raise RuntimeError(f"sauvegarde incorrecte ({controle})")
    partiel.replace(fichier)
    os.chmod(fichier, stat.S_IREAD)
    garder = max(1, int(os.environ.get("ERP_SAUVEGARDE_GARDER") or 60))
    destinations = [dossier]
    if os.environ.get("ERP_SAUVEGARDE_COPIE"):
        second = Path(os.environ["ERP_SAUVEGARDE_COPIE"])
        second.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fichier, second / fichier.name)
        os.chmod(second / fichier.name, stat.S_IREAD)
        destinations.append(second)
    for d in destinations:
        for ancien in par_date(d.glob(MODELE_SAUVEGARDE))[:-garder]:
            _retirer(ancien)
    return fichier


def par_date(fichiers):
    """Du plus ancien au plus récent (date du fichier : le nom suit l'heure locale, qui peut changer)."""
    return sorted(fichiers, key=lambda f: f.stat().st_mtime)


def sauvegardes(donnees):
    return par_date((donnees / "sauvegardes").glob(MODELE_SAUVEGARDE))


def restaurer(donnees, fichier=None):
    base = Path(os.environ["SQLITE_FICHIER"])
    candidates = sauvegardes(donnees)
    source = Path(fichier) if fichier else (candidates[-1] if candidates else None)
    if source is None or not source.exists():
        print("Aucune sauvegarde trouvée dans", donnees / "sauvegardes")
        return 1
    if base.exists():
        mise_de_cote = base.with_name(f"erp-avant-restauration-{datetime.datetime.now():%Y%m%d-%H%M%S}.sqlite3")
        base.replace(mise_de_cote)
        print(f"Base actuelle mise de côté : {mise_de_cote}")
    for suffixe in ("-wal", "-shm"):
        reste = Path(str(base) + suffixe)
        if reste.exists():
            reste.unlink()
    shutil.copy2(source, base)
    os.chmod(base, stat.S_IREAD | stat.S_IWRITE)
    journal(f"Base restaurée depuis {source}")
    return 0


def controler_base(donnees):
    """La base a été créée mais elle a disparu : ne jamais repartir d'une base vide sans le dire."""
    base, temoin = base_sqlite(), donnees / "base-creee.txt"
    if base is None or base.exists() or not temoin.exists():
        return True
    print(f"\n  ATTENTION : la base {base} a disparu (effacée ou déplacée).")
    dernieres = sauvegardes(donnees)
    if not dernieres:
        print("  Aucune sauvegarde dans", donnees / "sauvegardes", ": remettez le fichier à sa place puis relancez.")
        return False
    print(f"  Dernière sauvegarde : {dernieres[-1].name}")
    if input("  Remettre cette sauvegarde ? (O/N) ").strip().lower() in ("o", "oui"):
        return restaurer(donnees) == 0
    print("  Rien n'a été fait. Relancez le programme quand le fichier est revenu, ou choisissez « restaurer ».")
    return False


# ---------------------------------------------------------------- Tâches automatiques
def tache_periodique(nom, intervalle_s, action, attendre_d_abord=False):
    def boucle():
        from django.db import connections

        if attendre_d_abord:
            time.sleep(intervalle_s)
        while True:
            try:
                action()
            except Exception as exc:                              # une tâche en échec n'arrête pas le serveur
                journal(f"{nom} : ÉCHEC — {exc}")
                with open(dossier_donnees() / "journal.txt", "a", encoding="utf-8") as f:
                    traceback.print_exc(file=f)
            finally:
                connections.close_all()
            time.sleep(intervalle_s)

    threading.Thread(target=boucle, name=nom, daemon=True).start()


def commande(*args):
    import io

    from django.core.management import call_command

    sortie = io.StringIO()
    call_command(*args, stdout=sortie, stderr=sortie)
    return sortie.getvalue().strip().splitlines()[-1:] or [""]


def demarrer_taches(donnees):
    from django.conf import settings

    taches = []
    base = base_sqlite()
    if base is not None:
        heures = float(os.environ.get("ERP_SAUVEGARDE_HEURES") or 4)
        tache_periodique("Sauvegarde", heures * 3600, lambda: journal(f"Sauvegarde : {sauvegarder(base, donnees).name}"))
        taches.append(f"sauvegardes toutes les {heures:g} h → {donnees / 'sauvegardes'}"
                      + (f" et {os.environ['ERP_SAUVEGARDE_COPIE']}" if os.environ.get("ERP_SAUVEGARDE_COPIE") else ""))
    if "miroir" in settings.DATABASES:
        minutes = settings.MIROIR_INTERVALLE_MINUTES
        cible = settings.DATABASES["miroir"]
        tache_periodique("Miroir", minutes * 60, lambda: journal(commande("miroir")[0]))
        taches.append(f"copie miroir toutes les {minutes} min → {cible.get('HOST') or ''} {cible['NAME']}")

    def synchroniser():
        from apps.core.models import Societe

        if Societe.get().source_mode == Societe.SYNCHRO_MIROIR:
            journal("Synchronisation du dossier d'origine : " + commande("synchroniser_dossier")[0])

    tache_periodique("Synchronisation", 3600, synchroniser, attendre_d_abord=True)
    taches.append("synchronisation du dossier d'origine toutes les heures (si elle a été commencée à l'écran)")
    return taches


def demarrer_simulation(donnees, port):
    """Serveur de simulation (dossier séparé), dans un second processus qui s'arrête avec le programme."""
    if not (donnees / "simulation.sqlite3").exists():
        return None
    env = {k: v for k, v in os.environ.items() if k != "SQLITE_FICHIER" and not k.startswith("MIROIR_")}
    env.update(ERP_SANS_NAVIGATEUR="1", ERP_SOUS_PROCESSUS="1")
    programme = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    processus = subprocess.Popen(programme + ["simulation"], env=env)
    import atexit

    atexit.register(processus.terminate)
    return f"simulation : http://127.0.0.1:{port + 1}"


def deja_demarre(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ouvrir_pare_feu(port):
    if os.name != "nt":
        return
    regle = f"ERP OHADA (port {port})"
    if subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={regle}"], capture_output=True).returncode == 0:
        return
    ajout = subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", f"name={regle}", "dir=in", "action=allow",
                            "protocol=TCP", f"localport={port}", "profile=private,domain"], capture_output=True)
    if ajout.returncode != 0:
        print("  Pare-feu : acceptez la question de Windows (cochez « Réseaux privés ») pour les autres postes.")


def adresses_reseau():
    try:
        return sorted({i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
                       if not i[4][0].startswith("127.")})
    except OSError:
        return []


# ---------------------------------------------------------------- Démarrage
def initialiser(edition_, donnees, demander_compte=True):
    """Base, référentiels et compte administrateur au premier démarrage (rien n'est effacé ensuite)."""
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    from apps.comptabilite.models import Compte

    call_command("migrate", interactive=False, verbosity=0)
    if not Compte.objects.exists():
        print("Premier démarrage : création de la base, plan comptable, journaux et exercice…")
        call_command("init_erp", "--activite", edition_, verbosity=0)
    if base_sqlite() is not None and not os.environ.get("ERP_SOUS_PROCESSUS"):
        (donnees / "base-creee.txt").write_text(f"{base_sqlite()}\n", encoding="utf-8")
    U = get_user_model()
    if U.objects.filter(is_superuser=True).exists() or not demander_compte:
        return
    identifiant = os.environ.get("ERP_ADMIN") or input("Identifiant de l'administrateur [admin] : ").strip() or "admin"
    mot_de_passe = os.environ.get("ERP_ADMIN_MDP")
    while not mot_de_passe:
        import getpass

        saisi = getpass.getpass("Mot de passe (invisible, 8 caractères ou plus) : ")
        if len(saisi) >= 8 and saisi == getpass.getpass("Confirmez le mot de passe : "):
            mot_de_passe = saisi
        else:
            print("Mots de passe différents ou trop courts, recommencez.")
    u = U.objects.filter(username=identifiant).first() or U(username=identifiant)
    u.is_superuser = u.is_staff = u.is_active = True
    u.set_password(mot_de_passe)
    u.save()
    print(f"Compte administrateur prêt : {identifiant}")


def servir(port, reseau=False, ouvrir=True, resume=()):
    from waitress import serve

    from erp.wsgi import application

    hote = "0.0.0.0" if reseau else "127.0.0.1"
    adresse = f"http://127.0.0.1:{port}"
    print(f"\n  ERP OHADA {edition().capitalize()} : {adresse}")
    if reseau:
        for ip in adresses_reseau():
            print(f"  Autres postes du réseau : http://{ip}:{port}")
        ouvrir_pare_feu(port)
    for ligne in resume:
        print(f"  {ligne}")
    print("  Gardez cette fenêtre ouverte ; fermez-la pour tout arrêter.\n")
    if ouvrir and not os.environ.get("ERP_SANS_NAVIGATEUR"):
        threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(adresse)), daemon=True).start()
    serve(application, host=hote, port=port, threads=16 if reseau else 8)


def demarrage_automatique():
    """Lien dans le dossier Démarrage de Windows : le programme démarre à l'ouverture de session (sans navigateur)."""
    if os.name != "nt":
        print("Le démarrage automatique se règle sous Windows.")
        return
    dossier = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    lien = dossier / f"ERP OHADA {edition().capitalize()}.bat"
    if lien.exists():
        lien.unlink()
        print("Démarrage automatique RETIRÉ.")
        return
    lien.write_text(f'@echo off\r\nset ERP_SANS_NAVIGATEUR=1\r\nstart "ERP OHADA" /min "{sys.executable}"\r\n', encoding="utf-8")
    print("Le logiciel démarrera à chaque ouverture de session Windows sur ce poste (relancez pour retirer).")


def main(argv):
    edition_ = edition()
    port = int(os.environ.get("ERP_PORT") or PORTS.get(edition_, 8000))
    action = argv[0] if argv else ""
    if action == "dossier":
        print(dossier_donnees())
        return 0
    if action == "demarrage-auto":
        demarrage_automatique()
        return 0
    if action == "manage":
        preparer_environnement()
        from django.core.management import execute_from_command_line

        execute_from_command_line(["manage.py", *argv[1:]])
        return 0
    if action == "simulation":
        os.environ["CONTROLE_HEURE_DEPART"] = "0"
        os.environ["MIROIR_DB_ENGINE"] = ""                     # jamais de copie miroir d'un dossier fictif
        donnees = preparer_environnement(base="simulation.sqlite3")
        import django

        django.setup()
        from django.core.management import call_command

        from apps.transport.models import Depart

        call_command("migrate", interactive=False, verbosity=0)
        if not Depart.objects.exists():
            # simulation 3 (3 mois dès 09/2026) · simulation 2026-01 (jusqu'à aujourd'hui) · simulation 2026-01 6
            debut = next((a for a in argv[1:] if "-" in a), None)
            duree = next((a for a in argv[1:] if "-" not in a), None)
            periode = ["--nombre-mois", duree or "1"] if duree or not debut else ["--jusqu-au", "aujourdhui"]
            print(f"Simulation à partir de {debut or '2026-09'} ({duree + ' mois' if duree else 'jusqu à aujourd hui' if debut else '1 mois'}, "
                  "données fictives) : comptez environ une heure par mois.")
            call_command("simulation", "--mois", debut or "2026-09", *periode,
                         "--rapport", str(donnees / "BILAN-SIMULATION.md"))
        initialiser(edition_, donnees, demander_compte=not os.environ.get("ERP_SOUS_PROCESSUS"))
        servir(port + 1, reseau=os.environ.get("ERP_RESEAU", "1") != "0")
        return 0
    donnees = preparer_environnement()
    if action == "sauvegarder":
        base = base_sqlite()
        if base is None or not base.exists():
            print("Pas de base SQLite à sauvegarder.")
            return 1
        print(f"Sauvegarde : {sauvegarder(base, donnees)}")
        return 0
    if action == "restaurer":
        if deja_demarre(port):
            print("Arrêtez d'abord le logiciel (fermez sa fenêtre), puis relancez la restauration.")
            return 1
        return restaurer(donnees, argv[1] if len(argv) > 1 else None)
    if deja_demarre(port):
        print(f"Le logiciel est déjà démarré sur ce poste : http://127.0.0.1:{port}")
        if not os.environ.get("ERP_SANS_NAVIGATEUR"):
            webbrowser.open(f"http://127.0.0.1:{port}")
        return 0
    if not controler_base(donnees):
        return 1
    import django

    django.setup()
    initialiser(edition_, donnees)
    reseau = action != "local" and os.environ.get("ERP_RESEAU", "1") != "0"
    resume = [f"Données : {donnees}"] + demarrer_taches(donnees)
    simulation = demarrer_simulation(donnees, port)
    if simulation:
        resume.append(simulation)
    servir(port, reseau=reseau, resume=resume)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
