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
                            initialiser, reporter, preparer_schema=None,
                            finaliser_source=None):
    """Crée N+1 puis publie le lien seulement après initialisation et reports.

    initialiser(source, destination) recopie uniquement les référentiels ;
    reporter(source, destination) écrit les soldes d'ouverture.
    Les migrations du schéma cible sont terminées avant de verrouiller N.
    Un verrou SQLite BEGIN IMMEDIATE est ensuite pris sur N AVANT le snapshot :
    il attend les écritures déjà engagées et empêche une nouvelle écriture de
    se glisser entre la lecture des soldes et la clôture. Les callbacks de
    reprise ne peuvent écrire dans N (connexion source en mode lecture seule).
    finaliser_source(connexion_verrou) met à jour les marqueurs de clôture dans
    la transaction du verrou. Si la publication du catalogue échoue, cette
    transaction est annulée et N reste ouvert.
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
    if finaliser_source is not None and not callable(finaliser_source):
        raise TypeError("finalisation de l'exercice source invalide")
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
        # Les migrations Django de N+1 sont indépendantes de N : ne pas bloquer
        # les utilisateurs de l'exercice courant pendant leur exécution.
        if preparer_schema is not None:
            with closing(sqlite3.connect(str(cible), timeout=30)) as schema:
                schema.execute("PRAGMA foreign_keys=OFF")
                try:
                    preparer_schema(schema)
                    schema.commit()
                finally:
                    schema.execute("PRAGMA foreign_keys=ON")
                if schema.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("schéma N+1 invalide après migrations")

        # BEGIN IMMEDIATE, et non BEGIN lecteur : en mode WAL, un simple
        # snapshot autorise un autre écrivain à valider des mouvements absents
        # des reports. Le verrou est acquis avant le snapshot et gardé jusqu'à
        # la publication du catalogue et la finalisation de N.
        with closing(sqlite3.connect(str(source_path), timeout=30)) as verrou:
            try:
                verrou.execute("BEGIN IMMEDIATE")
                from urllib.parse import quote
                uri = "file:" + quote(str(source_path), safe="/:") + "?mode=ro"
                with closing(sqlite3.connect(uri, uri=True, timeout=30)) as origine:
                    origine.execute("PRAGMA query_only=ON")
                    with closing(sqlite3.connect(str(cible), timeout=30)) as nouvelle:
                        nouvelle.execute("PRAGMA foreign_keys=ON")
                        with nouvelle:
                            nouvelle.execute("BEGIN IMMEDIATE")
                            initialiser(origine, nouvelle)
                            reporter(origine, nouvelle)
                            if nouvelle.execute("PRAGMA foreign_key_check").fetchone() is not None:
                                raise ValueError("références invalides dans la base N+1")
                verifier_base_sqlite(str(cible))
                if finaliser_source is not None:
                    finaliser_source(verrou)
                resultat = publier_exercice_sqlite_valide(
                    catalogue, identifiant, str(cible), nouvel_identifiant,
                )
                # Dès que le catalogue est publié, ne jamais supprimer N+1,
                # même si le commit final du verrou source signale une erreur :
                # le catalogue reste alors le garde-fou lecture seule de N.
                publie = True
                verrou.commit()
                return resultat
            except Exception:
                verrou.rollback()
                raise

    finally:
        if not publie:
            # Un échec ne doit pas effacer une base créée par un autre processus.
            # Ce fichier est réservé exclusivement par O_EXCL ci-dessus.
            # Nettoyer les journaux SQLite apres fermeture des connexions :
            # un echec de migration peut laisser WAL/SHM ou rollback journal.
            cible.unlink(missing_ok=True)
            for suffixe in ("-wal", "-shm", "-journal"):
                Path(str(cible) + suffixe).unlink(missing_ok=True)
