"""Menus de l'ERP, organisés comme Sage 100c.

Chaque module est un logiciel à part entière doté d'une barre de menus :

    Fichier · Structure · Traitement · État · Fenêtre · ?

Chaque menu contient des éléments, qui peuvent ouvrir des sous-menus en cascade.
Comme dans Sage, les commandes non encore disponibles restent visibles mais grisées.
Cette définition unique alimente l'interface web et le client bureau (/api/navigation/).

Construire un élément avec `E(code, titre, nom_url, *args, **paramètres)` :
  - sans URL ni enfants      → commande grisée (non disponible) ;
  - `enfants=[...]`          → sous-menu ;
  - `dyn=fonction`           → sous-menu calculé à partir des données ;
  - `action="imprimer"`      → commande d'interface (imprimer, fermer, quitter) ;
  - `SEP()`                  → séparateur.
"""
import itertools
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import parse_qsl, urlencode

from django.urls import reverse

VERSION = "1.0"


@dataclass
class Element:
    code: str
    titre: str
    url: str = ""                      # nom d'URL Django (namespace:nom)
    args: tuple = ()
    query: dict = field(default_factory=dict)
    icone: str = ""
    enfants: list = field(default_factory=list)
    enfants_dynamiques: Optional[Callable] = None
    action: str = ""                   # imprimer | fermer | quitter
    separateur: bool = False

    def lien(self):
        if not self.url:
            return None
        lien = reverse(self.url, args=self.args)
        return f"{lien}?{urlencode(self.query)}" if self.query else lien

    def tous_enfants(self):
        return self.enfants + (self.enfants_dynamiques() if self.enfants_dynamiques else [])


@dataclass
class Onglet:
    """Un menu de la barre de menus (Fichier, Structure, Traitement, État…)."""
    code: str
    titre: str
    icone: str
    elements: list


@dataclass
class Module:
    code: str
    titre: str
    description: str
    icone: str
    couleur: str
    prefixe: str                       # préfixe d'URL qui identifie le module
    accueil: str                       # nom d'URL de la page d'accueil du module
    onglets: list


def E(code, titre, url="", *args, icone="", enfants=None, dyn=None, action="", **query):
    return Element(code, titre, url, args, query, icone, enfants or [], dyn, action)


_compteur = itertools.count()


def SEP():
    return Element(f"sep{next(_compteur)}", "", separateur=True)


# ---------------------------------------------------------------------------
# Menus communs
# ---------------------------------------------------------------------------
def menu_fichier(module, societe_url, fermer=True):
    return Onglet("fichier", "Fichier", "bi-folder2", [
        E("fichier.societe", "À propos de votre société", icone="bi-building", enfants=[
            E("fichier.societe.identification", "Identification", societe_url),
            *([E("fichier.societe.exercices", "Exercices comptables", "comptabilite:exercices")] if module == "comptabilite" else []),
        ]),
        E("fichier.autorisations", "Autorisations d'accès", "admin:auth_user_changelist", icone="bi-shield-lock"),
        SEP(),
        E("fichier.imprimer", "Imprimer…", icone="bi-printer", action="imprimer"),
        E("fichier.import", "Import", icone="bi-box-arrow-in-down"),
        E("fichier.export", "Export", icone="bi-box-arrow-up"),
        SEP(),
        *([E("fichier.fermer", "Fermer", icone="bi-x-square", action="fermer")] if fermer else []),
        E("fichier.quitter", "Quitter", icone="bi-power", action="quitter"),
    ])


def menu_fenetre(module):
    return Onglet("fenetre", "Fenêtre", "bi-window-stack", [
        E("fenetre.accueil", "Page d'accueil", MODULES_ACCUEIL[module], icone="bi-house"),
        SEP(),
        E("fenetre.portail", "Portail ERP OHADA", "core:portail", icone="bi-grid-3x3-gap"),
        *[E(f"fenetre.{code}", titre, accueil, icone=icone)
          for code, titre, accueil, icone in AUTRES_LOGICIELS if code != module],
    ])


