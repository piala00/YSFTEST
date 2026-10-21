#!/usr/bin/env bash
# Démarrage de la version en ligne de test (Render). Lancé à chaque déploiement, c'est-à-dire à chaque
# envoi sur la branche suivie : les migrations passent, puis le serveur démarre.
set -euo pipefail

python manage.py migrate --noinput
# Société de démonstration (ignorée si des tiers existent déjà), régime de TVA explicite
python manage.py init_erp --demo --regime-tva assujettie ${DEMO_ADMIN_PASSWORD:+--admin "$DEMO_ADMIN_PASSWORD"}

exec gunicorn erp.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
