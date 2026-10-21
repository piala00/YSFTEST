import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core import reprise_sage


class Command(BaseCommand):
    help = ("Reprend un dossier Sage 100 (CSV exportés par les SELECT de lecture seule) : dépôts, familles, comptes, "
            "tiers, articles, stock et soldes d'ouverture. Simulation par défaut.")

    def add_arguments(self, parser):
        parser.add_argument("--dossier", help="Dossier contenant depots.csv, familles.csv, … soldes.csv")
        parser.add_argument("--date-bascule", help="Date du stock et des soldes d'ouverture (AAAA-MM-JJ)")
        parser.add_argument("--appliquer", action="store_true", help="Enregistre l'import (sinon simple simulation)")
        parser.add_argument("--rapport", help="Écrit aussi le rapport dans ce fichier")
        parser.add_argument("--sql", action="store_true", help="Affiche les requêtes d'export à lancer dans Sage")
        parser.add_argument("--correspondance", action="store_true", help="Affiche la correspondance des colonnes")

    def handle(self, *args, **options):
        if options["sql"]:
            self.stdout.write(reprise_sage.SQL_EXPORT.read_text(encoding="utf-8"))
            return
        if options["correspondance"]:
            for nom in reprise_sage.ORDRE:
                table, colonnes = reprise_sage.FICHIERS[nom]
                self.stdout.write(f"\n{nom}.csv ← {table}")
                for colonne, (obligatoire, statut, ref, usage) in colonnes.items():
                    self.stdout.write(f"  {colonne:<15} {'obligatoire' if obligatoire else 'facultatif ':<11} "
                                      f"{statut:<17} {ref:<12} {usage}")
            return
        if not options["dossier"] or not options["date_bascule"]:
            raise CommandError("Indiquez --dossier et --date-bascule (ou --sql / --correspondance).")
        if not Path(options["dossier"]).is_dir():
            raise CommandError(f"Dossier introuvable : {options['dossier']}")
        try:
            date = datetime.date.fromisoformat(options["date_bascule"])
        except ValueError:
            raise CommandError("--date-bascule doit être au format AAAA-MM-JJ.")
        rapport = reprise_sage.importer(options["dossier"], date, appliquer=options["appliquer"])
        texte = rapport.texte()
        self.stdout.write(texte)
        if options["rapport"]:
            Path(options["rapport"]).write_text(texte + "\n", encoding="utf-8")
        if not rapport.conforme:
            raise CommandError("Reprise non conforme : rien n'a été enregistré.")
