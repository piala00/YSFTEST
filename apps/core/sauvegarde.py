"""Sauvegarde et restauration de toutes les données de l'ERP dans un fichier JSON.

Le fichier contient la société, les exercices, les utilisateurs, profils et droits, la gestion commerciale et la
comptabilité. La restauration remplace **toutes** les données actuelles par celles du fichier.
"""
import io
import hashlib
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.db import transaction, connection

CONTENU = ["auth.group", "auth.user", "authtoken", "core", "commercial", "comptabilite",
           "transport", "echanges", "garage", "personnel", "partenaires", "reporting", "relais", "licences"]
APPLICATIONS = sorted({nom.split(".")[0] for nom in CONTENU})
FORMAT = "erp-ohada-sauvegarde"


def empreinte_objets(objets):
    return hashlib.sha256(json.dumps(objets, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def sauvegarder():
    """Contenu JSON de la sauvegarde (texte)."""
    sortie = io.StringIO()
    # Un même instant logique pour les pièces et leurs écritures : SQLite conserve
    # sa lecture transactionnelle ; SQL Server protège aussi les nouvelles lignes.
    isolation = None
    try:
        if connection.settings_dict["ENGINE"] == "mssql":
            with connection.cursor() as cur:
                cur.execute("SELECT transaction_isolation_level FROM sys.dm_exec_sessions WHERE session_id=@@SPID")
                isolation = {1: "READ UNCOMMITTED", 2: "READ COMMITTED", 3: "REPEATABLE READ",
                             4: "SERIALIZABLE", 5: "SNAPSHOT"}.get(cur.fetchone()[0], "READ COMMITTED")
                cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        with transaction.atomic():
            call_command("dumpdata", *CONTENU, natural_foreign=True, indent=1, stdout=sortie)
    finally:
        if isolation:
            with connection.cursor() as cur:
                cur.execute("SET TRANSACTION ISOLATION LEVEL " + isolation)
    donnees = json.loads(sortie.getvalue())
    from django.utils import timezone

    entete = {"model": "_entete", "format": FORMAT, "version": 2, "applications": APPLICATIONS,
              "date": timezone.now().isoformat(),
              "objets": len(donnees), "sha256": empreinte_objets(donnees)}
    return json.dumps([entete] + donnees, ensure_ascii=False, indent=1)


def lire(contenu):
    """Contrôle le fichier ; renvoie (entête, objets) ou lève ValueError."""
    try:
        donnees = json.loads(contenu)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Le fichier n'est pas une sauvegarde lisible (JSON invalide).")
    if (not isinstance(donnees, list) or not donnees or not isinstance(donnees[0], dict)
            or donnees[0].get("format") != FORMAT or any(not isinstance(o, dict) for o in donnees[1:])):
        raise ValueError("Ce fichier n'est pas une sauvegarde de l'ERP OHADA.")
    entete, objets = donnees[0], donnees[1:]
    if entete.get("version") != 2 or entete.get("applications") != APPLICATIONS:
        raise ValueError("Ancienne sauvegarde JSON partielle ou périmètre non confirmé : restauration refusée pour préserver les modules Transport et les autres données. Conservez le fichier pour une reprise encadrée dans un dossier séparé.")
    if entete.get("objets") != len(objets):
        raise ValueError("Sauvegarde JSON incomplète : le nombre d'objets ne correspond pas à l'en-tête.")
    if entete.get("sha256") != empreinte_objets(objets):
        raise ValueError("Sauvegarde JSON altérée ou incomplète : l'empreinte du contenu ne correspond pas.")
    from django.apps import apps

    autorises = {m._meta.label_lower for m in apps.get_models() if m._meta.app_label in APPLICATIONS
                 and m._meta.label_lower not in {"auth.permission", "auth.user_groups", "auth.user_user_permissions"}}
    for o in objets:
        if o.get("model") not in autorises or not isinstance(o.get("fields"), dict):
            raise ValueError("La sauvegarde contient un modèle ou des champs non admis.")
    if not any(o.get("model") == "auth.user" and o["fields"].get("is_superuser") for o in objets):
        raise ValueError("La sauvegarde ne contient aucun administrateur : restauration refusée.")
    return entete, objets


@transaction.atomic
def restaurer(contenu):
    """Remplace toutes les données par celles de la sauvegarde (tout ou rien)."""
    entete, objets = lire(contenu)
    call_command("flush", interactive=False, verbosity=0)
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "sauvegarde.json"
        chemin.write_text(json.dumps(objets, ensure_ascii=False), encoding="utf-8")
        call_command("loaddata", str(chemin), verbosity=0)
    from apps.licences.licence import oublier

    oublier()
    return entete
