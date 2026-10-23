#!/usr/bin/env bash
# Mise à jour de l'ERP sur PythonAnywhere avec la dernière version envoyée sur GitHub (vos données sont conservées) :
#
#   bash ~/erp/deploy/pythonanywhere_mettre_a_jour.sh
set -euo pipefail

PROJET="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$HOME/.virtualenvs/erp"
cd "$PROJET"
cp db.sqlite3 "db.sqlite3.avant-mise-a-jour" 2>/dev/null || true      # copie de sécurité de la base
git pull --ff-only
"$VENV/bin/pip" install -q -r requirements.txt
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v0
touch "/var/www/${USER}_pythonanywhere_com_wsgi.py"                    # recharge le site
echo "Mise à jour terminée : https://${USER}.pythonanywhere.com"
