"""Structure de navigation de l'ERP : Module → Onglets → Éléments → Sous-éléments.

Chaque module est une application à part entière (sa fenêtre, son en-tête, ses
onglets). Cette définition unique alimente l'interface web (barre d'onglets et
arborescence latérale) et le client bureau (via /api/navigation/).

Pour ajouter une entrée : ajouter un `Element` dans l'onglet voulu. Un élément
peut avoir des `enfants` (sous-éléments), statiques ou calculés (`enfants_dynamiques`).
"""
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import parse_qsl, urlencode

from django.urls import reverse


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

    def lien(self):
        if not self.url:
            return None
        lien = reverse(self.url, args=self.args)
        return f"{lien}?{urlencode(self.query)}" if self.query else lien

    def tous_enfants(self):
        return self.enfants + (self.enfants_dynamiques() if self.enfants_dynamiques else [])


@dataclass
class Onglet:
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


def E(code, titre, url="", *args, icone="", enfants=None, dyn=None, **query):
    return Element(code, titre, url, args, query, icone, enfants or [], dyn)


# ---------------------------------------------------------------------------
# Éléments calculés à partir des données
# ---------------------------------------------------------------------------
def _journaux(url, prefixe):
    def construire():
        from apps.comptabilite.models import Journal

        return [E(f"{prefixe}.{j.code}", f"{j.code} - {j.intitule}", url, journal=j.code) for j in Journal.objects.all()]
    return construire


def _classes_comptables():
    from apps.comptabilite.models import CLASSES_SYSCOHADA

    return [E(f"plan.classe{n}", f"Classe {n} - {lib}", "comptabilite:comptes", classe=n) for n, lib in CLASSES_SYSCOHADA.items()]


def _documents(domaine, types):
    """Sous-éléments « liste » et « nouveau » pour chaque type de document."""
    return [E(f"{domaine}.{code.lower()}", titre, "commercial:documents", domaine, type=code) for code, titre in types]


def _nouveaux(domaine, types):
    return [E(f"{domaine}.nouveau.{code.lower()}", titre, "commercial:document_create", code) for code, titre in types]


TYPES_VENTE = [("DEVIS", "Devis"), ("COMMANDE", "Bons de commande"), ("LIVRAISON", "Bons de livraison"),
               ("FACTURE", "Factures"), ("AVOIR", "Avoirs")]
TYPES_ACHAT = [("ACHAT_COMMANDE", "Commandes fournisseurs"), ("ACHAT_RECEPTION", "Bons de réception"),
               ("ACHAT_FACTURE", "Factures fournisseurs"), ("ACHAT_AVOIR", "Avoirs fournisseurs")]
NOUVEAUX_VENTE = [("DEVIS", "Devis"), ("COMMANDE", "Bon de commande"), ("LIVRAISON", "Bon de livraison"),
                  ("FACTURE", "Facture"), ("AVOIR", "Avoir")]
NOUVEAUX_ACHAT = [("ACHAT_COMMANDE", "Commande fournisseur"), ("ACHAT_RECEPTION", "Bon de réception"),
                  ("ACHAT_FACTURE", "Facture fournisseur"), ("ACHAT_AVOIR", "Avoir fournisseur")]


