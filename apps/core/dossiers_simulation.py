"""Dossiers fictifs portables : aucun remplacement ni rattachement à la base de la société.

Module utilisable avant django.setup() : le choix de base est fait au redémarrage,
jamais en remplaçant une connexion globale pendant une requête.
"""
import datetime
import contextlib
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from pathlib import Path

FORMAT = "erp-ohada-dossier-simulation"
VERSION = 1
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_BASE = 2 * 1024 * 1024 * 1024
BASE = "simulation.sqlite3"
MANIFESTE = "dossier.json"


@contextlib.contextmanager
def verrou_generation(dossier):
    chemin = dossier / ".generation.lock"
    if chemin.is_symlink():
        raise ValueError("Verrou de génération invalide.")
    with chemin.open("a+b") as f:
        if not chemin.stat().st_size:
            f.write(b"1")
            f.flush()
        f.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError("Une génération utilise encore ce dossier.") from None
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)


def generation_active(dossier):
    if not (dossier / ".generation.lock").exists():
        return False
    try:
        with verrou_generation(dossier):
            return False
    except RuntimeError:
        return True


def ecrire_json(chemin, donnees):
    temporaire = chemin.with_name(chemin.name + ".tmp")
    temporaire.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    temporaire.replace(chemin)


def lire_json(chemin):
    if chemin.is_symlink() or chemin.stat().st_size > 32 * 1024:
        raise ValueError("Descripteur de dossier invalide.")
    try:
        d = json.loads(chemin.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        raise ValueError("Descripteur de dossier illisible.") from None
    if not isinstance(d, dict):
        raise ValueError("Descripteur de dossier invalide.")
    return d


def emplacement(racine, identifiant):
    if not re.fullmatch(r"[a-f0-9]{32}", identifiant or ""):
        raise ValueError("Dossier inconnu.")
    espace = Path(racine).resolve() / "dossiers-simulation"
    dossier = espace / identifiant
    if espace.is_symlink() or dossier.is_symlink() or (dossier / BASE).is_symlink():
        raise ValueError("Un lien de fichier ne peut pas être utilisé comme dossier de simulation.")
    return dossier


def identifiant_actif(racine):
    marqueur = Path(racine) / "dossier-actif.json"
    if not marqueur.exists():
        return ""
    identifiant = lire_json(marqueur).get("id", "")
    emplacement(racine, identifiant)
    return identifiant


def verifier_manifeste(d):
    if (not isinstance(d, dict) or d.get("format") != FORMAT or d.get("version") != VERSION or d.get("fictif") is not True
            or d.get("edition") != "transport" or d.get("etat") != "prete"):
        raise ValueError("Ce fichier n'est pas un dossier de simulation Transport prêt à ouvrir.")


@contextlib.contextmanager
def ouvrir_base(base):
    if not base.is_file() or base.is_symlink() or base.stat().st_size > MAX_BASE:
        raise ValueError("Base de simulation absente, liée ou trop volumineuse.")
    c = sqlite3.connect(base.resolve().as_uri() + "?mode=ro", uri=True, timeout=15)
    try:
        c.execute("PRAGMA trusted_schema=OFF")
        yield c
    finally:
        c.close()


def verifier_base(base):
    with ouvrir_base(base) as c:
        if c.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("Base de simulation endommagée.")
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"django_migrations", "core_societe", "auth_user", "transport_depart", "transport_billet"} <= tables:
            raise ValueError("Ce fichier ne contient pas une société de transport de l'ERP.")
        if c.execute("SELECT count(*) FROM sqlite_master WHERE type IN ('trigger','view')").fetchone()[0]:
            raise ValueError("Les vues et déclencheurs ne sont pas admis dans un dossier de simulation importé.")
        societe = c.execute("SELECT raison_sociale, activite FROM core_societe ORDER BY id LIMIT 1").fetchone()
        if not societe or societe[1] != "TRANSPORT":
            raise ValueError("L'édition de la société doit être Transport.")
        # Une base provenant d'une version plus récente ne doit jamais être ouverte en rétrogradant.
        return societe[0], set(c.execute("SELECT app, name FROM django_migrations"))


