"""Catalogue des bases par société, agence et exercice, sans connexion implicite."""
import json
from pathlib import Path


def lire_catalogue(fichier):
    chemin = Path(fichier)
    if not chemin.is_file():
        return []
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    if not isinstance(donnees, dict) or donnees.get("version") != 1 or not isinstance(donnees.get("bases"), list):
        raise ValueError("Catalogue multi-sociétés invalide")
    identifiants = set()
    bases = []
    for entree in donnees["bases"]:
        champs = ("id", "societe", "agence", "exercice", "moteur", "base")
        if not isinstance(entree, dict) or any(not isinstance(entree.get(k), str) or not entree[k].strip() for k in champs):
            raise ValueError("Métadonnées de société incomplètes")
        if entree["id"] in identifiants:
            raise ValueError("Identifiant de base dupliqué")
        if entree["moteur"] not in ("sqlite", "mssql") or not isinstance(entree.get("cloture", False), bool):
            raise ValueError("Moteur ou clôture invalide")
        identifiants.add(entree["id"])
        bases.append({**entree, "cloture": entree.get("cloture", False)})
    return bases


def regrouper(bases, recherche="", afficher_clotures=False):
    """Filtre puis regroupe Société → Agence → exercices (récents d'abord)."""
    terme = recherche.strip().casefold()
    groupes = {}
    for base in bases:
        if base["cloture"] and not afficher_clotures:
            continue
        if terme and terme not in " ".join(str(base[k]) for k in ("societe", "agence", "exercice")).casefold():
            continue
        groupes.setdefault(base["societe"], {}).setdefault(base["agence"], []).append(base)
    return [{"societe": nom, "agences": [
        {"agence": agence, "exercices": sorted(exercices, key=lambda b: (b["exercice"], b["id"]), reverse=True)}
        for agence, exercices in sorted(agences.items(), key=lambda x: x[0].casefold())]}
        for nom, agences in sorted(groupes.items(), key=lambda x: x[0].casefold())]


def verifier_base_sqlite(nom):
    """Refuse une base absente, non ERP ou dont le chemin est ambigu."""
    import sqlite3
    from urllib.parse import quote
    chemin = Path(nom)
    if not chemin.is_absolute() or not chemin.is_file():
        raise ValueError("fichier SQLite absolu existant requis")
    # Mode lecture seule : ne crée ni ne modifie la base ciblée.
    uri = "file:" + quote(str(chemin.resolve()), safe="/:") + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=3) as base:
            tables = {r[0] for r in base.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"django_migrations", "auth_user", "core_societe"}.issubset(tables):
                raise ValueError("la base sélectionnée n'est pas une base ERP compatible")
            resultat = base.execute("PRAGMA quick_check").fetchone()
            if not resultat or resultat[0] != "ok":
                raise ValueError("la base sélectionnée est endommagée")
    except sqlite3.DatabaseError as exc:
        raise ValueError("base SQLite illisible") from exc
    return str(chemin.resolve())
