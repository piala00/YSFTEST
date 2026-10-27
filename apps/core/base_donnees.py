"""Gestion de la base de données à l'écran (Fichier › Administration du poste › Base de données).

SQLite (fichier sur ce serveur) ou SQL Server (base dédiée à l'ERP) : état, vérification, réparation, optimisation,
sauvegarde et restauration, et changement de moteur (copie complète contrôlée table par table).
Jamais une base d'un autre logiciel : une base qui contient d'autres tables que celles de l'ERP est refusée.
"""
import datetime
import sqlite3
import threading
from pathlib import Path

from django.conf import settings
from django.db import connection, connections

LIBELLES = {"sqlite": "SQLite (fichier sur ce serveur)", "mssql": "SQL Server", "postgresql": "PostgreSQL"}


def moteur(alias="default"):
    engine = connections.databases[alias]["ENGINE"]
    return "sqlite" if "sqlite" in engine else "mssql" if engine == "mssql" else "postgresql" if "postgresql" in engine else engine


def _nom(alias="default"):
    return str(connections.databases[alias]["NAME"])


# ---------------------------------------------------------------- État
def info():
    m, reglage = moteur(), connections.databases["default"]
    d = {"moteur": m, "libelle": LIBELLES.get(m, m), "tables": len(connection.introspection.table_names()),
         "miroir": "miroir" in connections.databases}
    if m == "sqlite":
        with connection.cursor() as cur:
            cur.execute("PRAGMA page_count")
            pages = cur.fetchone()[0]
            cur.execute("PRAGMA page_size")
            taille = pages * cur.fetchone()[0]
        d.update(emplacement=str(reglage["NAME"]), version=f"SQLite {sqlite3.sqlite_version}", taille=taille)
    elif m == "mssql":
        with connection.cursor() as cur:
            cur.execute("SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(40)), "
                        "CAST(SERVERPROPERTY('Edition') AS nvarchar(100)), SUM(CAST(size AS bigint)) * 8192 "
                        "FROM sys.database_files")
            version, edition, taille = cur.fetchone()
            cur.execute("SELECT recovery_model_desc FROM sys.databases WHERE name = DB_NAME()")
            recuperation = cur.fetchone()[0]
        d.update(emplacement=f"{reglage.get('HOST') or 'localhost'} · base {reglage['NAME']}",
                 version=f"SQL Server {version} ({edition})", taille=int(taille or 0), recuperation=recuperation,
                 compte=reglage.get("USER") or "compte Windows")
    else:
        d.update(emplacement=f"{reglage.get('HOST')} · {reglage['NAME']}", version="", taille=0)
    return d


# ---------------------------------------------------------------- Vérifier, réparer, optimiser
def verifier():
    """(intègre ?, messages). SQLite : integrity_check + clés étrangères ; SQL Server : DBCC CHECKDB."""
    m = moteur()
    with connection.cursor() as cur:
        if m == "sqlite":
            cur.execute("PRAGMA integrity_check")
            resultats = [r[0] for r in cur.fetchall()]
            cur.execute("PRAGMA foreign_key_check")
            orphelins = cur.fetchall()
            messages = [] if resultats == ["ok"] else resultats[:20]
            if orphelins:
                messages.append(f"{len(orphelins)} ligne(s) qui pointent vers une ligne absente "
                                f"(tables : {', '.join(sorted({o[0] for o in orphelins})[:5])})")
            return not messages, messages or ["Base intègre : aucune erreur."]
        if m == "mssql":
            try:
                cur.execute(f"DBCC CHECKDB (N'{_nom()}') WITH NO_INFOMSGS, ALL_ERRORMSGS")
                lignes = cur.fetchall() if cur.description else []
            except Exception as exc:                               # erreurs de cohérence remontées comme exceptions
                return False, [str(exc)[:500]]
            return not lignes, [str(l)[:300] for l in lignes[:20]] or ["DBCC CHECKDB : aucune erreur de cohérence."]
    return True, ["Vérification à faire avec les outils du serveur de base de données."]


def optimiser():
    """Réindexation et statistiques (les deux moteurs) ; SQLite : la base est aussi compactée."""
    m = moteur()
    with connection.cursor() as cur:
        if m == "sqlite":
            cur.execute("REINDEX")
            cur.execute("ANALYZE")
            cur.execute("PRAGMA optimize")
            if connection.in_atomic_block:
                return "Index reconstruits, statistiques à jour."
            cur.execute("VACUUM")                                 # compactage (hors transaction)
            return "Index reconstruits, statistiques à jour, base compactée."
        if m == "mssql":
            tables = connection.introspection.table_names()
            for t in tables:
                cur.execute(f"ALTER INDEX ALL ON [{t}] REBUILD")
            cur.execute("EXEC sp_updatestats")
            return f"Index reconstruits sur {len(tables)} tables, statistiques à jour."
    return "Rien à faire pour ce moteur."