def creer(racine, debut, duree):
    identifiant = uuid.uuid4().hex
    dossier = emplacement(racine, identifiant)
    dossier.mkdir(parents=True, exist_ok=False)
    d = {"format": FORMAT, "version": VERSION, "edition": "transport", "fictif": True,
         "etat": "preparation", "nom": f"Simulation {debut}", "debut": debut, "duree": duree,
         "cree_le": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    ecrire_json(dossier / MANIFESTE, d)
    return identifiant, dossier


def terminer(dossier, erreur=""):
    d = lire_json(dossier / MANIFESTE)
    if not erreur:
        verifier_base(dossier / BASE)
    d.update(etat="erreur" if erreur else "prete", erreur=str(erreur)[:300])
    ecrire_json(dossier / MANIFESTE, d)


def lister(racine):
    espace = Path(racine) / "dossiers-simulation"
    actif = identifiant_actif(racine)
    resultat = []
    if espace.is_symlink():
        raise ValueError("Le répertoire des dossiers de simulation est invalide.")
    for chemin in sorted(espace.glob("*")) if espace.exists() else []:
        try:
            dossier = emplacement(racine, chemin.name)
            d = lire_json(dossier / MANIFESTE)
            if d.get("format") != FORMAT or d.get("fictif") is not True:
                continue
            if d.get("etat") == "preparation" and not generation_active(dossier):
                age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(d["cree_le"])
                if age.total_seconds() > 60:
                    d.update(etat="interrompue", erreur="Génération interrompue : supprimez ce dossier fictif puis relancez la création.")
            journal = dossier / "simulation-journal.txt"
            texte = ""
            if journal.is_file() and not journal.is_symlink():
                # Lecture bornée, même après plusieurs mois simulés.
                with journal.open("rb") as f:
                    f.seek(max(0, journal.stat().st_size - 4096))
                    texte = f.read(4096).decode("utf-8", errors="replace")
            resultat.append({**d, "id": chemin.name, "actif": chemin.name == actif,
                             "journal": texte, "taille": (dossier / BASE).stat().st_size if (dossier / BASE).is_file() else 0})
        except (OSError, ValueError):
            continue
    return resultat


def copier_base(source, cible):
    with ouvrir_base(source) as entree, contextlib.closing(sqlite3.connect(cible)) as sortie:
        entree.backup(sortie)


def nettoyer_copie(base, utilisateur=None):
    """Retire les sessions, autorisations de licence et secrets d'authentification de la copie exportée.
    Un administrateur local peut ensuite être créé pour le dossier importé, jamais sur la source.
    """
    with contextlib.closing(sqlite3.connect(base)) as c, c:
        c.execute("PRAGMA trusted_schema=OFF")
        c.execute("PRAGMA secure_delete=ON")
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ("django_session", "authtoken_token", "licences_etatlicence", "licences_licencedeposee"):
            if table in tables:
                c.execute(f'DELETE FROM "{table}"')
        # Le nom aléatoire évite les collisions avec un compte déjà nommé demo-<id>.
        prefixe = "fictif-" + uuid.uuid4().hex[:12] + "-"
        c.execute("UPDATE auth_user SET username=? || id, password='!', email='', first_name='', last_name='', "
                  "is_active=0, is_staff=0, is_superuser=0, last_login=NULL", [prefixe])
        if utilisateur:
            nom, hache = utilisateur
            if not nom or len(nom) > 150 or not hache or len(hache) > 128:
                raise ValueError("Identifiants de l'administrateur du dossier invalides.")
            c.execute("INSERT INTO auth_user (username,password,email,first_name,last_name,is_active,is_staff,is_superuser,date_joined) "
                      "VALUES (?,?,'','','',1,1,1,?)", [nom, hache, datetime.datetime.now(datetime.timezone.utc).isoformat()])
        c.execute("UPDATE core_societe SET assistant_termine=1")
        c.commit()
        c.execute("VACUUM")  # Retire aussi les anciennes valeurs des pages libres de la copie.


def exporter(racine, identifiant):
    dossier = emplacement(racine, identifiant)
    d = lire_json(dossier / MANIFESTE)
    verifier_manifeste(d)
    verifier_base(dossier / BASE)
    # Fichier temporaire fermé seulement par la réponse HTTP ; aucune clé/configuration du serveur exportée.
    archive = tempfile.TemporaryFile()
    try:
        with tempfile.TemporaryDirectory(prefix="erp-export-simulation-") as travail:
            copie = Path(travail) / BASE
            copier_base(dossier / BASE, copie)
            nettoyer_copie(copie)
            d = {k: v for k, v in d.items() if k in (
                "format", "version", "edition", "fictif", "etat", "nom", "debut", "duree", "cree_le")}
            d["sha256"] = empreinte(copie)
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
                z.writestr(MANIFESTE, json.dumps(d, ensure_ascii=False))
                z.write(copie, BASE)
                z.writestr("LISEZ-MOI.txt", "Données fictives. Importer depuis Administration du poste > Simulation. Aucun mot de passe, clé ou licence n'est transporté.\n")
        archive.seek(0)
        return archive
    except BaseException:
        archive.close()
        raise


def empreinte(base):
    h = hashlib.sha256()
    with base.open("rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def importer(racine, fichier, utilisateur, migrations_connues):
    identifiant, dossier = creer(racine, "importée", "")
    try:
        fichier.seek(0, 2)
        if fichier.tell() > MAX_ARCHIVE:
            raise ValueError("Archive trop volumineuse (512 Mo maximum).")
        fichier.seek(0)
        with zipfile.ZipFile(fichier) as z:
            infos = z.infolist()
            noms = [i.filename for i in infos]
            if (len(noms) != len(set(noms)) or not {MANIFESTE, BASE} <= set(noms)
                    or set(noms) - {MANIFESTE, BASE, "LISEZ-MOI.txt"}):
                raise ValueError("Contenu d'archive inattendu ; seul un dossier de simulation exporté par le logiciel est accepté.")
            if z.getinfo(MANIFESTE).file_size > 32 * 1024 or z.getinfo(BASE).file_size > MAX_BASE:
                raise ValueError("Contenu décompressé trop volumineux.")
            d = json.loads(z.read(MANIFESTE))
            verifier_manifeste(d)
            with z.open(BASE) as entree, (dossier / BASE).open("wb") as sortie:
                total = 0
                for bloc in iter(lambda: entree.read(1024 * 1024), b""):
                    total += len(bloc)
                    if total > MAX_BASE:
                        raise ValueError("Base décompressée trop volumineuse.")
                    sortie.write(bloc)
        if d.get("sha256") != empreinte(dossier / BASE):
            raise ValueError("Le dossier a été altéré ou son transfert est incomplet.")
        _, migrations = verifier_base(dossier / BASE)
        if migrations - set(migrations_connues):
            raise ValueError("Ce dossier provient d'une version plus récente ou inconnue : mettez d'abord le logiciel à jour.")
        nettoyer_copie(dossier / BASE, utilisateur)
        d.pop("sha256", None)
        d["nom"] = str(d.get("nom") or "Simulation importée")[:150]
        ecrire_json(dossier / MANIFESTE, d)
        return identifiant
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError, TypeError, UnicodeError, RuntimeError) as exc:
        shutil.rmtree(dossier)
        raise ValueError("Import refusé : " + str(exc)[:250]) from None


def prevoir_ouverture(racine, identifiant, sauvegarder):
    if identifiant:
        dossier = emplacement(racine, identifiant)
        verifier_manifeste(lire_json(dossier / MANIFESTE))
        verifier_base(dossier / BASE)
    if not sauvegarder():
        raise ValueError("La sauvegarde préalable n'a pas été confirmée.")
    marqueur = Path(racine) / "dossier-actif.json"
    if identifiant:
        ecrire_json(marqueur, {"id": identifiant})
    else:
        marqueur.unlink(missing_ok=True)


def environnement_actif(racine, env):
    identifiant = identifiant_actif(racine)
    if not identifiant:
        return Path(racine)
    dossier = emplacement(racine, identifiant)
    verifier_manifeste(lire_json(dossier / MANIFESTE))
    verifier_base(dossier / BASE)
    config = dossier / "configuration.env"
    if not config.exists():
        import secrets
        config.write_text("SECRET_KEY=" + secrets.token_urlsafe(50) + "\n", encoding="utf-8")
    secret = next((l.split("=", 1)[1] for l in config.read_text().splitlines() if l.startswith("SECRET_KEY=")), "")
    if not secret:
        raise ValueError("Configuration locale du dossier fictif incomplète.")
    # Valider tout le dossier avant de remplacer les paramètres du processus.
    for cle in list(env):
        if cle.startswith(("DB_", "MIROIR_", "ECHANGES_", "ERP_SAUVEGARDE_", "ERP_VERIFICATION_")):
            env.pop(cle, None)
    env.update(DB_ENGINE="sqlite", SQLITE_FICHIER=str(dossier / BASE), SECRET_KEY=secret,
               ERP_DOSSIER_DONNEES=str(dossier), ERP_DOSSIER_SIMULATION=identifiant,
               ERP_SESSION_COOKIE="erp_simulation_" + identifiant,
               CONTROLE_HEURE_DEPART="0")
    return dossier


def supprimer(racine, identifiant):
    dossier = emplacement(racine, identifiant)
    if identifiant == identifiant_actif(racine):
        raise ValueError("Revenez au dossier de la société avant de supprimer cette simulation.")
    if generation_active(dossier):
        raise ValueError("Une génération utilise encore ce dossier.")
    if lire_json(dossier / MANIFESTE).get("fictif") is not True:
        raise ValueError("Seul un dossier fictif reconnu peut être supprimé.")
    shutil.rmtree(dossier)
