"""Clôture annuelle N → N+1 : point d'entrée utilisable (ligne de commande / poste compilé).

Enveloppe le moteur déjà testé (`adaptateur_cloture_transport_sqlite`) : crée la base de
l'année N+1 (migrations Django isolées), y recopie la configuration et passe les reports à
nouveau des **écritures validées** de N, puis publie le lien N→N+1 dans le catalogue et marque
N comme clôturé. Aucune écriture de mouvement n'est recopiée. N reste en lecture seule ; en cas
d'échec, la base N+1 est supprimée et N reste ouvert.
"""
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.catalogue_societes import lire_catalogue


def _slug(texte):
    return re.sub(r"[^a-z0-9]+", "-", str(texte).casefold()).strip("-") or "dossier"


def derive_parametres(catalogue, identifiant, destination=None, nouvel_identifiant=None):
    """Depuis le catalogue, déduit (destination, nouvel_identifiant, année N+1) pour un exercice.

    Lève CommandError (message en français) si l'exercice est inconnu, non SQLite ou déjà clôturé.
    """
    source = next((b for b in lire_catalogue(catalogue) if b["id"] == identifiant), None)
    if source is None:
        raise CommandError(f"Exercice « {identifiant} » introuvable dans le catalogue.")
    if source["moteur"] != "sqlite":
        raise CommandError("La clôture annuelle automatique ne gère que les bases SQLite.")
    if source.get("cloture"):
        raise CommandError("Cet exercice est déjà clôturé.")
    annee = int(source["exercice"]) + 1
    base_dossier = f"{_slug(source['societe'])}-{_slug(source['agence'])}-{annee}"
    if destination is None:
        destination = str(Path(source["base"]).parent / f"{base_dossier}.sqlite3")
    if nouvel_identifiant is None:
        nouvel_identifiant = base_dossier
    return destination, nouvel_identifiant, annee


class Command(BaseCommand):
    help = ("Clôture l'exercice N d'un dossier SQLite et crée la base de l'année N+1 "
            "(configuration reprise + reports à nouveau), puis lie N+1 à N dans le catalogue.")

    def add_arguments(self, parser):
        parser.add_argument("identifiant", help="Identifiant de l'exercice N dans le catalogue.")
        parser.add_argument("--catalogue", default=os.environ.get("ERP_CATALOGUE_SOCIETES", ""),
                            help="Chemin du catalogue multi-sociétés (défaut : ERP_CATALOGUE_SOCIETES).")
        parser.add_argument("--destination", default=None,
                            help="Chemin de la base N+1 (défaut : déduit de la société/agence/année).")
        parser.add_argument("--nouvel-identifiant", default=None,
                            help="Identifiant de l'exercice N+1 (défaut : déduit).")

    def handle(self, *args, **options):
        catalogue = (options["catalogue"] or "").strip()
        if not catalogue:
            raise CommandError("Catalogue non configuré (variable ERP_CATALOGUE_SOCIETES ou option --catalogue).")
        if not Path(catalogue).is_file():
            raise CommandError(f"Catalogue introuvable : {catalogue}")
        destination, nouvel_identifiant, annee = derive_parametres(
            catalogue, options["identifiant"], options["destination"], options["nouvel_identifiant"])
        # Import tardif : évite de charger le sous-processus de migration quand on ne fait que lister.
        from apps.core.adaptateur_cloture_transport_sqlite import preparer_dossier_transport_sqlite

        self.stdout.write(f"Clôture de « {options['identifiant']} » → exercice {annee} dans {destination}…")
        try:
            suivante = preparer_dossier_transport_sqlite(
                catalogue, options["identifiant"], destination, nouvel_identifiant, annee)
        except (ValueError, FileExistsError, RuntimeError, OSError) as exc:
            raise CommandError(f"Clôture impossible, aucun changement : {exc}") from exc
        self.stdout.write(self.style.SUCCESS(
            f"Exercice {annee} créé (« {suivante['id']} ») ; l'exercice précédent est clôturé."))
