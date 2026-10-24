#!/usr/bin/env bash
# Construit ERP-OHADA-Windows.zip : logiciel + Python 3.12 pour Windows (paquet NuGet officiel de la
# Python Software Foundation) + composants Windows, pour une installation sans Internet.
# Usage : deploy/windows/construire_paquet.sh [dossier_de_sortie]
set -euo pipefail
DEPOT="$(cd "$(dirname "$0")/../.." && pwd)"
SORTIE="${1:-$DEPOT/sortie}"
PYVER=3.12.10
TRAVAIL="$(mktemp -d)"
P="$TRAVAIL/ERP-OHADA"
mkdir -p "$P/logiciel" "$P/paquets" "$P/python" "$P/outils" "$SORTIE"

git -C "$DEPOT" archive HEAD | tar -x -C "$P/logiciel"
rm -rf "$P/logiciel/docs/"*.zip "$P/logiciel/.github"
# Documentation de travail (skills) : seule la procédure d'essai sur le poste est utile au logiciel installé
find "$P/logiciel/.claude/skills" -mindepth 1 -maxdepth 1 ! -name essai-synchronisation-dossier-local -exec rm -rf {} +
cp "$DEPOT"/deploy/windows/*.bat "$DEPOT/deploy/windows/LISEZ-MOI.txt" "$P/"
cp "$DEPOT"/deploy/windows/outils/* "$P/outils/"

curl -sSL -o "$TRAVAIL/python.nupkg" "https://api.nuget.org/v3-flatcontainer/python/$PYVER/python.$PYVER.nupkg"
unzip -q "$TRAVAIL/python.nupkg" "tools/*" -d "$TRAVAIL/nupkg"
cp -r "$TRAVAIL/nupkg/tools/." "$P/python/"

pip download -q -d "$P/paquets" --only-binary=:all: --python-version 3.12 --platform win_amd64 \
    -r "$DEPOT/deploy/windows/outils/composants.txt"

# Zip lisible par l'Explorateur Windows : noms en ASCII uniquement (sinon arrêt), compression standard
python3 - "$TRAVAIL" "$SORTIE/ERP-OHADA-Windows.zip" <<'PY'
import os, sys, zipfile
racine, cible = sys.argv[1], sys.argv[2]
if os.path.exists(cible):
    os.remove(cible)
with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for dossier, _, fichiers in os.walk(os.path.join(racine, "ERP-OHADA")):
        for f in sorted(fichiers):
            chemin = os.path.join(dossier, f)
            nom = os.path.relpath(chemin, racine).replace(os.sep, "/")
            if not nom.isascii():
                sys.exit(f"Nom de fichier non ASCII, à renommer : {nom}")
            if len(nom) > 150:
                sys.exit(f"Chemin trop long pour Windows : {nom}")
            z.write(chemin, nom)
PY
rm -rf "$TRAVAIL"
ls -la "$SORTIE/ERP-OHADA-Windows.zip"
