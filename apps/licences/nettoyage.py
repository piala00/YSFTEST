"""Inventaire et sauvegarde vérifiée avant suppression ciblée ; aucune connexion SQL Server."""
from contextlib import closing
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import shutil
import tempfile
import zipfile

MARQUEUR = ".erp-produit"
DONNEES = re.compile(r"^(configuration(?:-[0-9-]+)?\.env|erp(?:-avant-restauration-[0-9-]+)?\.sqlite3(?:-wal|-shm)?|"
                     r"simulation\.sqlite3(?:-wal|-shm)?|journal\.txt|simulation-journal\.txt|\.erp-essai|"
                     r"installation\.dat|cle-installation\.txt|role-installation\.txt|installation-agence\.erpx|"
                     r"installation-base\.env(?:\.applique)?|base-creee\.txt|erreur-base\.txt|dossier-actif\.json|"
                     r"dossier-erreur\.txt|dossier-refuse-[0-9-]+\.json|restaurer-au-demarrage\.txt|restaurer-sqlserver\.txt)$")


def sur(p):
    p = Path(p).absolute()
    for c in (p, *p.parents):
        if c.exists() or c.is_symlink():
            s = c.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
                raise ValueError(f"Lien ou point de réanalyse refusé : {c}")
    if p.resolve() != p:
        raise ValueError(f"Chemin indirect refusé : {p}")
    return p