def menu_aide(module):
    return Onglet("aide", "?", "bi-question-circle", [
        E("aide.a_propos", "À propos de l'ERP OHADA", f"{module}:a_propos", icone="bi-info-circle"),
    ])


MODULES_ACCUEIL = {"commercial": "commercial:accueil", "comptabilite": "comptabilite:accueil", "reporting": "reporting:dashboard"}
AUTRES_LOGICIELS = [
    ("commercial", "Gestion commerciale", "commercial:accueil", "bi-shop"),
    ("comptabilite", "Comptabilité OHADA", "comptabilite:accueil", "bi-calculator"),
    ("reporting", "Reporting", "reporting:dashboard", "bi-bar-chart-line"),
]


# ---------------------------------------------------------------------------
# Sous-menus calculés à partir des données
# ---------------------------------------------------------------------------
def _journaux(url, prefixe):
    def construire():
        from apps.comptabilite.models import Journal

        return [E(f"{prefixe}.{j.code}", f"{j.code} - {j.intitule}", url, journal=j.code) for j in Journal.objects.all()]
    return construire


def _documents(domaine, types):
    return [E(f"{domaine}.{code.lower()}", titre, "commercial:documents", domaine, type=code) for code, titre in types]


def _nouveaux(domaine, types):
    return [E(f"{domaine}.nouveau.{code.lower()}", titre, "commercial:document_create", code) for code, titre in types]


TYPES_VENTE = [("DEVIS", "Devis"), ("COMMANDE", "Bons de commande"), ("LIVRAISON", "Bons de livraison"),
               ("FACTURE", "Factures"), ("AVOIR", "Factures d'avoir")]
TYPES_ACHAT = [("ACHAT_COMMANDE", "Bons de commande"), ("ACHAT_RECEPTION", "Bons de réception"),
               ("ACHAT_FACTURE", "Factures"), ("ACHAT_AVOIR", "Factures d'avoir")]
NOUVEAUX_VENTE = [("DEVIS", "Devis"), ("COMMANDE", "Bon de commande"), ("LIVRAISON", "Bon de livraison"),
                  ("FACTURE", "Facture"), ("AVOIR", "Facture d'avoir")]
NOUVEAUX_ACHAT = [("ACHAT_COMMANDE", "Bon de commande"), ("ACHAT_RECEPTION", "Bon de réception"),
                  ("ACHAT_FACTURE", "Facture"), ("ACHAT_AVOIR", "Facture d'avoir")]