# ---------------------------------------------------------------------------
# Modules
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
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("tiers", "Tiers", icone="bi-people", enfants=[
                E("tiers.clients", "Clients", "commercial:clients"),
                E("tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs"),
                E("tiers.nouveau_client", "Nouveau client", "commercial:tiers_create", type="CLIENT"),
                E("tiers.nouveau_fournisseur", "Nouveau fournisseur", "commercial:tiers_create", type="FOURNISSEUR"),
            ]),
            E("articles", "Articles", icone="bi-box-seam", enfants=[
                E("articles.liste", "Liste des articles", "commercial:articles"),
                E("articles.familles", "Familles d'articles", "commercial:familles"),
                E("articles.nouveau", "Nouvel article", "commercial:article_create"),
                E("articles.nouvelle_famille", "Nouvelle famille", "commercial:famille_create"),
            ]),
            E("parametres", "Paramètres", icone="bi-gear", enfants=[
                E("parametres.societe", "Société", "commercial:societe"),
            ]),
        ]),
        Onglet("ventes", "Ventes", "bi-receipt", [
            E("ventes.documents", "Documents de vente", icone="bi-folder2-open", enfants=[
                E("ventes.tous", "Tous les documents", "commercial:documents", "ventes"),
                *_documents("ventes", TYPES_VENTE),
            ]),
            E("ventes.nouveau", "Nouveau document", icone="bi-plus-square", enfants=_nouveaux("ventes", NOUVEAUX_VENTE)),
            E("ventes.suivi", "Suivi", icone="bi-eye", enfants=[
                E("ventes.brouillons", "Brouillons", "commercial:documents", "ventes", statut="BROUILLON"),
                E("ventes.impayees", "Factures non réglées", "commercial:documents", "ventes", impayees=1),
            ]),
        ]),
        Onglet("achats", "Achats", "bi-cart", [
            E("achats.documents", "Documents d'achat", icone="bi-folder2-open", enfants=[
                E("achats.tous", "Tous les documents", "commercial:documents", "achats"),
                *_documents("achats", TYPES_ACHAT),
            ]),
            E("achats.nouveau", "Nouveau document", icone="bi-plus-square", enfants=_nouveaux("achats", NOUVEAUX_ACHAT)),
            E("achats.suivi", "Suivi", icone="bi-eye", enfants=[
                E("achats.brouillons", "Brouillons", "commercial:documents", "achats", statut="BROUILLON"),
                E("achats.impayees", "Factures à payer", "commercial:documents", "achats", impayees=1),
            ]),
        ]),
        Onglet("stock", "Stock", "bi-boxes", [
            E("stock.etat", "État du stock", "commercial:stock", icone="bi-clipboard-data"),
            E("stock.mouvements", "Mouvements de stock", "commercial:mouvements", icone="bi-arrow-left-right"),
            E("stock.alertes", "Articles en alerte", "commercial:articles", icone="bi-exclamation-triangle", alerte=1),
        ]),
        Onglet("reglements", "Règlements", "bi-cash-coin", [
            E("reglements.liste", "Règlements", icone="bi-list-ul", enfants=[
                E("reglements.tous", "Tous les règlements", "commercial:reglements"),
                E("reglements.encaissements", "Encaissements clients", "commercial:reglements", sens="E"),
                E("reglements.decaissements", "Paiements fournisseurs", "commercial:reglements", sens="D"),
            ]),
            E("reglements.nouveau", "Nouveau règlement", "commercial:reglement_create", icone="bi-plus-square"),
        ]),
        Onglet("etats", "États", "bi-printer", [
            E("etats.ventes", "Analyse des ventes", icone="bi-graph-up", enfants=[
                E("etats.ventes.clients", "Ventes par client", "commercial:etat_ventes", vue="clients"),
                E("etats.ventes.articles", "Ventes par article", "commercial:etat_ventes", vue="articles"),
            ]),
            E("etats.echeances", "Échéancier", icone="bi-hourglass-split", enfants=[
                E("etats.balance_agee_clients", "Balance âgée clients", "commercial:etat_balance_agee", type="CLIENT"),
                E("etats.balance_agee_fournisseurs", "Balance âgée fournisseurs", "commercial:etat_balance_agee", type="FOURNISSEUR"),
            ]),
        ]),
    ],
)

COMPTABILITE = Module(
    code="comptabilite",
    titre="Comptabilité OHADA",
    description="Plan SYSCOHADA, saisie, journaux, grand livre, balance, états financiers",
    icone="bi-calculator",
    couleur="#2e7d32",
    prefixe="/comptabilite/",
    accueil="comptabilite:accueil",
    onglets=[
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("plan", "Plan comptable", icone="bi-list-ol", enfants=[
                E("plan.tout", "Tout le plan", "comptabilite:comptes"),
                E("plan.classes", "Par classe", dyn=_classes_comptables),
                E("plan.nouveau", "Nouveau compte", "comptabilite:compte_create"),
            ]),
            E("journaux", "Journaux", icone="bi-collection", enfants=[
                E("journaux.liste", "Liste des journaux", "comptabilite:journaux"),
                E("journaux.nouveau", "Nouveau journal", "comptabilite:journal_create"),
            ]),
            E("exercices", "Exercices", icone="bi-calendar3", enfants=[
                E("exercices.liste", "Liste des exercices", "comptabilite:exercices"),
                E("exercices.nouveau", "Nouvel exercice", "comptabilite:exercice_create"),
            ]),
        ]),
        Onglet("saisie", "Saisie", "bi-pencil-square", [
            E("saisie.nouvelle", "Saisie d'écriture", "comptabilite:ecriture_create", icone="bi-plus-square"),
            E("saisie.ecritures", "Écritures", icone="bi-journal-text", enfants=[
                E("saisie.toutes", "Toutes les écritures", "comptabilite:ecritures"),
                E("saisie.brouillard", "Brouillard", "comptabilite:ecritures", statut="BROUILLARD"),
                E("saisie.validees", "Écritures validées", "comptabilite:ecritures", statut="VALIDEE"),
                E("saisie.par_journal", "Par journal", dyn=_journaux("comptabilite:ecritures", "saisie.journal")),
            ]),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("traitement.lettrage", "Lettrage", "comptabilite:lettrage", icone="bi-link-45deg"),
        ]),
        Onglet("etats", "États", "bi-printer", [
            E("etats.journaux", "Journaux", icone="bi-journals", enfants=[
                E("etats.journal_general", "Journal général", "comptabilite:journal"),
                E("etats.journal.liste", "Journaux auxiliaires", dyn=_journaux("comptabilite:journal", "etats.journal")),
            ]),
            E("etats.grand_livre", "Grand livre", icone="bi-book", enfants=[
                E("etats.gl.general", "Grand livre général", "comptabilite:grand_livre"),
                E("etats.gl.tiers", "Grand livre des tiers", "comptabilite:grand_livre", compte_debut="4", compte_fin="4"),
            ]),
            E("etats.balance", "Balance", icone="bi-table", enfants=[
                E("etats.balance.generale", "Balance générale", "comptabilite:balance"),
                E("etats.balance.tiers", "Balance des tiers", "comptabilite:balance", compte_debut="4", compte_fin="4"),
            ]),
            E("etats.financiers", "États financiers", icone="bi-bank", enfants=[
                E("etats.financiers.bilan", "Bilan", "comptabilite:bilan"),
                E("etats.financiers.resultat", "Compte de résultat", "comptabilite:compte_resultat"),
            ]),
            E("etats.fiscal", "Fiscalité", icone="bi-percent", enfants=[
                E("etats.fiscal.tva", "Récapitulatif TVA", "comptabilite:tva"),
            ]),
        ]),
    ],
)

