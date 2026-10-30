"""ERP OHADA en un seul programme (ERP-OHADA-Transport.exe ou ERP-OHADA-Commerce.exe).

Le programme contient le logiciel, Python, le serveur et la documentation. Un double-clic démarre tout ce que les
anciens fichiers .bat lançaient un par un :
  - le serveur, ouvert aux postes du réseau local (les autres ordinateurs n'installent rien) ;
  - les sauvegardes automatiques de la base (au démarrage puis toutes les ERP_SAUVEGARDE_HEURES heures) ;
  - la copie miroir vers SQL Server, si elle est configurée (toutes les MIROIR_INTERVALLE_MINUTES minutes) ;
  - la synchronisation du dossier d'origine pendant la transition (toutes les heures, si elle est commencée) ;
  - les échanges direction ↔ agences par la boîte aux lettres, si elle est configurée (toutes les 5 minutes) ;
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
import json
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
ENVIRONNEMENT_INITIAL = dict(os.environ)          # avant configuration.env : un redémarrage relit la configuration
MODELE_SAUVEGARDE = "erp-????????-??????*.sqlite3"


def dossier_programme():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]                    # exécution depuis le dépôt (essais)


if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(dossier_programme()))

# Sortie redirigée vers un fichier sous Windows (démarrage automatique, service…) : encodage cp1252 qui ne connaît pas
# tous les caractères (→, …) ; le programme ne doit jamais s'arrêter pour un caractère affiché
for _flux in (sys.stdout, sys.stderr):
    if _flux is not None and hasattr(_flux, "reconfigure"):
        try:
            _flux.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)   # progression lisible
        except (ValueError, OSError):
            pass


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
            "# MIROIR_DB_PYTHON_DRIVER=mssql_python", "# MIROIR_INTERVALLE_MINUTES=60",
            "# Direction et agences : échanges automatiques par une boîte aux lettres (lots chiffrés)",
            "#   relais Internet (adresse et jeton donnés par la direction) :",
            "# ECHANGES_RELAIS_URL=https://relais.exemple.com", "# ECHANGES_RELAIS_JETON=",
            "#   ou dossier partagé (réseau, disque synchronisé) :",
            "# ECHANGES_DOSSIER_PARTAGE=\\\\SERVEUR\\Echanges-ERP", "# ECHANGES_INTERVALLE_MINUTES=5", ""]), encoding="utf-8")
    choix = donnees / "installation-base.env"                    # base choisie dans l'installateur
    if choix.exists():
        valeurs = dict(l.split("=", 1) for l in choix.read_text(encoding="utf-8").splitlines() if "=" in l)
        modifier_configuration(donnees, {k.strip(): v.strip() for k, v in valeurs.items()})
        choix.replace(donnees / "installation-base.env.applique")
    for ligne in config.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            if cle.strip() in ("ERP_LICENCE", "ERP_ASSISTANT"):   # jamais pilotés par le fichier (contournement)
                continue
            os.environ.setdefault(cle.strip(), valeur.strip())
    os.environ.setdefault("SQLITE_FICHIER", str(donnees / base))   # chemin absolu, dans le dossier des données
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
    os.environ.setdefault("ERP_DOSSIER_DONNEES", str(donnees))    # mémoire de l'essai hors de la base
    return donnees


def modifier_configuration(donnees, valeurs):
    """Écran Base de données : met à jour configuration.env (clé=valeur ; None met la ligne en commentaire).
    L'ancien fichier est gardé (configuration-AAAAMMJJ-HHMMSS.env) ; le changement prend effet au redémarrage."""
    config = donnees / "configuration.env"
    lignes = config.read_text(encoding="utf-8").splitlines() if config.exists() else []
    if config.exists():
        shutil.copy2(config, donnees / f"configuration-{datetime.datetime.now():%Y%m%d-%H%M%S}.env")
    restantes = dict(valeurs)
    for i, ligne in enumerate(lignes):
        cle = ligne.lstrip("# ").split("=", 1)[0].strip()
        if "=" in ligne and cle in restantes:
            valeur = restantes.pop(cle)
            lignes[i] = f"# {cle}=" if valeur is None else f"{cle}={valeur}"
    lignes += [f"{cle}={valeur}" for cle, valeur in restantes.items() if valeur is not None]
    config.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    for cle, valeur in valeurs.items():                           # sauvegardes et vérifications : sans redémarrage
        if cle.startswith(("ERP_SAUVEGARDE_", "ERP_VERIFICATION_")):
            if valeur is None:
                os.environ.pop(cle, None)
            else:
                os.environ[cle] = str(valeur)


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
    horodatage = f"{datetime.datetime.now():%Y%m%d-%H%M%S}"
    fichier, n = dossier / f"erp-{horodatage}.sqlite3", 1
    while fichier.exists():                          # deux sauvegardes dans la même seconde : ne jamais écraser
        n += 1
        fichier = dossier / f"erp-{horodatage}-{n}.sqlite3"
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