# ---------------------------------------------------------------------------
# Gestion commerciale
# ---------------------------------------------------------------------------
GESTION_COMMERCIALE = Module(
    code="commercial",
    titre="Gestion commerciale",
    description="Tiers, articles, ventes, achats, stock et règlements",
    icone="bi-shop",
    couleur="#1565c0",
    prefixe="/commercial/",
    accueil="commercial:accueil",
    onglets=[
        menu_fichier("commercial", "commercial:societe"),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("tiers.clients", "Clients", "commercial:clients", icone="bi-people"),
            E("tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs", icone="bi-truck"),
            E("structure.collaborateurs", "Collaborateurs", icone="bi-person-badge"),
            SEP(),
            E("articles.familles", "Familles", "commercial:familles", icone="bi-tags"),
            E("articles.liste", "Articles", "commercial:articles", icone="bi-box-seam"),
            E("structure.gammes", "Gammes"),
            E("structure.conditionnements", "Conditionnements"),
            E("structure.glossaires", "Glossaires"),
            SEP(),
            E("structure.depots", "Dépôts de stockage", icone="bi-house-gear"),
            E("structure.baremes", "Barèmes", icone="bi-percent", enfants=[
                E("structure.baremes.remises", "Rabais, remises et ristournes"),
                E("structure.baremes.commissions", "Commissions"),
                E("structure.baremes.promotions", "Soldes et promotions"),
            ]),
            SEP(),
            E("structure.plan_comptable", "Plan comptable", "comptabilite:comptes", icone="bi-list-ol"),
            E("structure.taux_taxes", "Taux de taxes"),
            E("structure.codes_journaux", "Codes journaux", "comptabilite:journaux"),
            E("structure.banques", "Banques"),
            E("structure.modeles_reglement", "Modèles de règlement"),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("ventes.documents", "Documents des ventes", icone="bi-receipt", enfants=[
                E("ventes.tous", "Tous les documents", "commercial:documents", "ventes"),
                SEP(),
                *_documents("ventes", TYPES_VENTE),
                SEP(),
                E("ventes.nouveau", "Nouveau", enfants=_nouveaux("ventes", NOUVEAUX_VENTE)),
            ]),
            E("achats.documents", "Documents des achats", icone="bi-cart", enfants=[
                E("achats.tous", "Tous les documents", "commercial:documents", "achats"),
                SEP(),
                *_documents("achats", TYPES_ACHAT),
                SEP(),
                E("achats.nouveau", "Nouveau", enfants=_nouveaux("achats", NOUVEAUX_ACHAT)),
            ]),
            E("stock.documents", "Documents des stocks", "commercial:mouvements", icone="bi-arrow-left-right"),
            E("traitement.documents_internes", "Documents internes"),
            SEP(),
            E("stock.inventaire", "Saisie des inventaires", "commercial:stock", icone="bi-clipboard-data"),
            E("stock.reappro", "Gestion des réapprovisionnements", "commercial:articles", icone="bi-exclamation-triangle", alerte=1),
            SEP(),
            E("reglements.clients", "Règlements clients", "commercial:reglements", icone="bi-cash-coin", sens="E"),
            E("reglements.fournisseurs", "Règlements fournisseurs", "commercial:reglements", icone="bi-cash-stack", sens="D"),
            E("reglements.nouveau", "Saisie d'un règlement", "commercial:reglement_create"),
            SEP(),
            E("traitement.encours", "Contrôle de l'encours client", "commercial:documents", "ventes", icone="bi-shield-exclamation", impayees=1),
            E("traitement.interrogation", "Interrogation commerciale", icone="bi-search", enfants=[
                E("traitement.interrogation.articles", "Articles", "commercial:stock", vue="interrogation"),
                E("traitement.interrogation.achats_a_payer", "Factures fournisseurs à payer", "commercial:documents", "achats", impayees=1),
                E("traitement.interrogation.brouillons_ventes", "Ventes en brouillon", "commercial:documents", "ventes", statut="BROUILLON"),
                E("traitement.interrogation.brouillons_achats", "Achats en brouillon", "commercial:documents", "achats", statut="BROUILLON"),
            ]),
            E("traitement.maj_comptable", "Mise à jour comptable", icone="bi-journal-arrow-up", enfants=[
                E("traitement.maj_comptable.ventes", "Écritures du journal des ventes", "comptabilite:ecritures", journal="VT"),
                E("traitement.maj_comptable.achats", "Écritures du journal des achats", "comptabilite:ecritures", journal="AC"),
            ]),
        ]),
        Onglet("etat", "État", "bi-printer", [
            E("etats.statistiques", "Statistiques", icone="bi-graph-up", enfants=[
                E("etats.ventes.clients", "Statistiques clients", "commercial:etat_ventes", vue="clients"),
                E("etats.ventes.articles", "Statistiques articles", "commercial:etat_ventes", vue="articles"),
                E("etats.stats_fournisseurs", "Statistiques fournisseurs"),
                E("etats.stats_collaborateurs", "Statistiques collaborateurs"),
            ]),
            E("etats.palmares", "Palmarès", icone="bi-trophy", enfants=[
                E("etats.palmares.clients", "Palmarès clients", "commercial:etat_ventes", vue="clients", tri="ca"),
                E("etats.palmares.articles", "Palmarès articles", "commercial:etat_ventes", vue="articles", tri="ca"),
            ]),
            SEP(),
            E("etats.inventaire", "Inventaire", "commercial:stock", icone="bi-clipboard-check", vue="inventaire"),
            E("etats.mouvements", "Mouvements de stock", "commercial:mouvements", icone="bi-arrow-left-right", vue="etat"),
            SEP(),
            E("etats.echeancier", "Échéancier", icone="bi-hourglass-split", enfants=[
                E("etats.balance_agee_clients", "Échéancier clients", "commercial:etat_balance_agee", type="CLIENT"),
                E("etats.balance_agee_fournisseurs", "Échéancier fournisseurs", "commercial:etat_balance_agee", type="FOURNISSEUR"),
            ]),
        ]),
        menu_fenetre("commercial"),
        menu_aide("commercial"),
    ],
)

