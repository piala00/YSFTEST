"""Recensement REPRODUCTIBLE des commandes de menus et occurrences de contrôles HTML commerciaux.

Commande:
    python manage.py recenser_boutons_commercial --sortie docs/retour/RECENSEMENT_BOUTONS_COMMERCIAL

Le recensement est STATIQUE : une occurrence dans un template Django n'est pas un nombre
de boutons rendus sur une facture. Aucune écriture métier et aucune requête SQL en écriture.
"""
import csv
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.commercial.models import Document
from apps.core.navigation import GESTION_COMMERCIALE, structure_module

COLONNES = (
    "id", "famille", "fichier_ou_menu", "ligne", "chemin", "libelle",
    "element_html", "etat_code", "condition", "cible_ou_action",
    "mode_ou_fenetre", "preuve_sage", "fonction_sage_detaillee",
    "fonction_erp_verifiee_en_execution", "ecart", "scenario_test",
)

# Le rendu des menus est compté dans navigation.py et PAS à nouveau dans
# core/_menu.html ou core/_arbre.html, ni la barre verticale qui réplique les liens.
TEMPLATES_COMMUNS = (
    "templates/base.html",
    "templates/pagination.html",
    "templates/core/_auteurs.html",
)

TAGS_ACTION = {"button", "a", "input", "summary", "select"}
CLASSES_INACTIVES = ("inactif", "desactive", "disabled")


