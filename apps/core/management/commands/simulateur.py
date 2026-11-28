"""Génère les simulateurs HTML autonomes de l'ERP (à télécharger et ouvrir dans un navigateur).

    python manage.py simulateur                       # docs/erp-simulateur-web.html et docs/erp-simulateur-bureau.html

À lancer sur une base de démonstration (init_erp --demo ou --sahel) : les écrans et les chiffres
affichés sont ceux de cette base. Les deux fichiers fonctionnent sans serveur ni Internet ;
gardez-les dans le même dossier pour passer de l'un à l'autre.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.core.management.commands.explorateur_menus import donnees
from apps.core.models import Exercice, Societe
from apps.core.navigation import MODULES, structure_module
from apps.core.simulateur import capture

GABARITS = Path(capture.__file__).resolve().parent


def _json(objet):
    return json.dumps(objet, ensure_ascii=False, default=str).replace("</", "<\\/")


def _remplacer(gabarit, valeurs):
    page = gabarit
    for cle, valeur in valeurs.items():
        repere = f"/*__{cle}__*/"
        if repere not in page:
            raise CommandError(f"Repère {repere} absent du gabarit")
        page = page.replace(repere, valeur)
    return page


class Command(BaseCommand):
    help = "Génère les simulateurs HTML (version web et version bureau) à partir de la base courante."

    def add_arguments(self, parser):
        parser.add_argument("--dossier", default="docs")

    def handle(self, *args, **options):
        from apps.commercial.models import Document

        if not Document.objects.exists():
            raise CommandError("Base vide : lancez d'abord « python manage.py init_erp --demo » (ou --sahel).")
        dossier = Path(options["dossier"])
        dossier.mkdir(parents=True, exist_ok=True)
        societe, exercice = Societe.get(), Exercice.courant()

        # --- Version web : toutes les commandes des menus, puis les liens internes
        depart = ["/"]

        def liens(noeuds):
            for n in noeuds:
                if n["url"]:
                    yield n["url"]
                yield from liens(n["enfants"])

        for module in MODULES:
            depart.append(reverse(module.accueil))
            for onglet in structure_module(module)[0]:
                depart.extend(liens(onglet["elements"]))
        pages = capture.capturer_web(depart)
        ressources = capture.ressources_statiques()
        navigation = donnees()
        navigation.pop("preuves", None)        # provenance des menus : notes d'étude, pas affichées dans le logiciel
        contexte = {"societe": societe.raison_sociale, "exercice": exercice.code if exercice else "",
                    "utilisateur": capture.capturer_api()["utilisateur"]}
        web = _remplacer((GABARITS / "web.html").read_text(encoding="utf-8"), {
            "BOOTSTRAP_CSS": ressources["bootstrap_css"], "ICONES_CSS": ressources["icones_css"], "ERP_CSS": ressources["erp_css"],
            "BOOTSTRAP_JS": ressources["bootstrap_js"], "CHART_JS": ressources["chart_js"],
            "PAGES": _json(pages), "NAVIGATION": _json(navigation), "CONTEXTE": _json(contexte),
        })
        chemin_web = dossier / "erp-simulateur-web.html"
        chemin_web.write_text(web, encoding="utf-8")
        self.stdout.write(f"Version web : {chemin_web} ({len(pages)} écrans, {len(web) // 1024} Ko)")

        # --- Version bureau : données de l'API lue par le client CustomTkinter
        api = capture.capturer_api()
        bureau = _remplacer((GABARITS / "bureau.html").read_text(encoding="utf-8"), {
            "API": _json(api), "ECRANS": _json(capture.ecrans_bureau()), "CONTEXTE": _json(contexte),
        })
        chemin_bureau = dossier / "erp-simulateur-bureau.html"
        chemin_bureau.write_text(bureau, encoding="utf-8")
        self.stdout.write(f"Version bureau : {chemin_bureau} ({len(bureau) // 1024} Ko)")
        self.stdout.write(self.style.SUCCESS("Simulateurs générés : ouvrez-les dans un navigateur (gardez-les dans le même dossier)."))
