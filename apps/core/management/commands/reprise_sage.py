import datetime
import getpass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core import reprise_sage
from apps.core.reprise_sage import source


def _date(valeur, option):
    try:
        return datetime.date.fromisoformat(valeur) if valeur else None
    except ValueError:
        raise CommandError(f"{option} doit être au format AAAA-MM-JJ.")


class Command(BaseCommand):
    help = ("Reprend un dossier Sage 100 complet (comptabilité et gestion commerciale), en lecture directe de la base "
            "SQL Server (lecture seule) ou depuis des CSV exportés. Simulation par défaut.")

    def add_arguments(self, parser):
        parser.add_argument("--serveur", help="Serveur SQL de Sage (lecture directe), ex. .\\SAGE100 ou localhost")
        parser.add_argument("--base", help="Base SQL du dossier Sage à reprendre")
        parser.add_argument("--utilisateur", default="", help="Compte SQL (vide : authentification Windows)")
        parser.add_argument("--dossier", help="Ou : dossier contenant les CSV exportés (depots.csv, …)")
        parser.add_argument("--date-bascule", help="Date de bascule : stock et comptabilité repris à cette date (AAAA-MM-JJ)")
        parser.add_argument("--debut-exercice", help="Premier jour de l'exercice en cours dans Sage (AAAA-MM-JJ)")
        parser.add_argument("--historique-depuis", help="Pièces commerciales reprises depuis cette date "
                                                        "(défaut : début d'exercice ; les pièces en cours le sont toujours)")
        parser.add_argument("--appliquer", action="store_true", help="Enregistre l'import (sinon simple simulation)")
        parser.add_argument("--rapport", help="Écrit aussi le rapport dans ce fichier")
        parser.add_argument("--sql", action="store_true", help="Affiche les requêtes d'export (CSV) à lancer dans Sage")
        parser.add_argument("--correspondance", action="store_true", help="Affiche la correspondance des colonnes")

    def handle(self, *args, **options):
        bascule = _date(options["date_bascule"], "--date-bascule")
        debut = _date(options["debut_exercice"], "--debut-exercice")
        historique = _date(options["historique_depuis"], "--historique-depuis")
        if options["sql"]:
            aujourdhui = datetime.date.today()
            self.stdout.write(source.script_export(debut or aujourdhui.replace(month=1, day=1), bascule or aujourdhui, historique))
            return
        if options["correspondance"]:
            for nom in reprise_sage.ORDRE:
                table, colonnes = reprise_sage.FICHIERS[nom]
                self.stdout.write(f"\n{nom}.csv ← {table}")
                for colonne, (obligatoire, statut, ref, usage) in colonnes.items():
                    self.stdout.write(f"  {colonne:<15} {'obligatoire' if obligatoire else 'facultatif ':<11} "
                                      f"{statut:<17} {ref:<12} {usage}")
            return
        if not bascule:
            raise CommandError("Indiquez --date-bascule (ou --sql / --correspondance).")
        if options["serveur"]:
            if not options["base"] or not debut:
                raise CommandError("Lecture directe : indiquez aussi --base et --debut-exercice.")
            mot_de_passe = getpass.getpass("Mot de passe SQL : ") if options["utilisateur"] else ""
            try:
                connexion = source.connecter(options["serveur"], options["base"], options["utilisateur"], mot_de_passe)
            except Exception as exc:
                raise CommandError(f"Connexion à Sage impossible : {exc}")
            origine = source.SourceSQL(connexion, debut, bascule, historique)
        elif options["dossier"]:
            if not Path(options["dossier"]).is_dir():
                raise CommandError(f"Dossier introuvable : {options['dossier']}")
            origine = options["dossier"]
        else:
            raise CommandError("Indiquez --serveur et --base (lecture directe) ou --dossier (CSV).")
        rapport = reprise_sage.importer(origine, bascule, appliquer=options["appliquer"], debut_exercice=debut)
        texte = rapport.texte()
        self.stdout.write(texte)
        if options["rapport"]:
            Path(options["rapport"]).write_text(texte + "\n", encoding="utf-8")
        if not rapport.conforme:
            raise CommandError("Reprise non conforme : rien n'a été enregistré.")
