"""Intègre une identité PUBLIQUE existante avant Cython/PyInstaller ; ne crée aucune clé.

python deploy/executable/personnaliser_identite.py --publique parametres.dat --empreinte SHA256
L'empreinte doit venir du guide propriétaire, obtenu séparément du fichier à intégrer.
"""
import argparse
import ast
import base64
import os
from pathlib import Path
import sys
import tempfile

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from apps.licences.identite import empreinte, lire_publique  # noqa: E402


def personnaliser(racine, contenu, attendue):
    brut = lire_publique(contenu)
    attendue = (attendue or "").strip().upper()
    if len(attendue) != 64 or any(c not in "0123456789ABCDEF" for c in attendue):
        raise ValueError("Empreinte SHA-256 autorisée attendue : 64 caractères hexadécimaux.")
    if empreinte(brut) != attendue:
        raise ValueError("L'empreinte publique ne correspond pas à celle autorisée ; aucune modification.")
    cible = Path(racine) / "apps/licences/cle_editeur.py"
    if cible.is_symlink() or not cible.is_file() or cible.stat().st_nlink != 1:
        raise ValueError("Module d'identité absent ou lié ; travailler sur une copie source avant compilation.")
    if any(cible.parent.glob("cle_editeur.*.pyd")) or any(cible.parent.glob("cle_editeur.*.so")):
        raise ValueError("Identité déjà compilée ; personnaliser une copie source propre.")
    arbre = ast.parse(cible.read_text(encoding="utf-8"))
    valeurs = [ast.literal_eval(n.value) for n in arbre.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "CLES" for t in n.targets)]
    if len(valeurs) != 1 or not isinstance(valeurs[0], list):
        raise ValueError("Déclaration CLES invalide ; aucune modification.")
    anciennes = [lire_publique(c.encode("ascii")) for c in valeurs[0]]
    if anciennes and anciennes != [brut]:
        raise ValueError("Une autre identité est déjà intégrée ; rotation explicite requise, anciennes licences à préserver.")
    source = ('"""Identité publique autorisée, intégrée avant compilation ; aucun secret privé."""\n'
              f'# Empreinte SHA-256 : {attendue}\nCLES = [{base64.b64encode(brut).decode()!r}]\n')
    temporaire = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=cible.parent, delete=False) as f:
            temporaire = Path(f.name)
            f.write(source)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaire, cible)
    finally:
        if temporaire is not None:
            temporaire.unlink(missing_ok=True)
    return attendue


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    entree = p.add_mutually_exclusive_group(required=True)
    entree.add_argument("--publique", type=Path)
    entree.add_argument("--publique-base64")
    p.add_argument("--empreinte", required=True)
    p.add_argument("--racine", type=Path, default=RACINE)
    a = p.parse_args(argv)
    try:
        if a.publique:
            with a.publique.open("rb") as f:
                contenu = f.read(8193)
        else:
            contenu = a.publique_base64.encode("ascii")
        print("Identité publique intégrée : " + personnaliser(a.racine, contenu, a.empreinte))
    except (ValueError, OSError, SyntaxError) as exc:
        p.exit(2, f"Refusé : {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
