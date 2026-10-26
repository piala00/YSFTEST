"""Installation de l'ERP sur un poste Windows, sans Internet.

Lancé par 1-INSTALLER.bat avec le Python fourni (dossier python). Étapes :
installation des paquets fournis, choix de la base (SQLite ou SQL Server), création de la base,
tables, données de départ et compte administrateur. Relançable sans risque : rien n'est effacé.
"""
import getpass
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LOGICIEL = RACINE / "logiciel"
PAQUETS = RACINE / "paquets"
ENV = LOGICIEL / ".env"
PY = sys.executable
# Paquet « Commerce » ou « Transport » : edition.txt fixe l'activité (absent : choix à l'installation)
_EDITION = Path(__file__).resolve().parent / "edition.txt"
EDITION = _EDITION.read_text(encoding="utf-8").strip().lower() if _EDITION.exists() else ""


def titre(texte):
    print("\n" + "=" * 70 + "\n  " + texte + "\n" + "=" * 70)


def demander(question, defaut=""):
    reponse = input(f"{question}{f' [{defaut}]' if defaut else ''} : ").strip()
    return reponse or defaut


def oui(question, defaut="O"):
    return demander(question + " (O/N)", defaut).upper().startswith("O")


def lancer(*args, verifier=True):
    resultat = subprocess.run([PY, *args], cwd=LOGICIEL)
    if verifier and resultat.returncode != 0:
        print("\n*** L'étape a échoué : lisez le message ci-dessus. Corrigez puis relancez 1-INSTALLER.bat. ***")
        input("Appuyez sur Entrée pour fermer.")
        sys.exit(1)
    return resultat.returncode == 0


def installer_paquets():
    titre("1/4  Installation des composants (sans Internet)")
    lancer("-m", "pip", "install", "--no-index", "--find-links", str(PAQUETS), "--disable-pip-version-check",
           "-q", "-r", str(RACINE / "outils" / "composants.txt"))
    print("Composants installés.")


def pilote_sql():
    """pyodbc si le pilote ODBC 17/18 de Microsoft est installé ; sinon le pilote fourni (mssql_python)."""
    try:
        import pyodbc
        pilotes = pyodbc.drivers()
    except Exception:
        pilotes = []
    for nom in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if nom in pilotes:
            return {"DB_DRIVER": nom}
    return {"DB_PYTHON_DRIVER": "mssql_python"}


def configurer():
    titre("2/4  Choix de la base de données")
    if ENV.exists():
        print(f"Configuration existante conservée : {ENV}")
        print("(Pour changer de base, lancez 3-CHANGER-DE-BASE.bat.)")
        return
    print("1 = SQLite   : un simple fichier, rien à configurer (conseillé pour un premier essai)")
    print("2 = SQL Server : une base séparée sur votre serveur SQL (jamais une base Sage)")
    choix = demander("Votre choix", "1")
    poste = socket.gethostname()
    try:
        adresse = socket.gethostbyname(poste)          # pour les autres postes du réseau local
    except OSError:
        adresse = ""
    hotes = ",".join(h for h in ("localhost", "127.0.0.1", poste, adresse) if h)
    lignes = [f"SECRET_KEY={secrets.token_urlsafe(50)}", "DEBUG=False", f"ALLOWED_HOSTS={hotes}", "TIME_ZONE=Africa/Douala"]
    if choix == "2":
        print("\nNom du serveur SQL, comme dans SQL Server Management Studio")
        print("(exemples : localhost   .\\SQLEXPRESS   " + poste + "\\SAGE100)")
        hote = demander("Serveur SQL", "localhost")
        base = demander("Nom de la NOUVELLE base de l'ERP", "ERP_OHADA")
        lignes += ["DB_ENGINE=mssql", f"DB_HOST={hote}", f"DB_NAME={base}"]
        if oui("Connexion avec votre compte Windows (authentification Windows)"):
            lignes += ["DB_USER=", "DB_PASSWORD="]
        else:
            lignes += [f"DB_USER={demander('Utilisateur SQL', 'sa')}",
                       f"DB_PASSWORD={getpass.getpass('Mot de passe SQL (invisible) : ')}"]
        lignes += [f"{k}={v}" for k, v in pilote_sql().items()]
        lignes.append("DB_EXTRA_PARAMS=TrustServerCertificate=yes")
    else:
        lignes.append("DB_ENGINE=sqlite")
    ENV.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"Configuration enregistrée dans {ENV}")


