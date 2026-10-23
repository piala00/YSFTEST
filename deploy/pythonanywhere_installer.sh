#!/usr/bin/env bash
# Installation de l'ERP sur PythonAnywhere (compte gratuit), à lancer UNE fois dans une console Bash :
#
#   git clone -b ccr-5592a371-fusjt2 https://github.com/piala00/YSFTEST.git ~/erp
#   bash ~/erp/deploy/pythonanywhere_installer.sh MOT_DE_PASSE_ADMIN [--demo]
#
# Crée l'environnement Python, le fichier .env (clé secrète, adresse du site), la base SQLite (conservée
# d'une mise à jour à l'autre), le compte « admin », et écrit le fichier WSGI de l'application web.
# Avant : onglet Web › Add a new web app › Manual configuration › Python 3.13 (ou 3.12). Voir docs/HEBERGEMENT_PYTHONANYWHERE.md.
set -euo pipefail

MOT_DE_PASSE="${1:?Indiquez le mot de passe du compte admin : bash pythonanywhere_installer.sh MOT_DE_PASSE [--demo]}"
DEMO="${2:-}"
PROJET="$(cd "$(dirname "$0")/.." && pwd)"
SITE="${USER}.pythonanywhere.com"
VENV="$HOME/.virtualenvs/erp"

PYTHON=""
for v in python3.13 python3.12; do command -v "$v" >/dev/null && { PYTHON="$v"; break; }; done
[ -n "$PYTHON" ] || { echo "Python 3.12 ou 3.13 introuvable : choisissez une image système récente (Account › System image)."; exit 1; }

echo "1/5 Environnement Python ($PYTHON) dans $VENV"
[ -d "$VENV" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$PROJET/requirements.txt"

echo "2/5 Fichier .env (privé, jamais envoyé sur GitHub)"
if [ ! -f "$PROJET/.env" ]; then
  CLE="$("$VENV/bin/python" -c 'import secrets; print(secrets.token_urlsafe(50))')"
  cat > "$PROJET/.env" <<FIN
SECRET_KEY=$CLE
DEBUG=false
ALLOWED_HOSTS=$SITE
CSRF_TRUSTED_ORIGINS=https://$SITE
FIN
  chmod 600 "$PROJET/.env"
fi

cd "$PROJET"
echo "3/5 Base de données et fichiers statiques"
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v0

echo "4/5 Société, plan comptable, compte admin"
if [ "$DEMO" = "--demo" ]; then
  "$VENV/bin/python" manage.py init_erp --demo --regime-tva automatique --admin "$MOT_DE_PASSE"
else
  "$VENV/bin/python" manage.py init_erp --regime-tva automatique --admin "$MOT_DE_PASSE"
fi

echo "5/5 Fichier WSGI de l'application web"
WSGI="/var/www/${USER}_pythonanywhere_com_wsgi.py"
if [ -f "$WSGI" ]; then
  cat > "$WSGI" <<FIN
# Écrit par deploy/pythonanywhere_installer.sh
import os
import sys

chemin = "$PROJET"
if chemin not in sys.path:
    sys.path.insert(0, chemin)
os.environ["DJANGO_SETTINGS_MODULE"] = "erp.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
FIN
  touch "$WSGI"
  echo "Terminé. Dans l'onglet Web, indiquez Virtualenv : $VENV, puis cliquez sur Reload."
  echo "Adresse : https://$SITE  (utilisateur : admin)"
else
  echo "Fichier $WSGI absent : créez d'abord l'application (onglet Web › Add a new web app › Manual configuration),"
  echo "puis relancez ce script."
fi