def digest(p):
    sur(p)
    if not stat.S_ISREG(p.lstat().st_mode):
        raise ValueError(f"Fichier spécial refusé : {p}")
    if p.stat().st_nlink != 1:
        raise ValueError(f"Lien dur refusé : {p}")
    h = hashlib.sha256()
    with p.open("rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def marquer(racine, edition):
    if edition not in ("transport", "commerce"):
        raise ValueError("Édition inconnue.")
    racine = sur(racine)
    racine.mkdir(parents=True, exist_ok=True)
    fichier = racine / MARQUEUR
    if fichier.exists():
        digest(fichier)
        if fichier.read_text(encoding="utf-8") != edition:
            raise ValueError("Ce dossier appartient à une autre édition.")
    else:
        # Le marqueur ne suffit pas à déclarer tous les fichiers propriétaires : la liste blanche reste appliquée.
        with fichier.open("x", encoding="utf-8") as f:
            f.write(edition)


def inventorier(programme, donnees, edition):
    if edition not in ("transport", "commerce"):
        raise ValueError("Édition inconnue.")
    racines = {"programme": sur(programme), "donnees": sur(donnees)}
    p, d = racines.values()
    if p == d or p in d.parents or d in p.parents:
        raise ValueError("Les dossiers programme et données doivent être distincts et indépendants.")
    plan = {"version": 2, "edition": edition, "racines": {k: str(v) for k, v in racines.items()},
            "fichiers": [], "repertoires": [], "conserves": [], "avertissements": [
                "Aucune base SQL Server, aucun chemin SQLite externe ni dossier partagé ne sera effacé.",
                "La mémoire d'essai HKCU\\Software\\ERP-OHADA est commune aux éditions : conservée.",
                "Les profils d'autres utilisateurs Windows et leurs raccourcis ne sont pas parcourus."]}
    for genre, racine in racines.items():
        if not racine.exists():
            continue
        marqueur = racine / MARQUEUR
        try:
            reconnue = marqueur.is_file() and digest(marqueur) and marqueur.read_text(encoding="utf-8") == edition
        except (OSError, ValueError):
            reconnue = False
        # Anciennes données : seul le chemin standard explicitement nommé est reconnu, jamais un parent partagé.
        ancienne = (not marqueur.exists() and not marqueur.is_symlink() and genre == "donnees"
                    and racine.name.lower() == edition and racine.parent.name == "ERP-OHADA")
        if reconnue or ancienne:
            plan["repertoires"].append({"genre": genre, "relatif": ""})
        for dossier, repertoires, noms in os.walk(racine, followlinks=False):
            for nom in list(repertoires):
                enfant = Path(dossier) / nom
                try:
                    sur(enfant)
                    premier = enfant.relative_to(racine).parts[0]
                    dossier_attribue = ((genre == "donnees" and (reconnue or ancienne) and premier in ("sauvegardes", "dossiers-simulation"))
                                        or (genre == "programme" and reconnue and premier in ("journaux-service", "_internal")))
                    if dossier_attribue:
                        plan["repertoires"].append({"genre": genre, "relatif": enfant.relative_to(racine).as_posix()})
                    else:
                        plan["conserves"].append({"chemin": str(enfant), "raison": "Dossier non attribué exclusivement à l'application."})
                except ValueError as exc:
                    repertoires.remove(nom)
                    plan["conserves"].append({"chemin": str(enfant), "raison": str(exc)})
            for nom in sorted(noms):
                f = Path(dossier) / nom
                rel = f.relative_to(racine)
                connu = rel.as_posix() == MARQUEUR and reconnue
                if genre == "donnees" and (reconnue or ancienne):
                    connu |= (len(rel.parts) == 1 and bool(DONNEES.fullmatch(nom)))
                    connu |= (rel.parts[0] == "sauvegardes" and nom.startswith("erp-") and f.suffix in (".sqlite3", ".json", ".bak"))
                    connu |= (rel.parts[0] == "dossiers-simulation" and f.suffix in (".sqlite3", ".json", ".md", ".txt"))
                if genre == "programme" and reconnue:
                    connu |= (rel.parts[0] == "journaux-service" and nom.startswith(f"ERP-OHADA-{edition.capitalize()}")
                              and (nom.endswith(".log") or ".log." in nom))
                    connu |= (rel.parts[0] == "_internal" and len(rel.parts) > 3 and rel.parts[1] in ("apps", "erp", "django")
                              and "__pycache__" in rel.parts and f.suffix == ".pyc")
                try:
                    if not connu:
                        raise ValueError("Fichier non attribué exclusivement à cette application.")
                    sha = digest(f)
                    plan["fichiers"].append({"genre": genre, "relatif": rel.as_posix(), "taille": f.stat().st_size, "sha256": sha})
                except (ValueError, OSError) as exc:
                    plan["conserves"].append({"chemin": str(f), "raison": str(exc)})
    plan["fichiers"].sort(key=lambda f: (f["genre"], f["relatif"]))
    plan["repertoires"].sort(key=lambda d: (d["genre"], d["relatif"]))
    plan["conserves"].sort(key=lambda f: f["chemin"])
    return plan


def _verifier_plan(plan):
    courant = inventorier(plan["racines"]["programme"], plan["racines"]["donnees"], plan["edition"])
    if courant != plan:
        raise ValueError("L'inventaire a changé ; réexaminez un nouvel inventaire avant suppression.")


def sauvegarder(plan, destination):
    """Une archive exclusive hors des racines, relue et comparée aux empreintes de l'inventaire."""
    _verifier_plan(plan)
    destination = sur(destination)
    for racine in map(Path, plan["racines"].values()):
        if destination == racine or racine in destination.parents:
            raise ValueError("La sauvegarde doit être placée hors des dossiers à nettoyer.")
    # Même mode=ro peut créer/modifier les annexes WAL/SHM. Ne jamais ouvrir la source avec SQLite.
    # La copie d'archive reste immuable ; une seconde copie sert uniquement au contrôle SQLite.
    with tempfile.TemporaryDirectory(prefix="erp-sauvegarde-controle-", dir=destination.parent) as travail:
        instantane = Path(travail) / "instantane"
        for d in plan["repertoires"]:
            (instantane / d["genre"] / d["relatif"]).mkdir(parents=True, exist_ok=True)
        for f in plan["fichiers"]:
            source = Path(plan["racines"][f["genre"]]) / f["relatif"]
            copie = instantane / f["genre"] / f["relatif"]
            copie.parent.mkdir(parents=True, exist_ok=True)
            sur(source)
            shutil.copyfile(source, copie, follow_symlinks=False)
            if digest(copie) != f["sha256"]:
                raise ValueError("Fichier modifié pendant la copie ; refaire l'inventaire.")
        _verifier_plan(plan)
        for f in plan["fichiers"]:
            copie = instantane / f["genre"] / f["relatif"]
            if copie.suffix != ".sqlite3":
                continue
            with tempfile.TemporaryDirectory(prefix="sqlite-", dir=travail) as controle:
                base = Path(controle) / copie.name
                for suffixe in ("", "-wal", "-shm"):
                    annexe = Path(str(copie) + suffixe)
                    if annexe.is_file():
                        shutil.copyfile(annexe, Path(str(base) + suffixe))
                try:
                    with closing(sqlite3.connect(base.as_uri() + "?mode=ro", uri=True)) as c:
                        if c.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                            raise ValueError(f"Base SQLite à réparer avant suppression : {f['relatif']}")
                except sqlite3.Error:
                    raise ValueError(f"Contrôle SQLite impossible ; aucune suppression : {f['relatif']}") from None
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("INVENTAIRE.json", json.dumps(plan, ensure_ascii=False, indent=2))
            for d in plan["repertoires"]:
                z.writestr(d["genre"] + "/" + (d["relatif"] + "/" if d["relatif"] else ""), b"")
            for f in plan["fichiers"]:
                z.write(instantane / f["genre"] / f["relatif"], f["genre"] + "/" + f["relatif"])
    verifier_sauvegarde(plan, destination)
    _verifier_plan(plan)
    return destination


def verifier_sauvegarde(plan, archive):
    sur(archive)
    digest(Path(archive))  # refuse aussi les liens durs
    with zipfile.ZipFile(archive) as z:
        attendus = {"INVENTAIRE.json", *(f["genre"] + "/" + f["relatif"] for f in plan["fichiers"])}
        repertoires = {d["genre"] + "/" + (d["relatif"] + "/" if d["relatif"] else "") for d in plan["repertoires"]}
        attendus.update(repertoires)
        if len(z.namelist()) != len(attendus) or set(z.namelist()) != attendus:
            raise ValueError("Contenu d'archive inattendu ou dupliqué ; aucune suppression.")
        if json.loads(z.read("INVENTAIRE.json")) != plan:
            raise ValueError("L'archive ne correspond pas à l'inventaire approuvé.")
        if any(z.getinfo(nom).file_size for nom in repertoires):
            raise ValueError("Répertoire d'archive altéré ; aucune suppression.")
        for f in plan["fichiers"]:
            if z.getinfo(f["genre"] + "/" + f["relatif"]).file_size != f["taille"]:
                raise ValueError("Taille d'archive incohérente ; aucune suppression.")
            with z.open(f["genre"] + "/" + f["relatif"]) as entree:
                h = hashlib.sha256()
                for bloc in iter(lambda: entree.read(1024 * 1024), b""):
                    h.update(bloc)
            if h.hexdigest() != f["sha256"]:
                raise ValueError("Sauvegarde altérée ou incomplète ; aucune suppression.")


def effacer(plan, archive, *, confirmation=False):
    if confirmation is not True:
        raise ValueError("Confirmation explicite requise après inventaire et sauvegarde.")
    for racine in map(Path, plan["racines"].values()):
        if Path(archive).resolve() == racine or racine in Path(archive).resolve().parents:
            raise ValueError("Sauvegarde dans un dossier à nettoyer : refusé.")
    verifier_sauvegarde(plan, archive)
    _verifier_plan(plan)
    rapport = Path(archive).with_suffix(".rapport.json")
    # Réserver le journal avant toute suppression : une collision ou un défaut de droit ne doit rien effacer.
    journal = rapport.open("x", encoding="utf-8")
    json.dump({"etat": "en-cours", "sauvegarde": str(archive), "inventaire": plan}, journal, ensure_ascii=False)
    journal.flush()
    os.fsync(journal.fileno())
    resultat = {"supprimes": [], "repertoires_supprimes": [], "erreurs": [], "conserves": list(plan["conserves"]), "sauvegarde": str(archive)}
    genres_en_erreur = set()
    dossiers_attribues = {Path(plan["racines"][d["genre"]]) / d["relatif"] for d in plan["repertoires"]}
    for f in plan["fichiers"]:
        racine = Path(plan["racines"][f["genre"]])
        courant = (racine / f["relatif"]).parent
        while courant == racine or racine in courant.parents:
            dossiers_attribues.add(courant)
            if courant == racine:
                break
            courant = courant.parent
    # Garder l'identité du dossier pour une reprise si un fichier n'a pas pu être supprimé.
    fichiers = sorted(plan["fichiers"], key=lambda f: (f["relatif"] == MARQUEUR, f["genre"], f["relatif"]))
    for f in fichiers:
        chemin = Path(plan["racines"][f["genre"]]) / f["relatif"]
        if f["relatif"] == MARQUEUR and f["genre"] in genres_en_erreur:
            resultat["conserves"].append({"chemin": str(chemin), "raison": "Marqueur conservé pour reprendre les fichiers non supprimés."})
            continue
        try:
            if digest(chemin) != f["sha256"]:
                raise ValueError("Fichier modifié après vérification.")
            try:
                chemin.unlink()
            except PermissionError:
                mode = stat.S_IMODE(chemin.stat().st_mode)
                if mode & stat.S_IWRITE:
                    raise  # ACL ou verrou : ne jamais prendre possession ni élargir les droits.
                if digest(chemin) != f["sha256"]:
                    raise ValueError("Fichier modifié avant retrait de l'attribut lecture seule.")
                chemin.chmod(mode | stat.S_IWRITE)
                try:
                    chemin.unlink()
                except OSError as exc:
                    if chemin.exists():
                        sur(chemin)
                        try:
                            chemin.chmod(mode)
                        except OSError as restauration:
                            raise OSError(f"{exc} ; attribut initial non rétabli : {restauration}") from exc
                    raise
            resultat["supprimes"].append(str(chemin))
        except (OSError, ValueError) as exc:
            genres_en_erreur.add(f["genre"])
            resultat["erreurs"].append({"chemin": str(chemin), "raison": str(exc)})
    for dossier in sorted(dossiers_attribues, key=lambda p: len(p.parts), reverse=True):
        try:
            sur(dossier).rmdir()  # uniquement vide et attribué ; jamais un dossier inconnu ou un parent partagé
            resultat["repertoires_supprimes"].append(str(dossier))
        except (OSError, ValueError) as exc:
            if not isinstance(exc, OSError) or exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                resultat["erreurs"].append({"chemin": str(dossier), "raison": str(exc)})
    try:
        journal.seek(0)
        journal.truncate()
        json.dump(resultat, journal, ensure_ascii=False, indent=2)
        journal.flush()
        os.fsync(journal.fileno())
    finally:
        journal.close()
    return resultat