def restauration_prevue(donnees):
    marqueur = donnees / "restaurer-au-demarrage.txt"
    return marqueur.read_text(encoding="utf-8").strip() if marqueur.exists() else ""


def prevoir_restauration(donnees, nom):
    """Écran Administration du poste : la base ne se remplace pas pendant qu'elle sert ; on le fait au redémarrage."""
    marqueur = donnees / "restaurer-au-demarrage.txt"
    if nom is None:
        marqueur.unlink(missing_ok=True)
        return
    if nom not in {f.name for f in sauvegardes(donnees)}:
        raise ValueError("sauvegarde inconnue")
    marqueur.write_text(nom, encoding="utf-8")


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


PLANIFICATEUR = {"objet": None}


def sauvegarde_immediate(donnees):
    """Sauvegarde de la base de travail : fichier SQLite contrôlé, ou .bak SQL Server vérifié."""
    def faire():
        base = base_sqlite()
        if base is None:
            from apps.core.base_donnees import sauvegarder_sqlserver

            return sauvegarder_sqlserver()
        return sauvegarder(base, donnees).name
    return faire


def demarrer_taches(donnees):
    from django.conf import settings

    from apps.core import base_donnees, planification

    taches = []
    planificateur = planification.Planificateur(donnees, sauvegarde_immediate(donnees), base_donnees.verifier, journal)
    PLANIFICATEUR["objet"] = planificateur
    tache_periodique("Planificateur", 60, planificateur.passage)
    r = planification.reglages()
    taches.append({"heures": f"sauvegardes toutes les {r['heures']:g} h", "quotidien": f"sauvegarde chaque jour à {r['heure']}",
                   "desactive": "sauvegardes automatiques DÉSACTIVÉES"}[r["mode"]]
                  + (" (SQL Server : .bak sur le serveur SQL)" if base_sqlite() is None else f" → {donnees / 'sauvegardes'}")
                  + (f" et {r['copie']}" if r["copie"] else "")
                  + ("" if r["verification"] == "desactive" else " ; vérification de la base chaque semaine"))
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

    from apps.echanges import synchro

    boite = synchro.boite_configuree()
    if boite is not None:
        minutes = float(os.environ.get("ECHANGES_INTERVALLE_MINUTES") or 5)

        def echanger():
            bilan = synchro.synchroniser(boite)
            if bilan.envoyes or bilan.recus or bilan.erreurs:      # le journal ne se remplit pas de passages vides
                journal(f"Échanges ({boite}) : {bilan.texte()}")

        tache_periodique("Échanges", minutes * 60, echanger)
        taches.append(f"échanges direction / agences toutes les {minutes:g} min → {boite}")
    return taches


SIMULATION = {"processus": None}
FICHIERS_SIMULATION = ("simulation.sqlite3", "simulation.sqlite3-wal", "simulation.sqlite3-shm", "BILAN-SIMULATION.md",
                       "simulation-journal.txt")


