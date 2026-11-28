"""Inscrire une base SQLite au catalogue multi-sociétés (ERP_CATALOGUE_SOCIETES).

Rend « Ouvrir une société » et la clôture annuelle utilisables : le poste inscrit sa base
courante (société / agence / année) au catalogue. Écriture **atomique** et **validée** (les
doublons société/agence/année, d'identifiant ou de base physique sont refusés sans rien changer).
Ne modifie pas la base elle-même.
"""
import json
import os
import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.catalogue_societes import lire_catalogue


def _slug(texte):
    return re.sub(r"[^a-z0-9]+", "-", str(texte).casefold()).strip("-") or "dossier"


def base_sqlite_courante():
    """Chemin absolu de la base SQLite en cours d'utilisation, ou None (SQL Server / inconnu)."""
    reglage = settings.DATABASES.get("default", {})
    if not str(reglage.get("ENGINE", "")).endswith("sqlite3"):
        return None
    nom = str(reglage.get("NAME", "")).strip()
    return str(Path(nom).resolve()) if nom else None


class Command(BaseCommand):
    help = ("Inscrit une base SQLite au catalogue multi-sociétés (pour « Ouvrir une société » "
            "et la clôture annuelle).")

    def add_arguments(self, parser):
        parser.add_argument("--catalogue", default=os.environ.get("ERP_CATALOGUE_SOCIETES", ""),
                            help="Chemin du catalogue (défaut : ERP_CATALOGUE_SOCIETES).")
        parser.add_argument("--societe", required=True)
        parser.add_argument("--agence", required=True)
        parser.add_argument("--exercice", required=True, help="Année AAAA.")
        parser.add_argument("--base", default=None, help="Chemin de la base SQLite (défaut : base en cours).")
        parser.add_argument("--id", dest="identifiant", default=None, help="Identifiant (défaut : déduit).")

    def handle(self, *args, **options):
        catalogue = (options["catalogue"] or "").strip()
        if not catalogue:
            raise CommandError("Catalogue non configuré (variable ERP_CATALOGUE_SOCIETES ou option --catalogue).")
        exercice = str(options["exercice"]).strip()
        if not (len(exercice) == 4 and exercice.isascii() and exercice.isdigit()):
            raise CommandError("Exercice attendu au format AAAA.")
        base = options["base"] or base_sqlite_courante()
        if not base:
            raise CommandError("Base SQLite introuvable : précisez --base.")
        base = str(Path(base).expanduser().resolve())
        if not Path(base).is_file():
            raise CommandError(f"Fichier de base introuvable : {base}")
        identifiant = options["identifiant"] or f"{_slug(options['societe'])}-{_slug(options['agence'])}-{exercice}"

        chemin = Path(catalogue)
        try:
            bases = lire_catalogue(chemin) if chemin.is_file() else []
        except (OSError, ValueError) as exc:
            raise CommandError(f"Catalogue illisible : {exc}")
        entree = {"id": identifiant, "societe": options["societe"].strip(), "agence": options["agence"].strip(),
                  "exercice": exercice, "moteur": "sqlite", "base": base, "cloture": False}
        contenu = {"version": 1, "bases": [dict(b) for b in bases] + [entree]}

        chemin.parent.mkdir(parents=True, exist_ok=True)
        temporaire = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(chemin.parent),
                                             prefix=".societes-", suffix=".tmp", delete=False) as flux:
                temporaire = Path(flux.name)
                json.dump(contenu, flux, ensure_ascii=False, indent=2)
                flux.write("\n")
                flux.flush()
                os.fsync(flux.fileno())
            lire_catalogue(temporaire)                 # refuse doublons / incohérences avant publication
            os.replace(temporaire, chemin)
            temporaire = None
        except (OSError, ValueError) as exc:
            raise CommandError(f"Inscription refusée, catalogue inchangé : {exc}")
        finally:
            if temporaire is not None:
                temporaire.unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(
            f"Base inscrite au catalogue : « {identifiant} » ({entree['societe']} / {entree['agence']} / {exercice})."))
