"""Recopie contrôlée de référentiels dans une base annuelle déjà migrée.

Les tables à recopier sont déclarées explicitement par le service métier :
aucune table de mouvements n'est sélectionnée automatiquement.
"""
import sqlite3

def _contraintes_uniques(connexion, nom):
    """Compare les index uniques par colonnes, pas par noms auto-générés."""
    ident = '"' + nom + '"'
    resultat = []
    for index in connexion.execute(f"PRAGMA index_list({ident})"):
        if not index[2]:
            continue
        index_ident = '"' + index[1].replace('"', '""') + '"'
        colonnes = tuple(
            (col[2], col[3], col[4], col[5])
            for col in connexion.execute(f"PRAGMA index_xinfo({index_ident})")
            if col[5]
        )
        # Les index partiels et sur expressions ne sont pas comparables
        # par leurs seules colonnes : refuser toute reprise ambiguë.
        if index[4] or any(col[1] < 0 for col in connexion.execute(f"PRAGMA index_xinfo({index_ident})") if col[5]):
            raise ValueError(f"contraintes uniques complexes non prises en charge : {nom}")
        resultat.append((index[3], bool(index[4]), colonnes))
    return sorted(resultat, key=repr)


def recopier_referentiels(source: sqlite3.Connection, cible: sqlite3.Connection, tables):
    """Copie les lignes des tables autorisées, sans créer ni modifier le schéma.

    Le schéma de N+1 doit avoir été créé par les migrations applicatives.
    L'appelant contrôle la transaction et la vérification des clés étrangères.
    """
    if not isinstance(tables, (tuple, list)) or not tables:
        raise ValueError("liste explicite de référentiels requise")
    if any(not isinstance(nom, str) or not nom.isidentifier() or nom.startswith("sqlite_") for nom in tables):
        raise ValueError("nom de table de référentiel invalide")
    if len(set(tables)) != len(tables):
        raise ValueError("table de référentiel dupliquée")
    # Prévalider toutes les tables avant la première insertion.
    for nom in tables:
        for connexion in (source, cible):
            if connexion.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)
            ).fetchone() is None:
                raise ValueError(f"table de référentiel absente : {nom}")
        ident = '"' + nom + '"'
        source_cols = source.execute(f"PRAGMA table_info({ident})").fetchall()
        cible_cols = cible.execute(f"PRAGMA table_info({ident})").fetchall()
        if not source_cols or source_cols != cible_cols:
            raise ValueError(f"structure de référentiel incompatible : {nom}")
        # Les colonnes identiques ne garantissent pas les mêmes contraintes FK.
        if (source.execute(f"PRAGMA foreign_key_list({ident})").fetchall() !=
                cible.execute(f"PRAGMA foreign_key_list({ident})").fetchall()):
            raise ValueError(f"clés étrangères de référentiel incompatibles : {nom}")
        if _contraintes_uniques(source, nom) != _contraintes_uniques(cible, nom):
            raise ValueError(f"contraintes uniques de référentiel incompatibles : {nom}")
        if cible.execute(f"SELECT 1 FROM {ident} LIMIT 1").fetchone():
            raise ValueError(f"table N+1 non vide : {nom}")
    # Respecter les dépendances FK même si la liste métier est inversée.
    # Détecter les cycles AVANT toute insertion pour éviter une copie partielle.
    dependances = {}
    noms = set(tables)
    for nom in tables:
        ident = '"' + nom + '"'
        parents = {ligne[2] for ligne in cible.execute(f"PRAGMA foreign_key_list({ident})")}
        dependances[nom] = (parents & noms) - {nom}
        if nom in parents:
            raise ValueError(f"référence circulaire de référentiel : {nom}")
    ordre = []
    restants = set(tables)
    while restants:
        prets = [nom for nom in tables if nom in restants and not (dependances[nom] & restants)]
        if not prets:
            raise ValueError("références circulaires entre référentiels")
        ordre.extend(prets)
        restants.difference_update(prets)
    # Le SAVEPOINT protège aussi les appels au sein d'une transaction existante.
    cible.execute("SAVEPOINT reprise_referentiels")
    try:
        for nom in ordre:
            ident = '"' + nom + '"'
            source_cols = [r[1] for r in source.execute(f"PRAGMA table_info({ident})")]
            colonnes = ", ".join('"' + col.replace('"', '""') + '"' for col in source_cols)
            marqueurs = ", ".join("?" for _ in source_cols)
            lecture = source.execute(f"SELECT {colonnes} FROM {ident}")
            cible.executemany(
                f"INSERT INTO {ident} ({colonnes}) VALUES ({marqueurs})", lecture,
            )
    except Exception:
        cible.execute("ROLLBACK TO SAVEPOINT reprise_referentiels")
        cible.execute("RELEASE SAVEPOINT reprise_referentiels")
        raise
    else:
        cible.execute("RELEASE SAVEPOINT reprise_referentiels")
