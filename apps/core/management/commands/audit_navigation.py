"""Matrice de traçabilité Sage 100 → ERP OHADA, générée depuis la définition des menus.

    python manage.py audit_navigation                      # Gestion commerciale, vers la sortie standard
    python manage.py audit_navigation --sortie docs/AUDIT_SAGE_V12_GESCOM.md
"""
from collections import Counter

from django.core.management.base import BaseCommand

from apps.core.navigation import MODULES_PAR_CODE, PREUVES, structure_module

ETATS = {
    "realise": "✅ Réalisé",
    "action": "✅ Commande d'interface",
    "externe": "↗ Autre logiciel de l'ERP",
    "sous_menu": "▸ Sous-menu",
    "grise": "⬜ Grisé (non développé)",
}


def etat_du_noeud(noeud):
    if noeud["enfants"]:
        return "sous_menu"
    if noeud["action"]:
        return "action"
    if noeud["module"]:
        return "externe"
    return "realise" if noeud["url"] else "grise"


class Command(BaseCommand):
    help = "Génère la matrice de traçabilité des menus (élément Sage → écran ERP → état → preuve)."

    def add_arguments(self, parser):
        parser.add_argument("--module", default="commercial", choices=sorted(MODULES_PAR_CODE))
        parser.add_argument("--sortie", help="Fichier Markdown à écrire")

    def handle(self, *args, **options):
        module = MODULES_PAR_CODE[options["module"]]
        onglets, _ = structure_module(module)
        lignes, compteurs, preuves = [], Counter(), Counter()

        def parcourir(noeuds, chemin):
            for n in noeuds:
                if n["separateur"]:
                    continue
                etat = etat_du_noeud(n)
                complet = chemin + [n["titre"]]
                if etat != "sous_menu":
                    compteurs[etat] += 1
                    preuves[n["preuve"] or "—"] += 1
                cible = n["url"] or (f"action « {n['action']} »" if n["action"] else "")
                lignes.append(f"| {' › '.join(chemin)} | {'**' if etat == 'sous_menu' else ''}{n['titre']}"
                              f"{'**' if etat == 'sous_menu' else ''} | {n['preuve'] or '—'} | {ETATS[etat]} | "
                              f"{('`' + cible + '`') if cible else ''} |")
                parcourir(n["enfants"], complet)

        for onglet in onglets:
            lignes.append(f"| **{onglet['titre']}** | | | | |")
            parcourir(onglet["elements"], [onglet["titre"]])

        total = sum(compteurs.values())
        sortie = [
            f"# Matrice de traçabilité — {module.titre}",
            "",
            "Générée par `python manage.py audit_navigation` à partir de `apps/core/navigation.py`.",
            "Méthode : skill `sage-100-gescom-v12-ui` (référence 10, phase D) — élément Sage → écran ERP → état → preuve.",
            "",
            "## Synthèse",
            "",
            "| État | Commandes |",
            "|---|---|",
            *[f"| {ETATS[cle]} | {compteurs[cle]} |" for cle in ("realise", "action", "externe", "grise")],
            f"| **Total des commandes** | **{total}** |",
            "",
            "| Niveau de preuve | Commandes | Signification |",
            "|---|---|---|",
            *[f"| {p} | {preuves[p]} | {PREUVES.get(p, 'Hors périmètre du découpage Gescom')} |" for p in sorted(preuves)],
            "",
            "## Détail par menu",
            "",
            "| Chemin | Élément | Preuve | État dans l'ERP | Écran / action |",
            "|---|---|---|---|---|",
            *lignes,
            "",
        ]
        texte = "\n".join(sortie)
        if options["sortie"]:
            with open(options["sortie"], "w", encoding="utf-8") as f:
                f.write(texte)
            self.stdout.write(self.style.SUCCESS(f"Matrice écrite dans {options['sortie']} ({total} commandes)."))
        else:
            self.stdout.write(texte)
