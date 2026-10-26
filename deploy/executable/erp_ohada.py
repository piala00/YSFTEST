"""ERP OHADA en un seul programme (ERP-OHADA-Transport.exe ou ERP-OHADA-Commerce.exe).

Le programme contient le logiciel, Python et le serveur. Ses données sont à côté de lui, dans le dossier « donnees » :
configuration (clé secrète, base), base SQLite. Rien n'est écrit ailleurs.

    ERP-OHADA-Transport.exe                     démarre le logiciel et ouvre le navigateur
    ERP-OHADA-Transport.exe reseau              serveur pour tous les postes de l'agence
    ERP-OHADA-Transport.exe simulation 3        dossier de simulation séparé (3 mois fictifs), puis démarrage
    ERP-OHADA-Transport.exe manage <commande>   commande d'administration (longueur_comptes, echanges, …)

Au premier démarrage : création de la base, plan comptable (7 chiffres), journaux, exercice, puis compte
administrateur (identifiant et mot de passe demandés dans la fenêtre).
"""
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORTS = {"commerce": 8000, "transport": 8100}


def dossier_programme():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]                    # exécution depuis le dépôt (essais)


def edition():
    """Commerce ou Transport : fixée à la compilation (edition.txt dans le programme), sinon ERP_EDITION."""
    fichier = Path(getattr(sys, "_MEIPASS", dossier_programme())) / "edition.txt"
    if fichier.exists():
        return fichier.read_text(encoding="utf-8").strip().lower()
    return os.environ.get("ERP_EDITION", "transport").lower()


def preparer_environnement(base="erp.sqlite3"):
    """Configuration du dossier « donnees » ; les réglages déjà présents (ex. SQL Server) sont respectés."""
    donnees = Path(os.environ.get("ERP_DONNEES") or dossier_programme() / "donnees")
    donnees.mkdir(parents=True, exist_ok=True)
    config = donnees / "configuration.env"
    if not config.exists():
        poste = socket.gethostname()
        try:
            adresse = socket.gethostbyname(poste)
        except OSError:
            adresse = ""
        hotes = ",".join(h for h in ("localhost", "127.0.0.1", poste, adresse) if h)
        config.write_text("\n".join([f"SECRET_KEY={secrets.token_urlsafe(50)}", "DEBUG=False", f"ALLOWED_HOSTS={hotes}",
                                     "TIME_ZONE=Africa/Douala", "DB_ENGINE=sqlite", ""]), encoding="utf-8")
    for ligne in config.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())
    os.environ.setdefault("SQLITE_FICHIER", str(donnees / base))   # chemin absolu : à côté du programme
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
    return donnees


def initialiser(edition_, demander_compte=True):
    """Base, référentiels et compte administrateur au premier démarrage (rien n'est effacé ensuite)."""
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    from apps.comptabilite.models import Compte

    call_command("migrate", interactive=False, verbosity=0)
    if not Compte.objects.exists():
        print("Premier démarrage : plan comptable, journaux et exercice…")
        call_command("init_erp", "--activite", edition_, verbosity=0)
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


def servir(port, reseau=False, ouvrir=True):
    from waitress import serve

    from erp.wsgi import application

    hote = "0.0.0.0" if reseau else "127.0.0.1"
    adresse = f"http://127.0.0.1:{port}"
    print(f"\n  ERP OHADA {edition().capitalize()} : {adresse}\n  Gardez cette fenêtre ouverte ; fermez-la pour arrêter.\n")
    if ouvrir and not os.environ.get("ERP_SANS_NAVIGATEUR"):
        threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(adresse)), daemon=True).start()
    serve(application, host=hote, port=port, threads=16 if reseau else 8)


def main(argv):
    edition_ = edition()
    port = int(os.environ.get("ERP_PORT") or PORTS.get(edition_, 8000))
    commande = argv[0] if argv else ""
    if commande == "manage":
        preparer_environnement()
        from django.core.management import execute_from_command_line

        execute_from_command_line(["manage.py", *argv[1:]])
        return
    if commande == "simulation":
        os.environ["CONTROLE_HEURE_DEPART"] = "0"
        donnees = preparer_environnement(base="simulation.sqlite3")
        import django

        django.setup()
        from django.core.management import call_command

        from apps.transport.models import Depart

        call_command("migrate", interactive=False, verbosity=0)
        if not Depart.objects.exists():
            mois = argv[1] if len(argv) > 1 else "1"
            print(f"Simulation de {mois} mois (données fictives) : comptez environ une heure par mois.")
            call_command("simulation", "--mois", "2026-09", "--nombre-mois", mois,
                         "--rapport", str(donnees / "BILAN-SIMULATION.md"))
        initialiser(edition_)
        servir(port + 1)
        return
    preparer_environnement()
    import django

    django.setup()
    initialiser(edition_)
    servir(port, reseau=commande == "reseau")


if __name__ == "__main__":
    main(sys.argv[1:])