def reparer():
    """Réparation sûre : réindexation puis nouvelle vérification. Une base encore abîmée se répare en restaurant
    la dernière sauvegarde saine (jamais de réparation qui accepte de perdre des données)."""
    message = optimiser()
    intacte, details = verifier()
    if intacte:
        return True, f"{message} Vérification : aucune erreur."
    return False, (f"{message} Des erreurs restent : restaurez la dernière sauvegarde saine (liste ci-dessous). "
                   + " ; ".join(details[:3]))


# ---------------------------------------------------------------- SQL Server : sauvegarde et restauration natives
def dossier_sauvegarde_sqlserver(alias="default"):
    """Dossier des sauvegardes SUR LE SERVEUR SQL (ERP_SAUVEGARDE_SQL_DOSSIER, sinon celui de l'instance)."""
    import os

    if os.environ.get("ERP_SAUVEGARDE_SQL_DOSSIER"):                # réglé à l'écran (sans redémarrage)
        return os.environ["ERP_SAUVEGARDE_SQL_DOSSIER"].rstrip("\\/")
    with connections[alias].cursor() as cur:
        cur.execute("SELECT CAST(SERVERPROPERTY('InstanceDefaultBackupPath') AS nvarchar(400))")
        return (cur.fetchone()[0] or "").rstrip("\\/")


def sauvegarder_sqlserver(alias="default", base=None, motif=""):
    """BACKUP DATABASE … WITH CHECKSUM, COPY_ONLY (n'interfère pas avec les sauvegardes du service informatique),
    puis RESTORE VERIFYONLY. Renvoie le chemin du fichier .bak sur le serveur SQL."""
    base = base or _nom(alias)
    dossier = dossier_sauvegarde_sqlserver(alias)
    separateur = "\\" if "\\" in dossier or ":" in dossier[:3] else "/"
    # Nom toujours unique : deux sauvegardes dans la même seconde (ex. celle faite juste avant une restauration)
    # ne doivent jamais s'écraser — WITH INIT remplacerait la sauvegarde que l'on veut restaurer
    import uuid

    fichier = (f"{dossier}{separateur}ERP-{base}-{datetime.datetime.now():%Y%m%d-%H%M%S}"
               f"{'-' + motif if motif else ''}-{uuid.uuid4().hex[:6]}.bak")
    with connections[alias].cursor() as cur:
        cur.execute(f"BACKUP DATABASE [{base}] TO DISK = N'{fichier}' WITH INIT, CHECKSUM, COPY_ONLY")
        while cur.nextset():                                       # messages de progression de BACKUP
            pass
        cur.execute(f"RESTORE VERIFYONLY FROM DISK = N'{fichier}' WITH CHECKSUM")
        while cur.nextset():
            pass
    return fichier


def sauvegardes_sqlserver(alias="default", base=None, nombre=30):
    """Sauvegardes complètes connues du serveur (historique msdb), de la plus récente à la plus ancienne."""
    base = base or _nom(alias)
    with connections[alias].cursor() as cur:
        cur.execute(f"SELECT TOP {int(nombre)} f.physical_device_name, s.backup_finish_date, s.backup_size "
                    "FROM msdb.dbo.backupset s JOIN msdb.dbo.backupmediafamily f ON f.media_set_id = s.media_set_id "
                    "WHERE s.database_name = %s AND s.type = 'D' ORDER BY s.backup_finish_date DESC", [base])
        return [{"nom": r[0], "date": r[1], "taille": int(r[2] or 0)} for r in cur.fetchall()]


