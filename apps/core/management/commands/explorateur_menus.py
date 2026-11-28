"""Génère l'explorateur HTML des menus (Fichier, Édition, Structure, Traitement, Etat, Fenêtre, ?).

    python manage.py explorateur_menus --sortie docs/explorateur-menus.html            # page publiable
    python manage.py explorateur_menus --sortie explorateur.html --autonome            # à ouvrir dans un navigateur
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.navigation import MODULES, PREUVES, serialiser_module

GABARIT = Path(__file__).resolve().parents[2] / "explorateur" / "explorateur.html"
CHAMPS = ("code", "titre", "url", "action", "module", "separateur", "preuve")


def _nettoyer(noeud):
    return {**{k: noeud.get(k) or ("" if k != "separateur" else False) for k in CHAMPS},
            "enfants": [_nettoyer(e) for e in noeud["enfants"]]}


def donnees():
    modules = []
    for module in MODULES:
        s = serialiser_module(module)
        modules.append({
            "code": s["code"], "titre": s["titre"], "description": s["description"], "couleur": s["couleur"],
            "onglets": [{"code": o["code"], "titre": o["titre"], "elements": [_nettoyer(e) for e in o["elements"]]}
                        for o in s["onglets"]],
        })
    return {"genere": timezone.localtime().strftime("%d/%m/%Y"), "preuves": PREUVES, "modules": modules}


class Command(BaseCommand):
    help = "Génère la page HTML qui permet de parcourir et vérifier les menus des trois logiciels."

    def add_arguments(self, parser):
        parser.add_argument("--sortie", default="docs/explorateur-menus.html")
        parser.add_argument("--autonome", action="store_true",
                            help="Ajoute l'enveloppe <!doctype html> pour ouvrir le fichier directement dans un navigateur")

    def handle(self, *args, **options):
        json_donnees = json.dumps(donnees(), ensure_ascii=False).replace("</", "<\\/")
        page = GABARIT.read_text(encoding="utf-8").replace("/*__DONNEES__*/", json_donnees)
        if options["autonome"]:
            page = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
                    + page + "</body></html>")
        sortie = Path(options["sortie"])
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(page, encoding="utf-8")
        nb = sum(1 for _ in json_donnees.split('"code"')) - 1
        self.stdout.write(self.style.SUCCESS(f"Explorateur écrit dans {sortie} ({len(page) // 1024} Ko, {nb} entrées)."))
