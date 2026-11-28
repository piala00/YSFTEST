import datetime
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core import reprise_sage
from apps.core.models import Societe
from apps.core.reprise_sage import source


class Command(BaseCommand):
    help = ("Synchronisation planifiée de la copie du dossier d'origine (lecture seule de sa base SQL Server). "
            "Serveur, instance et base : ceux de la première synchronisation (écran) ; compte SQL éventuel dans .env : "
            "SYNCHRO_UTILISATEUR, SYNCHRO_MOT_DE_PASSE (vide : authentification Windows).")

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Données jusqu'au (AAAA-MM-JJ, défaut : aujourd'hui)")
        parser.add_argument("--simuler", action="store_true", help="Contrôle seulement, rien n'est enregistré")

    def handle(self, *args, **options):
        fiche = Societe.get()
        if fiche.source_mode != Societe.SYNCHRO_MIROIR:
            self.stdout.write("Aucune copie synchronisée en cours (pas encore commencée à l'écran, ou bascule faite) : rien à faire.")
            return
        serveur, _, base = fiche.source_dossier.rpartition("/")
        if not serveur or not base or Path(fiche.source_dossier).exists():
            raise CommandError(f"Dossier synchronisé « {fiche.source_dossier} » : ce n'est pas une base SQL Server "
                               "(serveur\\instance/base). Synchronisez depuis l'écran Fichier › Reprise d'un dossier existant.")
        try:
            jusqu_au = datetime.date.fromisoformat(options["date"]) if options["date"] else datetime.date.today()
        except ValueError:
            raise CommandError("--date doit être au format AAAA-MM-JJ.")
        try:
            connexion = source.connecter(serveur, base, os.environ.get("SYNCHRO_UTILISATEUR", ""),
                                         os.environ.get("SYNCHRO_MOT_DE_PASSE", ""))
        except Exception as exc:
            raise CommandError(f"Connexion au dossier d'origine impossible : {exc}")
        origine = source.SourceSQL(connexion, fiche.source_debut_exercice, jusqu_au, dossier_nom=fiche.source_dossier)
        try:
            rapport = reprise_sage.importer(origine, jusqu_au, appliquer=not options["simuler"],
                                            debut_exercice=fiche.source_debut_exercice, dossier=fiche.source_dossier)
        except Exception as exc:
            raise CommandError(f"Synchronisation impossible : {exc}")
        self.stdout.write(rapport.texte())
        if not rapport.conforme:
            raise CommandError("Synchronisation non conforme : rien n'a été enregistré (voir le rapport ci-dessus).")
