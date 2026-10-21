"""Sauvegarde et restauration de toutes les données de l'ERP dans un fichier JSON.

Le fichier contient la société, les exercices, les utilisateurs, profils et droits, la gestion commerciale et la
comptabilité. La restauration remplace **toutes** les données actuelles par celles du fichier.
"""
import io
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.db import transaction

CONTENU = ["auth.group", "auth.user", "authtoken", "core", "commercial", "comptabilite"]
FORMAT = "erp-ohada-sauvegarde"


def sauvegarder():
    """Contenu JSON de la sauvegarde (texte)."""
    sortie = io.StringIO()
    call_command("dumpdata", *CONTENU, natural_foreign=True, indent=1, stdout=sortie)
    donnees = json.loads(sortie.getvalue())
    from django.utils import timezone

    entete = {"model": "_entete", "format": FORMAT, "version": 1, "date": timezone.now().isoformat(),
              "objets": len(donnees)}
    return json.dumps([entete] + donnees, ensure_ascii=False, indent=1)


def lire(contenu):
    """Contrôle le fichier ; renvoie (entête, objets) ou lève ValueError."""
    try:
        donnees = json.loads(contenu)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Le fichier n'est pas une sauvegarde lisible (JSON invalide).")
    if not isinstance(donnees, list) or not donnees or donnees[0].get("format") != FORMAT:
        raise ValueError("Ce fichier n'est pas une sauvegarde de l'ERP OHADA.")
    entete, objets = donnees[0], donnees[1:]
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
    return entete