def preparer_base():
    titre("3/4  Création de la base et des tables")
    contenu = ENV.read_text(encoding="utf-8")
    if "DB_ENGINE=mssql" in contenu:
        lancer("manage.py", "creer_base_sqlserver")
    lancer("manage.py", "migrate", "--noinput")
    lancer("manage.py", "collectstatic", "--noinput", "-v0")
    from_zero = not (LOGICIEL / ".initialise").exists()
    if from_zero:
        if EDITION in ("commerce", "transport"):
            activite = EDITION
            print(f"\nERP {EDITION.capitalize()} : activité « {EDITION} ».")
        else:
            print("\nActivité de la société :")
            print("  1. Commerce (achat-revente de marchandises, stocks)")
            print("  2. Transport de voyageurs (billetterie des cars, colis et courrier, logistique)")
            print("  3. Les deux")
            activite = {"1": "commerce", "2": "transport", "3": "mixte"}.get(demander("Votre choix", "1"), "commerce")
        demo = oui("Ajouter les données de démonstration (fictives) ?", "O")
        print("\nTVA : par défaut, aucune TVA n'est appliquée (modifiable ensuite dans les Paramètres de la société).")
        tva = oui("La société facture-t-elle la TVA (taux du Cameroun : 19,25 %, 11 %, 0 %) ?", "N")
        lancer("manage.py", "init_erp", "--activite", activite, *(["--demo"] if demo else []),
               *(["--regime-tva", "automatique"] if tva else []))
        if activite != "transport":
            configurer_gros_detail()
        (LOGICIEL / ".initialise").write_text("ok", encoding="utf-8")
    print("Base prête.")


def configurer_gros_detail():
    """Gros et détail : la vente au détail est réservée à une ou deux boutiques approvisionnées par transfert."""
    print("\nVente en gros et au détail")
    print("Pour ne pas ouvrir les cartons dans les magasins de gros, la vente au détail peut être réservée")
    print("à un ou deux dépôts (boutiques), approvisionnés par transfert depuis les magasins.")
    if not oui("Réserver la vente au détail à des boutiques désignées ?", "N"):
        print("Pas de séparation : modifiable plus tard dans Fichier > Paramètres de la société.")
        return
    noms = demander("Nom de la ou des boutiques (séparés par une virgule)", "Boutique")
    os.environ["ERP_BOUTIQUES"] = noms
    code = ("import os; from apps.commercial.models import Depot; from apps.core.models import Societe\n"
            "for i, nom in enumerate([n.strip() for n in os.environ['ERP_BOUTIQUES'].split(',') if n.strip()], 1):\n"
            "    d = Depot.objects.filter(intitule__iexact=nom).first() or Depot(code=f'BOUT{i}', intitule=nom)\n"
            "    d.vente_detail = True; d.save(); print('Dépôt de détail :', d.intitule)\n"
            "Societe.objects.update(separation_gros_detail=True)")
    lancer("manage.py", "shell", "-c", code)


def creer_compte():
    titre("4/4  Compte administrateur")
    code = ("from django.contrib.auth import get_user_model; "
            "print(get_user_model().objects.filter(is_superuser=True).exists())")
    existe = subprocess.run([PY, "manage.py", "shell", "-c", code], cwd=LOGICIEL, capture_output=True, text=True)
    if existe.stdout.strip() == "True" and not oui("Un administrateur existe déjà. En créer un autre ?", "N"):
        return
    identifiant = demander("Identifiant", "admin")
    while True:
        mdp = getpass.getpass("Mot de passe (invisible, 8 caractères ou plus) : ")
        if len(mdp) >= 8 and mdp == getpass.getpass("Confirmez le mot de passe : "):
            break
        print("Mots de passe différents ou trop courts, recommencez.")
    os.environ["ERP_MDP"] = mdp
    code = ("import os; from django.contrib.auth import get_user_model; U = get_user_model(); "
            f"u = U.objects.filter(username={identifiant!r}).first() or U(username={identifiant!r}); "
            "u.is_superuser = u.is_staff = u.is_active = True; u.set_password(os.environ['ERP_MDP']); u.save(); "
            "print('Compte prêt :', u.username)")
    lancer("manage.py", "shell", "-c", code)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "changer-base":
        if ENV.exists():
            ENV.replace(ENV.with_suffix(".ancien"))
            (LOGICIEL / ".initialise").unlink(missing_ok=True)
            print("Ancienne configuration gardée dans logiciel\\.env.ancien (l'ancienne base n'est pas effacée).")
        configurer()
        preparer_base()
        creer_compte()
    else:
        installer_paquets()
        configurer()
        preparer_base()
        creer_compte()
    titre("Installation terminée")
    print("Lancez 2-DEMARRER-ERP.bat : le logiciel s'ouvre dans votre navigateur.")
    input("Appuyez sur Entrée pour fermer.")
