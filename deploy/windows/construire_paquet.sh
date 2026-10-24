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
cp "$DEPOT"/deploy/windows/*.bat "$DEPOT/deploy/windows/LISEZ-MOI.txt" "$P/"
cp "$DEPOT"/deploy/windows/outils/* "$P/outils/"

curl -sSL -o "$TRAVAIL/python.nupkg" "https://api.nuget.org/v3-flatcontainer/python/$PYVER/python.$PYVER.nupkg"
unzip -q "$TRAVAIL/python.nupkg" "tools/*" -d "$TRAVAIL/nupkg"
cp -r "$TRAVAIL/nupkg/tools/." "$P/python/"

pip download -q -d "$P/paquets" --only-binary=:all: --python-version 3.12 --platform win_amd64 \
    -r "$DEPOT/deploy/windows/outils/composants.txt"

( cd "$TRAVAIL" && zip -qr "$SORTIE/ERP-OHADA-Windows.zip" ERP-OHADA )
rm -rf "$TRAVAIL"
ls -la "$SORTIE/ERP-OHADA-Windows.zip"
