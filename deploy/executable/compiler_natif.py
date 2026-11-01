"""Compile le code de l'ERP (apps/, erp/) en modules natifs (C → code machine, .pyd sous Windows) avant PyInstaller.

    python deploy/executable/compiler_natif.py RACINE --supprimer-sources

Le programme livré ne contient alors plus le code source de l'ERP, ni son « bytecode » facile à relire : seulement
du code machine, comme un logiciel écrit en C. Restent lisibles, comme dans tout logiciel : les gabarits d'écran
(HTML), les fichiers statiques et les migrations de la base (structure des tables).
Non compilés : __init__.py, migrations, tests (les tests ne sont pas livrés).
--supprimer-sources efface les .py compilés : seulement sur une copie de travail (CI), jamais dans le dépôt de
développement (refusé si RACINE contient .git, sauf sur GitHub Actions dont le dépôt est jetable).
"""
import argparse
import os
import sys
from pathlib import Path

PAQUETS = ("apps", "erp")


def est_test(chemin):
    return chemin.name.startswith("tests") or "tests" in chemin.parts


def a_compiler(racine):
    fichiers = []
    for paquet in PAQUETS:
        for f in sorted((racine / paquet).rglob("*.py")):
            if f.name == "__init__.py" or "migrations" in f.parts or est_test(f.relative_to(racine)):
                continue
            fichiers.append(f)
    return fichiers


def compiler(racine, fichiers, taches):
    from Cython.Build import cythonize
    from setuptools import Distribution
    from setuptools.command.build_ext import build_ext

    os.chdir(racine)
    modules = cythonize([str(f.relative_to(racine)) for f in fichiers], nthreads=taches, quiet=True,
                        compiler_directives={"language_level": 3, "binding": True, "always_allow_keywords": True,
                                             "embedsignature": False, "emit_code_comments": False})
    dist = Distribution({"ext_modules": modules})
    commande = build_ext(dist)
    commande.inplace, commande.parallel = True, taches
    commande.ensure_finalized()
    commande.run()


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("racine")
    p.add_argument("--supprimer-sources", action="store_true")
    p.add_argument("--taches", type=int, default=os.cpu_count() or 2)
    p.add_argument("--version-essai", action="store_true", help="Autoriser explicitement une version sans identité éditeur.")
    a = p.parse_args(argv)
    racine = Path(a.racine).resolve()
    if a.supprimer_sources and (racine / ".git").exists() and not os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("Refusé : ce dossier est un dépôt de développement. Compilez une copie.")
    sys.path.insert(0, str(racine))
    from apps.licences.cle_editeur import CLES
    from apps.licences.identite import verifier_distribution

    try:
        identite = verifier_distribution(CLES, version_essai=a.version_essai)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    print(f"Distribution : {identite['mode']} ; empreintes : {', '.join(identite['empreintes_sha256']) or 'aucune'}")
    fichiers = a_compiler(racine)
    compiler(racine, fichiers, a.taches)
    natifs = 0
    for f in fichiers:
        binaires = [b for b in f.parent.glob(f"{f.stem}.*") if b.suffix in (".pyd", ".so")]
        if not binaires:
            raise SystemExit(f"Module non compilé : {f}")
        natifs += 1
        f.with_suffix(".c").unlink(missing_ok=True)
        if a.supprimer_sources:
            f.unlink()
    for build in (racine / "build").glob("temp.*"):
        import shutil

        shutil.rmtree(build, ignore_errors=True)
    print(f"{natifs} modules compilés en code natif{' ; sources retirées' if a.supprimer_sources else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