def nettoyer(texte):
    texte = re.sub(r"\{#[\s\S]*?#\}", " ", texte)
    texte = re.sub(r"\{%[\s\S]*?%\}", " ", texte)
    texte = re.sub(r"\{\{[\s\S]*?\}\}", " [variable] ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def lire_fichier(fichier):
    return fichier.read_text(encoding="utf-8-sig")


class LecteurCommandes(HTMLParser):
    """Compte chaque occurrence source une fois, y compris sous les boucles Django."""

    def __init__(self, relatif, source):
        super().__init__(convert_charrefs=True)
        self.relatif = relatif
        self.source = source
        self.lignes = source.splitlines()
        self.entrees = []
        self.pile = []
        self.boutons = []
        self.formulaires = []

    def _attrs(self, attrs):
        return {str(k): (v or "") for k, v in attrs if k}

    def handle_starttag(self, tag, attrs):
        self._debut(tag, attrs, ferme=False)

    def handle_startendtag(self, tag, attrs):
        self._debut(tag, attrs, ferme=True)

    def _debut(self, tag, attrs, ferme=False):
        a = self._attrs(attrs)
        ligne = self.getpos()[0]
        if tag == "form":
            self.formulaires.append({
                "action": a.get("action", ""),
                "method": a.get("method", "get").upper(),
            })
        classe = " ".join((a.get("class", ""), a.get("aria-disabled", ""))).lower()
        inactive = tag == "span" and any(mot in classe for mot in CLASSES_INACTIVES)
        bon_input = tag == "input" and a.get("type", "text").lower() in (
            "button", "submit", "reset", "checkbox", "radio"
        )
        action_lien = tag == "a" and (
            "href" in a or "onclick" in a or "data-bs-toggle" in a
            or "data-action" in a or a.get("role") == "button"
        )
        est_controle = (
            inactive or tag in ("button", "select", "summary")
            or bon_input or action_lien
        )
        entree = None
        if est_controle:
            extrait = self.lignes[ligne - 1] if 0 < ligne <= len(self.lignes) else ""
            conditions = [
                "condition_serveur" if "{% if " in extrait or "{% with " in extrait else "",
                "boucle_dynamique" if "{% for " in extrait else "",
                "variable_django" if "{{" in extrait else "",
            ]
            if "disabled" in a or a.get("aria-disabled", "").lower() == "true":
                etat = "desactive_ou_conditionnel" if "{% " in extrait else "desactive_html"
            elif inactive:
                etat = "inactif_html"
            elif "{%" in extrait:
                etat = "conditionnel_a_verifier"
            else:
                etat = "interactif_declare_non_teste"
            form = self.formulaires[-1] if self.formulaires else {}
            cible = (
                a.get("data-action") or a.get("data-erp-action")
                or a.get("href") or a.get("formaction")
                or a.get("onclick") or form.get("action", "")
            )
            if tag == "input":
                libelle = a.get("value") or a.get("aria-label") or a.get("title") or a.get("name", "")
            else:
                libelle = a.get("aria-label") or a.get("title") or ""
            mode = (
                "nouvelle_fenetre_mdi" if "data-nouvelle-fenetre" in a
                else "nouvel_onglet" if a.get("target") == "_blank"
                else "dialogue_bootstrap" if a.get("data-bs-toggle") in ("modal", "dropdown")
                else "confirmation_js" if "confirm(" in str(a.get("onclick", ""))
                else ("formulaire_" + form.get("method", "") if tag == "button" and form else "a_verifier")
            )
            entree = {
                "id": "", "famille": "controle_html",
                "fichier_ou_menu": self.relatif, "ligne": ligne,
                "chemin": self.relatif, "libelle": nettoyer(libelle),
                "element_html": tag + (":" + a.get("type", "") if tag == "input" else ""),
                "etat_code": etat, "condition": ",".join(filter(None, conditions)),
                "cible_ou_action": nettoyer(cible),
                "mode_ou_fenetre": mode,
                "preuve_sage": "A_VERIFIER", "fonction_sage_detaillee": "",
                "fonction_erp_verifiee_en_execution": "NON",
                "ecart": "", "scenario_test": "",
            }
            self.entrees.append(entree)
        if not ferme and tag not in ("input", "br", "hr", "meta", "link", "img", "source", "area"):
            self.pile.append((tag, entree))
            if entree:
                self.boutons.append(entree)

    def handle_data(self, data):
        morceaux = nettoyer(data)
        if not morceaux:
            return
        for entree in self.boutons:
            if entree is not None and len(entree["libelle"]) < 160:
                entree["libelle"] = (entree["libelle"] + " " + morceaux).strip()[:180]

    def handle_endtag(self, tag):
        if tag == "form" and self.formulaires:
            self.formulaires.pop()
        for i in range(len(self.pile) - 1, -1, -1):
            if self.pile[i][0] == tag:
                self.pile = self.pile[:i]
                break
        self.boutons = [e for _t, e in self.pile if e is not None]


def chemins_templates(racine):
    dossier = racine / "templates" / "commercial"
    fichiers = sorted(dossier.rglob("*.html"))
    fichiers += [racine / nom for nom in TEMPLATES_COMMUNS if (racine / nom).is_file()]
    return fichiers


def menus():
    onglets, _ = structure_module(GESTION_COMMERCIALE)
    resultat = []
    def parcourir(noeuds, chemin, onglet):
        for n in noeuds:
            if n.get("separateur"):
                continue
            sous = bool(n.get("enfants"))
            cible = n.get("url") or n.get("action") or ""
            if sous:
                etat = "sous_menu"
                nature = "menu_conteneur"
            elif n.get("action"):
                etat = "action_interface_declaree"
                nature = "menu_commande"
            elif n.get("module"):
                etat = "autre_logiciel_declare"
                nature = "menu_commande"
            elif n.get("url"):
                etat = "lien_declare_non_teste"
                nature = "menu_commande"
            else:
                etat = "grise_sans_cible"
                nature = "menu_commande"
            complet = " › ".join(chemin + [n.get("titre", "")])
            resultat.append({
                "id": "", "famille": nature, "fichier_ou_menu": onglet,
                "ligne": "", "chemin": complet, "libelle": n.get("titre", ""),
                "element_html": "menu", "etat_code": etat,
                "condition": "permissions_et_donnees_a_tester",
                "cible_ou_action": cible, "mode_ou_fenetre": "a_verifier",
                "preuve_sage": n.get("preuve", "") or "A_VERIFIER",
                "fonction_sage_detaillee": "",
                "fonction_erp_verifiee_en_execution": "NON",
                "ecart": "", "scenario_test": "",
            })
            parcourir(n.get("enfants", []), chemin + [n.get("titre", "")], onglet)
    for onglet in onglets:
        parcourir(onglet["elements"], [onglet["titre"]], onglet["titre"])
    return resultat


def generer():
    racine = Path(settings.BASE_DIR)
    lignes = menus()
    menu_commande = sum(e["famille"] == "menu_commande" for e in lignes)
    menu_conteneur = sum(e["famille"] == "menu_conteneur" for e in lignes)
    autres = []
    for chemin in chemins_templates(racine):
        contenu = lire_fichier(chemin)
        lecteur = LecteurCommandes(chemin.relative_to(racine).as_posix(), contenu)
        lecteur.feed(contenu)
        autres.extend(lecteur.entrees)
    lignes.extend(autres)
    for i, ligne in enumerate(lignes, 1):
        ligne["id"] = "BC-%05d" % i
    famille = Counter(l["famille"] for l in lignes)
    etats = Counter(l["etat_code"] for l in lignes)
    ventes = tuple(Document.TYPES_VENTE)
    achats = tuple(Document.TYPES_ACHAT)
    stocks = tuple(Document.TYPES_STOCK)
    return lignes, {
        "menu_commandes": menu_commande,
        "menu_conteneurs": menu_conteneur,
        "controles_templates": len(autres),
        "controles_templates_interactifs_declares": sum(
            x["etat_code"] in ("interactif_declare_non_teste", "conditionnel_a_verifier")
            for x in autres
        ),
        "controles_templates_inactifs": sum(
            x["etat_code"] in ("inactif_html", "desactive_html", "desactive_ou_conditionnel")
            for x in autres
        ),
        "types_documents_vente": len(ventes),
        "types_documents_achat": len(achats),
        "types_documents_stock": len(stocks),
        "documents": [(code, dict(Document.TYPES)[code], groupe)
                      for groupe, codes in (("vente", ventes), ("achat", achats), ("stock", stocks))
                      for code in codes],
        "etats": etats,
        "famille": famille,
        "fichiers_templates": len(chemins_templates(racine)),
    }


class Command(BaseCommand):
    help = "Recensement statique auditable des menus et boutons de l'ERP commercial"

    def add_arguments(self, parser):
        parser.add_argument("--sortie", default="docs/retour/RECENSEMENT_BOUTONS_COMMERCIAL",
                            help="Préfixe des fichiers .csv et .md")

    def handle(self, *args, **options):
        lignes, bilan = generer()
        prefixe = Path(options["sortie"])
        prefixe.parent.mkdir(parents=True, exist_ok=True)
        chemin_csv = prefixe.with_suffix(".csv")
        chemin_md = prefixe.with_suffix(".md")
        with chemin_csv.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLONNES, extrasaction="ignore", delimiter=";")
            w.writeheader()
            w.writerows(lignes)
        repartition = "\n".join(
            "| %s | %s |" % (etat, n) for etat, n in sorted(bilan["etats"].items())
        )
        documents = "\n".join(
            "| %s | %s | %s |" % (groupe, code, libelle)
            for code, libelle, groupe in bilan["documents"]
        )
        texte = (
            "# Recensement des boutons — ERP Gestion commerciale\n\n"
            "Généré automatiquement depuis la version de code utilisée pour exécuter la commande.\n"
            "Attention : INVENTAIRE STATIQUE. Les droits réels, les fenêtres affichées et les fonctions\n"
            "Sage 100 V12 restent à vérifier dans des sessions de test et avec des preuves.\n\n"
            "## Résultat reproductible\n\n"
            "| Mesure | Nombre |\n|---|---:|\n"
            "| Commandes terminales des menus | %d |\n"
            "| Entrées ouvrant un sous-menu (non terminales) | %d |\n"
            "| Occurrences HTML dans les écrans Commercial + communs sélectionnés | %d |\n"
            "| HTML avec action déclarée (y compris conditions) | %d |\n"
            "| HTML inactifs / désactivés dans le code | %d |\n"
            "| Fichiers HTML analysés | %d |\n"
            "| Types de documents ventes / achats / stocks | %d / %d / %d |\n\n"
            % (
                bilan["menu_commandes"], bilan["menu_conteneurs"],
                bilan["controles_templates"],
                bilan["controles_templates_interactifs_declares"],
                bilan["controles_templates_inactifs"],
                bilan["fichiers_templates"],
                bilan["types_documents_vente"], bilan["types_documents_achat"],
                bilan["types_documents_stock"],
            )
        )
        texte += (
            "## État statique des commandes et contrôles\n\n"
            "| État | Occurrences |\n|---|---:|\n" + repartition + "\n\n"
            "## Types de documents couverts par les fenêtres génériques\n\n"
            "| Famille | Code interne | Document |\n|---|---|---|\n"
            + documents + "\n\n"
            "## Méthode et exclusions indispensables\n\n"
            "- Une entrée de sous-menu ne s'additionne pas aux commandes terminales pour mesurer des actions.\n"
            "- Une occurrence HTML dans un template commun n'est comptée qu'une fois, même si son\n"
            "  affichage est répliqué sur 21 types de pièces ou des milliers de documents.\n"
            "- Les commandes des menus rendues via core/_menu.html, core/_arbre.html et la barre verticale\n"
            "  sont comptées UNE fois depuis navigation.py, pour éviter les doublons visuels.\n"
            "- Inclut les templates/commercial/**/*.html et base.html, pagination.html, core/_auteurs.html.\n"
            "- Les formulaires HTML produits indirectement par Django ({{ form }}, champs de formsets,\n"
            "  boutons JavaScript créés à l'exécution) ne sont PAS tous quantifiés statiquement.\n"
            "- Les états disabled, HTML inactif ou URL/action déclarée ne garantissent pas le comportement\n"
            "  à l'exécution ni les droits. Les éléments sous {% if %}/{% for %} restent conditionnels.\n"
            "- Les 21 types de pièces ont des boutons variables selon brouillon/validé/annulé,\n"
            "  droits, encours, règlements, types de transformations, dépôt et lignes.\n"
            "- Pour obtenir un **nombre de boutons affichés**, il faudra rendre chaque type/statut et\n"
            "  profil utilisateur, parcourir les boîtes de dialogue et tester les clics et routes.\n"
            "- Référence Sage : support officiel Sage 100 V12, découpage V12.10 ; un intitulé identique\n"
            "  ne prouve pas qu'un dialogue ou un traitement est identique. Marquer « A_VERIFIER ».\n\n"
            "## Procédure de vérification fonctionnelle conjointe Claude / GPT\n\n"
            "Pour chaque ligne CSV, renseigner après essai le dialogue ouvert, la vue/route et sa\n"
            "méthode HTTP, droits, état initial et final, test des statuts, effets sur stock/écritures,\n"
            "preuve Sage (page + capture + édition V12), écarts et responsable de la correction.\n"
            "Aucune écriture SQL de production ni aucun taux fiscal inventé.\n"
        )
        chemin_md.write_text(texte, encoding="utf-8")
        self.stdout.write(
            "RECENSEMENT COMMERCIAL : %d commandes menus ; %d sous-menus ; "
            "%d occurrences HTML dans %d templates ; %d types de pièces (V=%d A=%d S=%d)."
            % (
                bilan["menu_commandes"], bilan["menu_conteneurs"],
                bilan["controles_templates"], bilan["fichiers_templates"],
                sum((bilan["types_documents_vente"], bilan["types_documents_achat"],
                     bilan["types_documents_stock"])),
                bilan["types_documents_vente"], bilan["types_documents_achat"],
                bilan["types_documents_stock"],
            )
        )
        self.stdout.write(str(chemin_csv))
        self.stdout.write(str(chemin_md))