# ---------------------------------------------------------------------------
# Comptabilité
# ---------------------------------------------------------------------------
COMPTABILITE = Module(
    code="comptabilite",
    titre="Comptabilité OHADA",
    description="Plan SYSCOHADA, saisie, journaux, grand livre, balance, états financiers",
    icone="bi-calculator",
    couleur="#2e7d32",
    prefixe="/comptabilite/",
    accueil="comptabilite:accueil",
    onglets=[
        menu_fichier("comptabilite", "comptabilite:societe"),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("structure.plan", "Plan comptable", "comptabilite:comptes", icone="bi-list-ol"),
            E("structure.plan_tiers", "Plan tiers", icone="bi-people", enfants=[
                E("structure.plan_tiers.clients", "Clients", "commercial:clients"),
                E("structure.plan_tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs"),
            ]),
            E("structure.plan_analytique", "Plan analytique"),
            E("structure.plan_reporting", "Plan reporting"),
            SEP(),
            E("structure.taux_taxes", "Taux de taxes"),
            E("structure.journaux", "Codes journaux", "comptabilite:journaux", icone="bi-collection"),
            E("structure.journaux_analytiques", "Codes journaux analytiques"),
            E("structure.postes_budgetaires", "Postes budgétaires"),
            SEP(),
            E("structure.banques", "Banques"),
            E("structure.modeles_saisie", "Modèles de saisie"),
            E("structure.modeles_grille", "Modèles de grille"),
            E("structure.modeles_reglement", "Modèles de règlement"),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("traitement.saisie_journaux", "Saisie des journaux", icone="bi-journal-text", enfants=[
                E("traitement.saisie_journaux.tous", "Tous les journaux", "comptabilite:ecritures"),
                SEP(),
            ], dyn=_journaux("comptabilite:ecritures", "traitement.saisie_journaux")),
            E("traitement.saisie_piece", "Saisie par pièce", "comptabilite:ecriture_create", icone="bi-pencil-square"),
            E("traitement.saisie_bancaire", "Saisie des opérations bancaires"),
            E("traitement.saisie_analytique", "Saisie des écritures analytiques"),
            E("traitement.brouillard", "Écritures au brouillard", "comptabilite:ecritures", icone="bi-hourglass", statut="BROUILLARD"),
            SEP(),
            E("traitement.lettrage", "Interrogation et lettrage", "comptabilite:lettrage", icone="bi-link-45deg"),
            E("traitement.lettrage_auto", "Lettrage automatique"),
            E("traitement.rapprochement", "Rapprochement bancaire manuel"),
            E("traitement.reglement_tiers", "Règlement tiers", "commercial:reglement_create"),
            E("traitement.relance", "Rappel / relance clients", "comptabilite:balance_agee", type="CLIENT", vue="relance"),
            SEP(),
            E("traitement.tva", "Déclaration de taxes", "comptabilite:tva", icone="bi-percent"),
            E("traitement.revision", "Révision par cycle"),
            SEP(),
            E("traitement.fin_exercice", "Fin d'exercice", icone="bi-calendar-check", enfants=[
                E("traitement.fin_exercice.nouvel", "Nouvel exercice", "comptabilite:exercice_create"),
                E("traitement.fin_exercice.cloture", "Clôture de l'exercice", "comptabilite:exercices", vue="cloture"),
                E("traitement.fin_exercice.journaux", "Clôture des journaux"),
            ]),
        ]),
        Onglet("etat", "État", "bi-printer", [
            E("etats.journaux", "Journaux", icone="bi-journals", enfants=[
                E("etats.journal_general", "Journal général", "comptabilite:journal"),
                E("etats.journal.liste", "Journaux auxiliaires", dyn=_journaux("comptabilite:journal", "etats.journal")),
            ]),
            E("etats.grand_livre", "Grand-livre", icone="bi-book", enfants=[
                E("etats.gl.general", "Grand-livre des comptes", "comptabilite:grand_livre"),
                E("etats.gl.tiers", "Grand-livre des tiers", "comptabilite:grand_livre", compte_debut="4", compte_fin="4"),
            ]),
            E("etats.balance", "Balance", icone="bi-table", enfants=[
                E("etats.balance.generale", "Balance des comptes", "comptabilite:balance"),
                E("etats.balance.tiers", "Balance des tiers", "comptabilite:balance", compte_debut="4", compte_fin="4"),
                E("etats.balance.agee", "Balance âgée", "comptabilite:balance_agee", type="CLIENT"),
            ]),
            E("etats.echeancier", "Échéancier", icone="bi-hourglass-split", enfants=[
                E("etats.echeancier.clients", "Échéancier clients", "comptabilite:balance_agee", type="CLIENT", vue="echeancier"),
                E("etats.echeancier.fournisseurs", "Échéancier fournisseurs", "comptabilite:balance_agee", type="FOURNISSEUR"),
            ]),
            SEP(),
            E("etats.financiers", "Bilan et compte de résultat", icone="bi-bank", enfants=[
                E("etats.financiers.bilan", "Bilan", "comptabilite:bilan"),
                E("etats.financiers.resultat", "Compte de résultat", "comptabilite:compte_resultat"),
                E("etats.financiers.sig", "Soldes intermédiaires de gestion", "comptabilite:compte_resultat", vue="sig"),
            ]),
            E("etats.declarations", "Déclarations", icone="bi-file-earmark-text", enfants=[
                E("etats.fiscal.tva", "Déclaration de TVA", "comptabilite:tva", vue="etat"),
                E("etats.dsf", "Déclaration statistique et fiscale (DSF)"),
            ]),
        ]),
        menu_fenetre("comptabilite"),
        menu_aide("comptabilite"),
    ],
)

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
REPORTING = Module(
    code="reporting",
    titre="Reporting",
    description="Tableaux de bord, statistiques, échéanciers et états de synthèse",
    icone="bi-bar-chart-line",
    couleur="#6a1b9a",
    prefixe="/reporting/",
    accueil="reporting:dashboard",
    onglets=[
        menu_fichier("reporting", "commercial:societe"),
        Onglet("etat", "État", "bi-printer", [
            E("synthese.dashboard", "Tableau de bord", "reporting:dashboard", icone="bi-speedometer2"),
            SEP(),
            E("ventes.analyses", "Statistiques des ventes", icone="bi-graph-up", enfants=[
                E("ventes.mois", "Évolution mensuelle", "reporting:ventes", vue="mois"),
                E("ventes.clients", "Par client", "reporting:ventes", vue="clients"),
                E("ventes.articles", "Par article", "reporting:ventes", vue="articles"),
            ]),
            E("tiers.echeances", "Échéanciers", icone="bi-hourglass-split", enfants=[
                E("tiers.balance_agee_clients", "Clients", "reporting:balance_agee", type="CLIENT"),
                E("tiers.balance_agee_fournisseurs", "Fournisseurs", "reporting:balance_agee", type="FOURNISSEUR"),
            ]),
            SEP(),
            E("finances.etats", "États de synthèse", icone="bi-bank", enfants=[
                E("finances.bilan", "Bilan", "reporting:bilan"),
                E("finances.resultat", "Compte de résultat", "reporting:compte_resultat"),
                E("finances.sig", "Soldes intermédiaires de gestion", "reporting:compte_resultat", vue="sig"),
            ]),
        ]),
        menu_fenetre("reporting"),
        menu_aide("reporting"),
    ],
)

