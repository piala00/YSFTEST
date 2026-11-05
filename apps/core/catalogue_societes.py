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
    localisations = set()
    exercices = set()
    bases = []
    for entree in donnees["bases"]:
        champs = ("id", "societe", "agence", "exercice", "moteur", "base")
        if not isinstance(entree, dict) or any(not isinstance(entree.get(k), str) or not entree[k].strip() for k in champs):
            raise ValueError("Métadonnées de société incomplètes")
        if entree["id"] in identifiants:
            raise ValueError("Identifiant de base dupliqué")
        if entree["moteur"] not in ("sqlite", "mssql") or not isinstance(entree.get("cloture", False), bool):
            raise ValueError("Moteur ou clôture invalide")
        localisation = (entree["moteur"], entree["base"].casefold() if entree["moteur"] == "mssql" else entree["base"])
        if len(entree["exercice"]) != 4 or not entree["exercice"].isascii() or not entree["exercice"].isdigit() or int(entree["exercice"]) < 1 or int(entree["exercice"]) >= 9999:
            raise ValueError("Année d’exercice invalide (AAAA attendu)")
        exercice = (entree["societe"].casefold(), entree["agence"].casefold(), entree["exercice"])
        if localisation in localisations:
            raise ValueError("Base physique dupliquée dans le catalogue")
        if exercice in exercices:
            raise ValueError("Exercice société/agence dupliqué")
        identifiants.add(entree["id"])
        localisations.add(localisation)
        exercices.add(exercice)
        bases.append({**entree, "cloture": entree.get("cloture", False)})
    # Un exercice N+1 ne doit jamais pointer vers une autre société/agence,
    # une année incorrecte ou un exercice N encore ouvert.
    par_id = {base["id"]: base for base in bases}
    for entree in bases:
        parent_id = entree.get("exercice_precedent")
        if parent_id is None:
            continue
        if not isinstance(parent_id, str) or parent_id not in par_id or parent_id == entree["id"]:
            raise ValueError("Lien historique d'exercice invalide")
        parent = par_id[parent_id]
        if (parent["societe"].casefold() != entree["societe"].casefold() or
                parent["agence"].casefold() != entree["agence"].casefold() or
                not parent["exercice"].isdigit() or not entree["exercice"].isdigit() or
                int(entree["exercice"]) != int(parent["exercice"]) + 1 or
                not parent["cloture"]):
            raise ValueError("Lien historique d'exercice incohérent")
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


def enregistrer_exercice_suivant(fichier, identifiant_precedent, nouvelle_base, nouvel_identifiant):
    """Publie le lien N → N+1 après création et validation de la nouvelle base.

    Ne crée ni ne clôture les bases : l'appelant doit achever la clôture,
    les reports et la vérification de la nouvelle base AVANT cette publication.
    Un fichier existant n'est jamais écrasé et l'écriture est atomique.
    """
    import os
    import tempfile

    chemin = Path(fichier)
    if not chemin.is_file():
        raise ValueError("catalogue multi-sociétés absent")
    bases = lire_catalogue(chemin)
    precedentes = [b for b in bases if b["id"] == identifiant_precedent]
    if len(precedentes) != 1:
        raise ValueError("exercice précédent introuvable")
    precedente = precedentes[0]
    if precedente["cloture"]:
        raise ValueError("exercice précédent déjà clôturé")
    if not precedente["exercice"].isdigit() or len(precedente["exercice"]) != 4:
        raise ValueError("année précédente invalide")
    if not isinstance(nouvel_identifiant, str) or not nouvel_identifiant.strip():
        raise ValueError("identifiant du nouvel exercice requis")
    if not isinstance(nouvelle_base, str) or not nouvelle_base.strip():
        raise ValueError("base du nouvel exercice requise")
    if int(precedente["exercice"]) >= 9998:
        raise ValueError("Année suivante hors limites")
    annee = f"{int(precedente['exercice']) + 1:04d}"
    if any(b["id"] == nouvel_identifiant or
           (b["societe"].casefold() == precedente["societe"].casefold() and
            b["agence"].casefold() == precedente["agence"].casefold() and b["exercice"] == annee)
           for b in bases):
        raise ValueError("exercice suivant déjà enregistré")
    if any(b["moteur"] == precedente["moteur"] and
           (b["base"].casefold() == nouvelle_base.casefold() if precedente["moteur"] == "mssql"
            else b["base"] == nouvelle_base) for b in bases):
        raise ValueError("base déjà enregistrée")
    # Interdit aussi les alias physiques lorsque ce point d’entrée est appelé directement.
    # Ne pas exiger ici que la nouvelle base existe : le flux MSSQL est distinct.
    if precedente["moteur"] == "sqlite":
        cible = Path(nouvelle_base)
        for entree in bases:
            if entree["moteur"] != "sqlite":
                continue
            source = Path(entree["base"])
            if source.resolve() == cible.resolve():
                raise ValueError("base physique déjà enregistrée")
            if source.is_file() and cible.is_file() and source.samefile(cible):
                raise ValueError("base physique déjà enregistrée")
    suivante = {
        "id": nouvel_identifiant, "societe": precedente["societe"],
        "agence": precedente["agence"], "exercice": annee,
        "moteur": precedente["moteur"], "base": nouvelle_base,
        "cloture": False, "exercice_precedent": precedente["id"],
    }
    nouvelle_liste = [
        {**b, "cloture": True} if b["id"] == identifiant_precedent else b
        for b in bases
    ] + [suivante]
    # Contrôle intégral avant publication : aucune entrée existante perdue.
    temporaire = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=chemin.parent,
            prefix=".societes-", suffix=".tmp", delete=False,
        ) as flux:
            temporaire = Path(flux.name)
            json.dump({"version": 1, "bases": nouvelle_liste}, flux, ensure_ascii=False, indent=2)
            flux.write("
")
            flux.flush()
            os.fsync(flux.fileno())
        lire_catalogue(temporaire)
        os.replace(temporaire, chemin)
    finally:
        if temporaire is not None:
            temporaire.unlink(missing_ok=True)
    return suivante


def publier_exercice_sqlite_valide(fichier, identifiant_precedent, nouvelle_base, nouvel_identifiant):
    """Publie N+1 seulement après vérification physique de sa base SQLite ERP.

    Cette opération ne crée pas la base ni les reports à nouveau : le service de
    clôture doit les terminer avant de l'appeler. En cas d'échec, le catalogue
    reste inchangé et l'exercice N reste ouvert dans ce catalogue.
    """
    bases = lire_catalogue(fichier)
    precedente = next((b for b in bases if b["id"] == identifiant_precedent), None)
    if precedente is None:
        raise ValueError("exercice précédent introuvable")
    if precedente["moteur"] != "sqlite":
        raise ValueError("publication SQLite réservée aux bases SQLite")
    # Une autre orthographe du même chemin (.., lien symbolique ou lien physique) ne doit
    # jamais faire publier la base de l'exercice N comme celle de N+1.
    base_verifiee = verifier_base_sqlite(nouvelle_base)
    for entree in bases:
        if entree["moteur"] == "sqlite" and (
            Path(entree["base"]).resolve() == Path(base_verifiee) or
            (Path(entree["base"]).is_file() and
             Path(entree["base"]).stat().st_dev == Path(base_verifiee).stat().st_dev and
             Path(entree["base"]).stat().st_ino == Path(base_verifiee).stat().st_ino)
        ):
            raise ValueError("base physique déjà enregistrée")
    return enregistrer_exercice_suivant(
        fichier, identifiant_precedent, base_verifiee, nouvel_identifiant,
    )
