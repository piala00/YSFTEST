"""Point d'entrée Windows pour le serveur ERP local empaqueté avec PyInstaller.

La DB et le fichier .env sont EXTERNES au binaire. Ne jamais distribuer de
mots de passe, de clés ni de bases de production dans un exécutable.
"""
import argparse
import os
from pathlib import Path
import sys


def application_dir():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]


def load_env(directory):
    env_file = directory / ".env"
    if env_file.exists():
        for ligne in env_file.read_text(encoding="utf-8-sig").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())


def main():
    parser = argparse.ArgumentParser(description="ERP Transport — serveur applicatif local")
    parser.add_argument("--version", action="version", version="ERP Transport, lanceur Windows 1.0")
    parser.add_argument("--initialiser-base", action="store_true", help="Appliquer les migrations, action explicite")
    parser.add_argument("--creer-admin", action="store_true", help="Créer un administrateur de façon interactive")
    args = parser.parse_args()
    directory = application_dir()
    directory.mkdir(parents=True, exist_ok=True)
    load_env(directory)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
    os.environ.setdefault("DB_ENGINE", "sqlite")
    # Chemin ABSOLU afin de ne pas stocker la base SQLite dans le dossier temporaire PyInstaller
    if os.environ.get("DB_ENGINE", "sqlite") == "sqlite" and not os.environ.get("SQLITE_FICHIER"):
        data = directory / "donnees"
        data.mkdir(parents=True, exist_ok=True)
        os.environ["SQLITE_FICHIER"] = str(data / "erp.sqlite3")
    secret = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    if len(secret) < 32 or secret == "dev-insecure-change-me" or secret.startswith("REMPLACER_"):
        parser.error("Définir une SECRET_KEY longue et aléatoire dans .env avant toute opération")
    import django
    django.setup()
    if args.initialiser_base:
        from django.core.management import call_command
        call_command("migrate", interactive=False)
        print("Migrations appliquées à la base configurée. Vérifiez les journaux.")
        return
    if args.creer_admin:
        from django.core.management import call_command
        call_command("createsuperuser")
        return
    from waitress import serve
    from erp.wsgi import application
    address = os.environ.get("ERP_LISTEN", "127.0.0.1")
    port = int(os.environ.get("ERP_PORT", "8100"))
    print(f"ERP Transport — http://{address}:{port} (Ctrl+C pour arrêter)")
    serve(application, host=address, port=port, threads=8)


if __name__ == "__main__":
    main()