MODULES = [GESTION_COMMERCIALE, COMPTABILITE, REPORTING]
MODULES_PAR_CODE = {m.code: m for m in MODULES}


# ---------------------------------------------------------------------------
# Résolution de l'élément actif
# ---------------------------------------------------------------------------
def module_pour_chemin(chemin):
    for module in MODULES:
        if chemin.startswith(module.prefixe):
            return module
    return None


def _module_cible(module, lien):
    """Code du logiciel qui affiche ce lien (« » si c'est le module lui-même, « web » hors logiciel)."""
    if not lien or lien.startswith(module.prefixe):
        return ""
    autre = module_pour_chemin(lien)
    return autre.code if autre else "web"


def _score(element, chemin, parametres):
    """Score de correspondance d'un élément avec la page courante (None si aucune)."""
    lien = element.lien()
    if not lien:
        return None
    chemin_el, _, requete = lien.partition("?")
    attendus = dict(parse_qsl(requete))
    if chemin_el != chemin or any(parametres.get(k) != v for k, v in attendus.items()):
        return None
    return len(attendus)


def _arbre(module, elements, chemin, parametres, meilleur):
    """Construit l'arbre sérialisable et mémorise le meilleur élément correspondant."""
    noeuds = []
    for el in elements:
        if el.separateur:
            noeuds.append({"code": el.code, "separateur": True, "titre": "", "enfants": [], "url": None,
                           "actif": False, "ouvert": False, "disponible": False, "action": "", "module": ""})
            continue
        enfants = _arbre(module, el.tous_enfants(), chemin, parametres, meilleur)
        lien = el.lien()
        cible = _module_cible(module, lien)
        noeud = {"code": el.code, "titre": el.titre, "icone": el.icone, "url": lien, "enfants": enfants,
                 "action": el.action, "module": cible, "separateur": False,
                 "disponible": bool(lien or enfants or el.action), "actif": False, "ouvert": False}
        score = _score(el, chemin, parametres) if not cible else None
        if score is not None and (meilleur["score"] is None or score > meilleur["score"]):
            meilleur.update(score=score, noeud=noeud)
        noeuds.append(noeud)
    return noeuds


