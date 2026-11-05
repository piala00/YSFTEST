"""Recopie contrôlée de référentiels dans une base annuelle déjà migrée.

Les tables à recopier sont déclarées explicitement par le service métier :
aucune table de mouvements n'est sélectionnée automatiquement.
"""
import sqlite3


def recopier_referentiels(source: sqlite3.Connection, cible: sqlite3.Connection, tables):
    """Copie les lignes des tables autorisées, sans créer ni modifier le schéma.

    Le schéma de N+1 doit avoir été créé par les migrations applicatives.
    L'appelant contrôle la transaction et la vérification des clés étrangères.
    """
    if not isinstance(tables, (tuple, list)) or not tables:
        raise ValueError("liste explicite de référentiels requise")
    if len(set(tables)) != len(tables):
        raise ValueError("table de référentiel dupliquée")
    for nom in tables:
        if not isinstance(nom, str) or not nom.isidentifier() or nom.startswith("sqlite_"):
            raise ValueError("nom de table de référentiel invalide")
        for connexion in (source, cible):
            if connexion.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)
            ).fetchone() is None:
                raise ValueError(f"table de référentiel absente : {nom}")
        ident = '"' + nom + '"'
        source_cols = [r[1] for r in source.execute(f"PRAGMA table_info({ident})")]
        cible_cols = [r[1] for r in cible.execute(f"PRAGMA table_info({ident})")]
        if not source_cols or source_cols != cible_cols:
            raise ValueError(f"structure de référentiel incompatible : {nom}")
        if cible.execute(f"SELECT 1 FROM {ident} LIMIT 1").fetchone():
            raise ValueError(f"table N+1 non vide : {nom}")
        colonnes = ", ".join('"' + col.replace('"', '""') + '"' for col in source_cols)
        marqueurs = ", ".join("?" for _ in source_cols)
        lecture = source.execute(f"SELECT {colonnes} FROM {ident}")
        cible.executemany(
            f"INSERT INTO {ident} ({colonnes}) VALUES ({marqueurs})", lecture,
        )
