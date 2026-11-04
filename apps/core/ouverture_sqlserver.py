"""Validation en lecture seule d'une base SQL Server inscrite au catalogue.

Les identifiants restent dans les variables d'environnement du serveur, jamais dans
le catalogue JSON ni dans les pages HTML. Aucun CREATE/MIGRATE n'est exécuté.
"""
import os
import re

from django.core.management.base import CommandError


def verifier_base_sqlserver(entree, environnement=None):
    """Retourne les paramètres de redémarrage après contrôle de la base existante."""
    from apps.core.base_donnees import reglage_sqlserver
    from apps.core.management.commands.miroir import connexion_temporaire, controler_tables

    env = os.environ if environnement is None else environnement
    identifiant = entree["id"]
    if not re.fullmatch(r"[A-Za-z0-9_]{1,50}", identifiant):
        raise ValueError("Identifiant SQL Server invalide dans le catalogue")
    nom = entree["base"]
    if not re.fullmatch(r"[A-Za-z0-9_]{1,128}", nom):
        raise ValueError("Nom de base SQL Server invalide")
    prefixe = "ERP_SOCIETE_SQL_" + identifiant.upper() + "_"
    hote = env.get(prefixe + "HOST", "").strip()
    if not hote:
        raise ValueError("Serveur SQL non configuré pour cette société")
    utilisateur = env.get(prefixe + "USER", "")
    mot_de_passe = env.get(prefixe + "PASSWORD", "")
    port = env.get(prefixe + "PORT", "")
    if utilisateur and not mot_de_passe:
        raise ValueError("Mot de passe SQL non configuré")
    reglage = reglage_sqlserver(hote, nom, utilisateur, mot_de_passe, port)
    try:
        with connexion_temporaire("_societe_verification", reglage) as connexion:
            controler_tables("_societe_verification")
            tables = set(connexion.introspection.table_names())
            if not {"django_migrations", "auth_user", "core_societe"}.issubset(tables):
                raise ValueError("Base SQL Server non initialisée comme ERP")
            with connexion.cursor() as curseur:
                curseur.execute("SELECT COUNT(*) FROM [core_societe]")
                if curseur.fetchone()[0] < 1:
                    raise ValueError("Identité de société absente de la base")
    except CommandError as exc:
        raise ValueError("Base SQL Server non compatible avec l'ERP") from exc
    # Ne pas inclure d'identifiants dans les erreurs ou journaux.
    return {
        "DB_ENGINE": "mssql", "DB_HOST": hote, "DB_NAME": nom,
        "DB_USER": utilisateur or None, "DB_PASSWORD": mot_de_passe or None,
        "DB_PORT": port or None, "DB_PYTHON_DRIVER": "mssql_python",
        "DB_EXTRA_PARAMS": "TrustServerCertificate=yes",
        "SQLITE_FICHIER": None, "MIROIR_DB_ENGINE": None,
    }