def restaurer_sqlserver(reglage, fichier):
    """Remplace la base par la sauvegarde (connexion à « master »). La base actuelle est d'abord sauvegardée.
    À faire au démarrage du logiciel, quand personne n'est connecté."""
    base = reglage["NAME"]
    if not fichier.lower().endswith(".bak") or "'" in fichier:
        raise ValueError("fichier de sauvegarde SQL Server attendu (.bak)")
    from apps.core.management.commands.miroir import connexion_temporaire

    with connexion_temporaire("_maitre", {**reglage, "NAME": "master"}) as maitre:
        avant = sauvegarder_sqlserver("_maitre", base, motif="avant-restauration")
        if avant == fichier:                                      # impossible avec un nom unique, mais jamais d'écrasement
            raise RuntimeError("la sauvegarde de sécurité porterait le nom de la sauvegarde à restaurer")
        with maitre.cursor() as cur:
            cur.execute(f"ALTER DATABASE [{base}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            try:
                cur.execute(f"RESTORE DATABASE [{base}] FROM DISK = N'{fichier}' WITH REPLACE, CHECKSUM")
                while cur.nextset():
                    pass
            finally:
                cur.execute(f"ALTER DATABASE [{base}] SET MULTI_USER")
    return avant


# ---------------------------------------------------------------- Changer de moteur
def reglage_sqlserver(hote, base, utilisateur="", mot_de_passe="", port=""):
    return {"ENGINE": "mssql", "NAME": base, "USER": utilisateur, "PASSWORD": mot_de_passe, "HOST": hote, "PORT": port,
            "OPTIONS": {"python_driver": "mssql_python", "extra_params": "TrustServerCertificate=yes"},
            "ATOMIC_REQUESTS": False, "AUTOCOMMIT": True, "CONN_MAX_AGE": 0, "CONN_HEALTH_CHECKS": False,
            "TIME_ZONE": None, "TEST": {}}


def reglage_sqlite(fichier):
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": str(fichier), "USER": "", "PASSWORD": "", "HOST": "", "PORT": "",
            "OPTIONS": {"timeout": 20, "init_command": "PRAGMA journal_mode=WAL;"}, "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True, "CONN_MAX_AGE": 0, "CONN_HEALTH_CHECKS": False, "TIME_ZONE": None, "TEST": {}}


def tester_sqlserver(reglage):
    """Connexion au serveur, base existante ou à créer, base vide ou de l'ERP. Renvoie un message ; lève sinon."""
    from apps.core.management.commands.miroir import connexion_temporaire, controler_tables

    nom = reglage["NAME"]
    if not str(nom).replace("_", "").isalnum():
        raise ValueError("nom de base : lettres, chiffres et _ seulement")
    with connexion_temporaire("_essai_maitre", {**reglage, "NAME": "master"}) as maitre, maitre.cursor() as cur:
        cur.execute("SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(40)), "
                    "(SELECT COUNT(*) FROM sys.databases WHERE name = %s)", [nom])
        version, existe = cur.fetchone()
    if not existe:
        return f"Connexion réussie (SQL Server {version}). La base {nom} n'existe pas : elle sera créée."
    with connexion_temporaire("_essai", reglage) as base:
        controler_tables("_essai")
        tables = len(base.introspection.table_names())
    return (f"Connexion réussie (SQL Server {version}). Base {nom} existante, "
            + ("vide." if not tables else f"de l'ERP ({tables} tables) : elle sera remplacée par les données actuelles."))


ETAT_CHANGEMENT = {"etat": "", "message": ""}


def changer_de_moteur(cible):
    """Copie complète de la base actuelle vers la cible (créée si besoin, contrôlée), table par table.
    Ne modifie jamais la base actuelle. Lève une erreur explicite en cas d'échec (rien n'est changé)."""
    from django.core.management import call_command

    from django.db import transaction

    from apps.core.management.commands.miroir import connexion_temporaire, controler_tables, copier, creer_base_sqlserver

    if cible["ENGINE"] == "mssql":
        creer_base_sqlserver(cible)
    with connexion_temporaire("_cible", cible):
        controler_tables("_cible")
        call_command("migrate", database="_cible", interactive=False, verbosity=0)
        with transaction.atomic(using="default"):                # une seule photographie de la base actuelle
            return copier("default", "_cible")


def lancer_changement(cible, apres=None):
    """En arrière-plan (une grosse base prend plusieurs minutes) ; l'écran suit ETAT_CHANGEMENT."""
    if ETAT_CHANGEMENT["etat"] == "en_cours":
        raise RuntimeError("un changement de base est déjà en cours")
    ETAT_CHANGEMENT.update(etat="en_cours", message="Copie des données en cours…")

    def travail():
        try:
            lignes = changer_de_moteur(cible)
            if apres:
                apres()
            ETAT_CHANGEMENT.update(etat="termine", message=f"{lignes} lignes copiées et contrôlées table par table. "
                                                           "Redémarrez le logiciel pour travailler sur la nouvelle base.")
        except Exception as exc:
            ETAT_CHANGEMENT.update(etat="erreur", message=f"Changement impossible, rien n'a été modifié : {exc}"[:600])
        finally:
            connections.close_all()

    threading.Thread(target=travail, name="Changement de base", daemon=True).start()