def demarrer_simulation(donnees, port, arguments=None):
    """Serveur de simulation (dossier séparé), dans un second processus qui s'arrête avec le programme.
    arguments (mois de départ, durée) : la simulation est d'abord fabriquée (comptez une heure par mois)."""
    if arguments is None and not (donnees / "simulation.sqlite3").exists():
        return None
    from django.contrib.auth import get_user_model

    env = {k: v for k, v in os.environ.items()
           if k not in ("SQLITE_FICHIER", "ERP_ASSISTANT", "ERP_LICENCE", "ERP_DOSSIER_DONNEES", "ERP_SERVICE")
           and not k.startswith("DB_") and not k.startswith(("MIROIR_", "ECHANGES_"))}
    env.update(ERP_SANS_NAVIGATEUR="1", ERP_SOUS_PROCESSUS="1", PYTHONUNBUFFERED="1",
               ERP_ADMIN_COMPTES=json.dumps(list(get_user_model().objects.filter(is_superuser=True, is_active=True)
                                                 .values_list("username", "password"))))
    programme = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    sortie = open(donnees / "simulation-journal.txt", "a", encoding="utf-8")
    processus = subprocess.Popen(programme + ["simulation", *(arguments or [])], env=env, stdout=sortie,
                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    sortie.close()
    SIMULATION["processus"] = processus
    import atexit

    atexit.register(processus.terminate)
    return f"simulation : http://127.0.0.1:{port + 1}"


def etat_simulation(donnees, port):
    p = SIMULATION["processus"]
    vivant = p is not None and p.poll() is None
    if deja_demarre(port + 1):
        etat = "prete"
    elif vivant:
        etat = "preparation"
    elif (donnees / "simulation.sqlite3").exists():
        etat = "arretee"
    else:
        etat = "absente"
    journal_ = donnees / "simulation-journal.txt"
    lignes = journal_.read_text(encoding="utf-8", errors="replace").splitlines()[-15:] if journal_.exists() else []
    return {"etat": etat, "port": port + 1, "journal": "\n".join(lignes) if etat != "prete" else ""}


def creer_simulation(donnees, port, debut, duree):
    if etat_simulation(donnees, port)["etat"] != "absente":
        raise RuntimeError("une simulation existe déjà : supprimez-la d'abord")
    journal(f"Simulation demandée : à partir de {debut}, " + ("jusqu'à aujourd'hui" if duree == "aujourdhui" else f"{duree} mois"))
    demarrer_simulation(donnees, port, [debut] + ([] if duree == "aujourdhui" else [str(int(duree))]))


def supprimer_simulation(donnees):
    p = SIMULATION["processus"]
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(30)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(10)
    SIMULATION["processus"] = None
    for nom in FICHIERS_SIMULATION:
        (donnees / nom).unlink(missing_ok=True)
    journal("Simulation supprimée")


def preparer_sqlserver(donnees):
    """Base SQL Server choisie : créée si elle n'existe pas, refusée si elle contient d'autres tables.
    En cas d'échec, la configuration revient à SQLite (le logiciel reste utilisable) et l'erreur est montrée à
    l'écran Base de données / dans l'assistant. Renvoie False s'il faut relancer le programme."""
    from django.conf import settings

    reglage = settings.DATABASES["default"]
    if reglage["ENGINE"] != "mssql":
        return True
    try:
        from apps.core.management.commands.miroir import controler_tables, creer_base_sqlserver

        creer_base_sqlserver(reglage, journal)
        controler_tables("default")
        (donnees / "erreur-base.txt").unlink(missing_ok=True)
        return True
    except Exception as exc:
        message = f"SQL Server {reglage.get('HOST')} / {reglage['NAME']} inutilisable : {exc}"[:600]
        journal(message + " — retour sur SQLite")
        (donnees / "erreur-base.txt").write_text(message, encoding="utf-8")
        modifier_configuration(donnees, {"DB_ENGINE": "sqlite"})
        return False


def relancer():
    """Nouveau départ avec la configuration relue (en service Windows : le service se relance tout seul)."""
    if os.environ.get("ERP_SERVICE"):
        return 1
    programme = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    options = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen(programme + ["redemarrage"], env=dict(ENVIRONNEMENT_INITIAL), stdin=subprocess.DEVNULL, **options)
    return 0


def redemarrer(port):
    """Relance le programme (nouvelle fenêtre) puis arrête celui-ci : le nouveau attend que le port se libère."""
    p = SIMULATION["processus"]
    if p is not None and p.poll() is None:
        p.terminate()
    journal("Redémarrage demandé à l'écran")
    if os.environ.get("ERP_SERVICE"):                             # service Windows : il se relance tout seul
        threading.Timer(1.5, os._exit, [3]).start()
        return f"Redémarrage du service (port {port})"
    programme = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    env = {**ENVIRONNEMENT_INITIAL, "ERP_SANS_NAVIGATEUR": "1"}
    options = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen(programme + ["redemarrage"], env=env, stdin=subprocess.DEVNULL, **options)
    threading.Timer(1.5, os._exit, [0]).start()
    return f"Redémarrage en cours (port {port})"


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
    """Base, référentiels et comptes au premier démarrage (rien n'est effacé ensuite). Le compte administrateur se crée
    dans le navigateur (assistant de premier démarrage) ; ERP_ADMIN / ERP_ADMIN_MDP le créent sans question."""
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    from apps.comptabilite.models import Compte
    from apps.core.models import Societe

    call_command("migrate", interactive=False, verbosity=0)
    if not Compte.objects.exists():
        print("Premier démarrage : création de la base, plan comptable, journaux et exercice…")
        call_command("init_erp", "--activite", edition_, verbosity=0)
        if demander_compte:
            Societe.objects.filter(pk=Societe.get().pk).update(assistant_termine=False)
    if base_sqlite() is not None and not os.environ.get("ERP_SOUS_PROCESSUS"):
        (donnees / "base-creee.txt").write_text(f"{base_sqlite()}\n", encoding="utf-8")
    U = get_user_model()
    if U.objects.filter(is_superuser=True).exists():
        return
    if os.environ.get("ERP_ADMIN_COMPTES"):                       # simulation : mêmes identifiants que la vraie base
        for identifiant, empreinte in json.loads(os.environ["ERP_ADMIN_COMPTES"]):
            U.objects.create(username=identifiant, password=empreinte, is_superuser=True, is_staff=True, is_active=True)
        return
    if os.environ.get("ERP_ADMIN") and os.environ.get("ERP_ADMIN_MDP"):
        u = U(username=os.environ["ERP_ADMIN"], is_superuser=True, is_staff=True, is_active=True)
        u.set_password(os.environ["ERP_ADMIN_MDP"])
        u.save()
        print(f"Compte administrateur prêt : {u.username}")
    elif demander_compte:
        print("  Premier démarrage : le navigateur va s'ouvrir pour créer le compte administrateur,")
        print("  puis renseigner la société et le rôle de ce serveur (direction, agence ou site unique).")


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


def lien_demarrage():
    dossier = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return dossier / f"ERP OHADA {edition().capitalize()}.bat"


def lien_installateur():
    """Raccourci « Démarrage » pour tous les utilisateurs, posé par l'installateur (option cochée)."""
    dossier = Path(os.environ.get("ProgramData", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "StartUp"
    return dossier / f"ERP OHADA {edition().capitalize()}.lnk"


def installation_prevue(donnees):
    """Rôle choisi dans l'installateur (et fichier de l'agence), proposé par l'assistant du premier démarrage."""
    role, fichier = donnees / "role-installation.txt", donnees / "installation-agence.erpx"
    cle = donnees / "installation.dat"
    from apps.licences.licence import ouvrir_stockage
    return {"role": role.read_text(encoding="utf-8").strip() if role.exists() else "",
            "fichier_agence": fichier if fichier.exists() else None,
            "cle_installation": ouvrir_stockage(cle.read_text(encoding="ascii")) if cle.exists() else ""}


def demarrage_automatique():
    """Lien dans le dossier Démarrage de Windows : le programme démarre à l'ouverture de session (sans navigateur)."""
    if os.name != "nt":
        return "Le démarrage automatique se règle sous Windows."
    lien = lien_demarrage()
    if lien.exists():
        lien.unlink()
        return "Démarrage automatique retiré."
    lien.parent.mkdir(parents=True, exist_ok=True)
    lien.write_text(f'@echo off\r\nset ERP_SANS_NAVIGATEUR=1\r\nstart "ERP OHADA" /min "{sys.executable}"\r\n', encoding="utf-8")
    return "Le logiciel démarrera à chaque ouverture de session Windows sur ce poste."


def enregistrer_actions(donnees, port):
    """Écran Fichier › Administration du poste (apps.core.poste) : ce que le programme sait faire sur ce serveur."""
    from apps.core import poste

    def etat():
        base = base_sqlite()
        return {
            "edition": edition(), "port": port, "donnees": str(donnees), "base": str(base or "SQL Server"),
            "taille_base": base.stat().st_size if base and base.exists() else 0,
            "windows": os.name == "nt", "demarrage_auto": os.name == "nt" and lien_demarrage().exists(),
            "demarrage_installateur": os.name == "nt" and lien_installateur().exists(),
            "service": bool(os.environ.get("ERP_SERVICE")),
            "sauvegarde_heures": os.environ.get("ERP_SAUVEGARDE_HEURES") or "4",
            "sauvegarde_garder": os.environ.get("ERP_SAUVEGARDE_GARDER") or "60",
            "sauvegarde_copie": os.environ.get("ERP_SAUVEGARDE_COPIE", ""),
            "sauvegardes": [{"nom": f.name, "taille": f.stat().st_size,
                             "date": datetime.datetime.fromtimestamp(f.stat().st_mtime)} for f in reversed(sauvegardes(donnees))][:30],
            "restauration_prevue": restauration_prevue(donnees),
            "simulation": etat_simulation(donnees, port), "mois_courant": f"{datetime.date.today():%Y}-01"}

    def sauvegarder_maintenant():
        resultat = sauvegarde_immediate(donnees)()
        journal(f"Sauvegarde (à l'écran) : {resultat}")
        return resultat

    poste.ACTIONS.update(
        etat=etat, sauvegarder=sauvegarder_maintenant,
        restaurer_au_demarrage=lambda nom: prevoir_restauration(donnees, nom),
        simulation_creer=lambda debut, duree: creer_simulation(donnees, port, debut, duree),
        simulation_supprimer=lambda: supprimer_simulation(donnees),
        demarrage_auto_basculer=demarrage_automatique,
        configurer=lambda valeurs: modifier_configuration(donnees, valeurs),
        planification=lambda: PLANIFICATEUR["objet"].resume() if PLANIFICATEUR["objet"] else {},
        erreur_base=lambda: ((donnees / "erreur-base.txt").read_text(encoding="utf-8")
                             if (donnees / "erreur-base.txt").exists() else ""),
        redemarrer=lambda: redemarrer(port),
        nouveau_fichier_sqlite=lambda: donnees / ("erp.sqlite3" if not (donnees / "erp.sqlite3").exists()
                                                  else f"erp-{datetime.datetime.now():%Y%m%d-%H%M%S}.sqlite3"),
        restaurer_sqlserver_au_demarrage=lambda fichier: (
            (donnees / "restaurer-sqlserver.txt").write_text(fichier, encoding="utf-8") if fichier
            else (donnees / "restaurer-sqlserver.txt").unlink(missing_ok=True)),
        restauration_sqlserver_prevue=lambda: ((donnees / "restaurer-sqlserver.txt").read_text(encoding="utf-8").strip()
                                               if (donnees / "restaurer-sqlserver.txt").exists() else ""),
        installation_prevue=lambda: installation_prevue(donnees))


def main(argv):
    edition_ = edition()
    port = int(os.environ.get("ERP_PORT") or PORTS.get(edition_, 8000))
    action = argv[0] if argv else ""
    if action in ("sans-navigateur", "service"):                  # démarrage Windows, ou service Windows
        os.environ["ERP_SANS_NAVIGATEUR"] = "1"
        if action == "service":
            os.environ["ERP_SERVICE"] = "1"
        action, argv = "", argv[1:]
    if action == "ouvrir":                                        # le serveur tourne en service : ouvrir le navigateur
        for _ in range(240):
            if deja_demarre(port):
                webbrowser.open(f"http://127.0.0.1:{port}")
                return 0
            time.sleep(0.5)
        print(f"Le serveur ne répond pas sur le port {port} : vérifiez le service « ERP OHADA {edition_.capitalize()} ».")
        return 1
    if action == "dossier":
        print(dossier_donnees())
        return 0
    if action == "demarrage-auto":
        print(demarrage_automatique())
        return 0
    if action == "manage":
        preparer_environnement()
        from django.core.management import execute_from_command_line

        execute_from_command_line(["manage.py", *argv[1:]])
        return 0
    if action == "simulation":
        os.environ["CONTROLE_HEURE_DEPART"] = "0"
        os.environ["MIROIR_DB_ENGINE"] = ""                     # jamais de copie miroir d'un dossier fictif
        os.environ["DB_ENGINE"] = "sqlite"                      # toujours son propre fichier, jamais la vraie base SQL
        for cle in ("ECHANGES_RELAIS_URL", "ECHANGES_DOSSIER_PARTAGE"):
            os.environ[cle] = ""                                # ni d'échange avec les vraies agences
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
        initialiser(edition_, donnees, demander_compte=False)
        if not os.environ.get("ERP_SOUS_PROCESSUS"):
            os.environ["ERP_ASSISTANT"] = "1"                     # lancée seule : compte créé dans le navigateur
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
    if action == "redemarrage":                                   # demandé à l'écran : attendre l'arrêt de l'ancien
        for _ in range(120):
            if not deja_demarre(port):
                break
            time.sleep(0.5)
        action = ""
    if deja_demarre(port):
        print(f"Le logiciel est déjà démarré sur ce poste : http://127.0.0.1:{port}")
        if not os.environ.get("ERP_SANS_NAVIGATEUR"):
            webbrowser.open(f"http://127.0.0.1:{port}")
        return 0
    prevue = restauration_prevue(donnees)
    if prevue:                                                    # demandée à l'écran Administration du poste
        (donnees / "restaurer-au-demarrage.txt").unlink()
        restaurer(donnees, str(donnees / "sauvegardes" / prevue))
    if not controler_base(donnees):
        return 1
    os.environ.setdefault("ERP_ASSISTANT", "1")                   # premier démarrage : assistant dans le navigateur
    os.environ["ERP_LICENCE"] = "1"                               # toujours actif dans le programme compilé :
    #   ni configuration.env ni une variable d'environnement ne peuvent désactiver le contrôle de licence.
    import django

    django.setup()
    if not preparer_sqlserver(donnees):
        return relancer()
    marqueur = donnees / "restaurer-sqlserver.txt"
    if marqueur.exists():                                         # demandée à l'écran Base de données
        from django.conf import settings

        from apps.core.base_donnees import restaurer_sqlserver

        fichier = marqueur.read_text(encoding="utf-8").strip()
        marqueur.unlink()
        journal(f"Restauration SQL Server depuis {fichier} (base actuelle sauvegardée dans "
                f"{restaurer_sqlserver(settings.DATABASES['default'], fichier)})")
    initialiser(edition_, donnees)
    from apps.licences.licence import proteger_ancienne_installation

    proteger_ancienne_installation(donnees)
    enregistrer_actions(donnees, port)
    reseau = action != "local" and os.environ.get("ERP_RESEAU", "1") != "0"
    resume = [f"Données : {donnees}"] + demarrer_taches(donnees)
    simulation = demarrer_simulation(donnees, port)
    if simulation:
        resume.append(simulation)
    servir(port, reseau=reseau, resume=resume)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
