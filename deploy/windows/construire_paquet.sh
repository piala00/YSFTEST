#!/usr/bin/env bash
# Construit ERP-OHADA-Commerce-Windows.zip et ERP-OHADA-Transport-Windows.zip : logiciel + Python 3.12 pour Windows (paquet NuGet officiel de la
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
    -r "$DEPOT/deploy/windows/outils/composants.txt" -r "$DEPOT/deploy/windows/outils/compilation.txt"

# Deux paquets distincts : ERP Commerce et ERP Transport (même logiciel, activité fixée à l'installation,
# ports, titres et tâches planifiées différents pour pouvoir installer les deux sur le même PC)
for EDITION in ${EDITIONS:-Commerce Transport}; do
python3 - "$TRAVAIL" "$EDITION" "$SORTIE/ERP-OHADA-$EDITION-Windows.zip" <<'PY'
import os, re, shutil, sys, zipfile
racine, edition, cible = sys.argv[1], sys.argv[2], sys.argv[3]
dossier_ed = os.path.join(racine, f"ERP-OHADA-{edition}")
shutil.rmtree(dossier_ed, ignore_errors=True)
shutil.copytree(os.path.join(racine, "ERP-OHADA"), dossier_ed, symlinks=True)
with open(os.path.join(dossier_ed, "outils", "edition.txt"), "w", encoding="utf-8") as f:
    f.write(edition.lower() + "\n")
if edition == "Commerce":                       # la simulation de septembre est celle d'une société de transport
    for f in ("7-SIMULATION.bat", "8-SUPPRIMER-SIMULATION.bat"):
        os.remove(os.path.join(dossier_ed, f))
ports = {"8001": "8101", "8000": "8100"} if edition == "Transport" else {}
textes = [os.path.join(dossier_ed, f) for f in os.listdir(dossier_ed) if f.endswith((".bat", ".txt"))]
textes += [os.path.join(dossier_ed, "outils", f) for f in os.listdir(os.path.join(dossier_ed, "outils")) if f.endswith(".py")]
for chemin in textes:
    with open(chemin, "rb") as f:
        t = f.read().decode("utf-8")
    t = t.replace("ERP OHADA", f"ERP OHADA {edition}").replace("C:\\ERP-OHADA", f"C:\\ERP-OHADA-{edition}")
    for a, b in ports.items():
        t = t.replace(a, b)
    if chemin.endswith("LISEZ-MOI.txt"):
        autre = "Transport" if edition == "Commerce" else "Commerce"
        t = t.replace("aucune connexion Internet n'est nécessaire.\n", "aucune connexion Internet n'est nécessaire.\n\n"
                      f"Ce paquet est l'ERP {edition.upper()} (activité fixée à l'installation). L'ERP {autre} est un\n"
                      f"autre paquet (ERP-OHADA-{autre}-Windows.zip). Les deux peuvent être installés sur le même PC,\n"
                      "dans deux dossiers différents : ERP Commerce sur le port 8000, ERP Transport sur le port 8100.\n", 1)
    if edition == "Commerce" and chemin.endswith("LISEZ-MOI.txt"):
        t = re.sub(r"\n3 bis\. ESSAYER.*?(?=\n4\. EN CAS)", "\n", t, flags=re.S)
        t = re.sub(r"\n[78]-S[A-Z-]*\.bat[^\n]*", "", t)
    with open(chemin, "wb") as f:
        f.write(t.encode("utf-8"))
# Zip lisible par l'Explorateur Windows : noms en ASCII uniquement (sinon arrêt), compression standard
if os.path.exists(cible):
    os.remove(cible)
with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for dossier, _, fichiers in os.walk(dossier_ed):
        for f in sorted(fichiers):
            chemin = os.path.join(dossier, f)
            nom = os.path.relpath(chemin, racine).replace(os.sep, "/")
            if not nom.isascii():
                sys.exit(f"Nom de fichier non ASCII, à renommer : {nom}")
            if len(nom) > 150:
                sys.exit(f"Chemin trop long pour Windows : {nom}")
            z.write(chemin, nom)
shutil.rmtree(dossier_ed)
PY
ls -la "$SORTIE/ERP-OHADA-$EDITION-Windows.zip"
done
rm -rf "$TRAVAIL"
