"""Orchestration sûre d'une clôture annuelle SQLite.

Les services métier fournis doivent initialiser les référentiels et calculer
les reports à nouveau ; aucune copie aveugle des mouvements n'est autorisée.
"""
from pathlib import Path
import os
import sqlite3

from apps.core.catalogue_societes import (
    lire_catalogue, publier_exercice_sqlite_valide, verifier_base_sqlite,
)


def preparer_exercice_sqlite(catalogue, identifiant, destination, nouvel_identifiant,
                            initialiser, reporter):
    """Crée N+1 puis publie le lien seulement après initialisation et reports.

    initialiser(source, destination) doit créer le schéma et recopier uniquement
    la configuration ; reporter(source, destination) écrit les soldes d'ouverture.
    En cas d'échec, la nouvelle base est supprimée et N reste ouvert.
    Les callbacks ne doivent pas modifier N : celui-ci est ouvert en lecture seule.
    """
    bases = lire_catalogue(catalogue)
    source = next((b for b in bases if b["id"] == identifiant), None)
    if source is None or source["moteur"] != "sqlite":
        raise ValueError("exercice SQLite introuvable")
    if source["cloture"]:
        raise ValueError("exercice précédent déjà clôturé")
    if not callable(initialiser) or not callable(reporter):
        raise TypeError("initialisation et reports obligatoires")
    source_path = Path(verifier_base_sqlite(source["base"]))
    cible = Path(destination).expanduser().absolute()
    if cible == source_path or (cible.exists() and cible.samefile(source_path)):
        raise ValueError("la destination correspond à l'exercice courant")
    if cible.exists():
        raise FileExistsError("la base N+1 existe déjà")
    if not cible.parent.is_dir():
        raise ValueError("dossier de destination absent")
    # Création exclusive : jamais d'écrasement, même en cas de course.
    descripteur = os.open(str(cible), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descripteur)
    publie = False
    try:
        # URI en lecture seule ; le service métier ne reçoit pas de connexion
        # autorisant l'écriture dans N.
        from urllib.parse import quote
        uri = "file:" + quote(str(source_path), safe="/:") + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as origine:
            with sqlite3.connect(str(cible)) as nouvelle:
                nouvelle.execute("PRAGMA foreign_keys=ON")
                initialiser(origine, nouvelle)
                nouvelle.commit()
                reporter(origine, nouvelle)
                nouvelle.commit()
        verifier_base_sqlite(str(cible))
        resultat = publier_exercice_sqlite_valide(
            catalogue, identifiant, str(cible), nouvel_identifiant,
        )
        publie = True
        return resultat
    finally:
        if not publie:
            # Un échec ne doit pas effacer une base créée par un autre processus.
            # Ce fichier est réservé exclusivement par O_EXCL ci-dessus.
            cible.unlink(missing_ok=True)