REPORTING = Module(
    code="reporting",
    titre="Reporting",
    description="Tableaux de bord, analyses des ventes, échéances et états de synthèse",
    icone="bi-bar-chart-line",
    couleur="#6a1b9a",
    prefixe="/reporting/",
    accueil="reporting:dashboard",
    onglets=[
        Onglet("synthese", "Synthèse", "bi-speedometer2", [
            E("synthese.dashboard", "Tableau de bord", "reporting:dashboard", icone="bi-speedometer2"),
        ]),
        Onglet("ventes", "Ventes", "bi-graph-up", [
            E("ventes.analyses", "Analyses", icone="bi-graph-up", enfants=[
                E("ventes.mois", "Évolution mensuelle", "reporting:ventes", vue="mois"),
                E("ventes.clients", "Par client", "reporting:ventes", vue="clients"),
                E("ventes.articles", "Par article", "reporting:ventes", vue="articles"),
            ]),
        ]),
        Onglet("tiers", "Tiers", "bi-people", [
            E("tiers.echeances", "Balances âgées", icone="bi-hourglass-split", enfants=[
                E("tiers.balance_agee_clients", "Clients", "reporting:balance_agee", type="CLIENT"),
                E("tiers.balance_agee_fournisseurs", "Fournisseurs", "reporting:balance_agee", type="FOURNISSEUR"),
            ]),
        ]),
        Onglet("finances", "Finances", "bi-bank", [
            E("finances.etats", "États de synthèse", icone="bi-bank", enfants=[
                E("finances.bilan", "Bilan", "reporting:bilan"),
                E("finances.resultat", "Compte de résultat", "reporting:compte_resultat"),
            ]),
        ]),
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


def _score(element, chemin, parametres):
    """Score de correspondance d'un élément avec la page courante (None si aucune)."""
    lien = element.lien()
    if not lien:
        return None
    chemin_el, _, requete = lien.partition("?")
    attendus = dict(parse_qsl(requete))
    if any(parametres.get(k) != v for k, v in attendus.items()):
        return None
    if chemin_el == chemin:
        return (2, len(attendus))
    return None


def _arbre(elements, chemin, parametres, meilleur):
    """Construit l'arbre sérialisable et mémorise le meilleur élément correspondant."""
    noeuds = []
    for el in elements:
        enfants = _arbre(el.tous_enfants(), chemin, parametres, meilleur)
        noeud = {"code": el.code, "titre": el.titre, "icone": el.icone, "url": el.lien(),
                 "enfants": enfants, "actif": False, "ouvert": False}
        score = _score(el, chemin, parametres)
        if score and (meilleur["score"] is None or score > meilleur["score"]):
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
        if n["url"]:
            return n["url"]
        lien = premier_lien(n["enfants"])
        if lien:
            return lien
    return None


def structure_module(module, chemin="", parametres=None):
    """Onglets + arbres du module, avec l'onglet et l'élément actifs."""
    parametres = parametres or {}
    meilleur = {"score": None, "noeud": None}
    onglets = []
    for onglet in module.onglets:
        avant = meilleur["noeud"]
        arbre = _arbre(onglet.elements, chemin, parametres, meilleur)
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
