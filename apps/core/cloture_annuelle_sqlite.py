"""Orchestration sûre d'une clôture annuelle SQLite.

Les services métier fournis doivent initialiser les référentiels et calculer
les reports à nouveau ; aucune copie aveugle des mouvements n'est autorisée.
"""
from contextlib import closing
from pathlib import Path
import os
import sqlite3

from apps.core.catalogue_societes import (
    lire_catalogue, publier_exercice_sqlite_valide, verifier_base_sqlite,
)


def preparer_exercice_sqlite(catalogue, identifiant, destination, nouvel_identifiant,
                            initialiser, reporter, preparer_schema=None):
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
    if preparer_schema is not None and not callable(preparer_schema):
        raise TypeError("préparation du schéma invalide")
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
        # sqlite3.Connection.__exit__ ne ferme PAS la connexion.
        # closing garantit sa libération avant unlink, notamment sous Windows.
        with closing(sqlite3.connect(uri, uri=True)) as origine:
            origine.execute("PRAGMA query_only=ON")
            with closing(sqlite3.connect(str(cible))) as nouvelle:
                nouvelle.execute("PRAGMA foreign_keys=ON")
                # Les migrations Django SQLite doivent désactiver les FK pendant
                # leur schema_editor ; SQLite interdit ce PRAGMA dans BEGIN.
                # Le fichier N+1 étant exclusif et supprimé sur échec, cette
                # préparation hors transaction ne publie aucune donnée.
                if preparer_schema is not None:
                    nouvelle.execute("PRAGMA foreign_keys=OFF")
                    try:
                        preparer_schema(nouvelle)
                        nouvelle.commit()
                    finally:
                        nouvelle.execute("PRAGMA foreign_keys=ON")
                    if nouvelle.execute("PRAGMA foreign_key_check").fetchone():
                        raise ValueError("schéma N+1 invalide après migrations")
                with nouvelle:
                    # DDL SQLite est autrement susceptible de survivre à un
                    # échec des callbacks en l'absence de BEGIN explicite.
                    nouvelle.execute("BEGIN IMMEDIATE")
                    initialiser(origine, nouvelle)
                    reporter(origine, nouvelle)
                    if nouvelle.execute("PRAGMA foreign_key_check").fetchone() is not None:
                        raise ValueError("références invalides dans la base N+1")
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