def _marquer_ouverts(noeuds):
    """Ouvre les branches qui contiennent l'élément actif."""
    contient = False
    for n in noeuds:
        if _marquer_ouverts(n["enfants"]) or n["actif"]:
            n["ouvert"] = True
            contient = True
    return contient


def chemin_vers_actif(noeuds):
    """Liste des nœuds de la racine jusqu'à l'élément actif (fil d'Ariane)."""
    for n in noeuds:
        if n["actif"]:
            return [n]
        suite = chemin_vers_actif(n["enfants"])
        if suite:
            return [n] + suite
    return []


def premier_lien(noeuds):
    for n in noeuds:
        if n["url"] and not n["module"]:
            return n["url"]
        lien = premier_lien(n["enfants"])
        if lien:
            return lien
    return None


def structure_module(module, chemin="", parametres=None):
    """Menus du module, avec le menu et l'élément actifs."""
    parametres = parametres or {}
    meilleur = {"score": None, "noeud": None}
    onglets = []
    for onglet in module.onglets:
        avant = meilleur["noeud"]
        arbre = _arbre(module, onglet.elements, chemin, parametres, meilleur)
        onglets.append({"code": onglet.code, "titre": onglet.titre, "icone": onglet.icone, "elements": arbre,
                        "url": premier_lien(arbre), "contient_actif": False})
        if meilleur["noeud"] is not avant:
            for o in onglets:
                o["contient_actif"] = False
            onglets[-1]["contient_actif"] = True
    if meilleur["noeud"]:
        meilleur["noeud"]["actif"] = True
        for o in onglets:
            _marquer_ouverts(o["elements"])
    return onglets, meilleur["noeud"]


def serialiser_module(module):
    onglets, _ = structure_module(module)
    return {"code": module.code, "titre": module.titre, "description": module.description,
            "icone": module.icone, "couleur": module.couleur, "accueil": reverse(module.accueil), "onglets": onglets}
