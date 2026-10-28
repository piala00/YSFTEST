"""Menus de l'ERP, organisés comme Sage 100c.

Chaque module est un logiciel à part entière doté d'une barre de menus :

    Fichier · Édition · Structure · Traitement · Etat · Fenêtre · ?

La Gestion commerciale reprend le « Découpage fonctionnel détaillé Sage 100 Gestion
commerciale V11 » (menus et sous-menus dans le même ordre).

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
    action: str = ""                   # imprimer | fermer | quitter | actualiser | couper | copier…
    separateur: bool = False
    preuve: str = ""                   # DOC-V12 | ERG-CLASSIQUE | INDICATIF | AJOUT-ERP (voir PREUVES)
    edition: str = ""                  # "transport" | "commerce" : entrée propre à un métier (vide : les deux)

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


def E(code, titre, url="", *args, icone="", enfants=None, dyn=None, action="", preuve="", edition="", **query):
    return Element(code, titre, url, args, query, icone, enfants or [], dyn, action, preuve=preuve, edition=edition)


# Niveaux de preuve (skill « sage-100-gescom-v12-ui ») : origine de chaque entrée de menu
PREUVES = {
    "DOC-V12": "Cité dans le découpage fonctionnel officiel Sage 100 (V11/V12) du logiciel concerné",
    "ERG-CLASSIQUE": "Ergonomie Sage classique, à vérifier sur une installation V12",
    "INDICATIF": "Proposition fonctionnelle, non vérifiée sur une capture V12",
    "AJOUT-ERP": "Ajout propre à l'ERP OHADA (absent de Sage)",
    "DOC-TIERS": "Cité par une source tierce (partenaire, formation), à confirmer sur Sage",
}


# Gestion commerciale : découpage officiel V11/V12 ; Comptabilité : ergonomie Sage 100 classique et skill
# « sage100-comptabilite-v5-v12-expert », à confirmer sur le découpage officiel Comptabilité ; Reporting : propre à l'ERP
PREUVE_PAR_DEFAUT = {"commercial": "DOC-V12", "comptabilite": "ERG-CLASSIQUE", "reporting": "AJOUT-ERP", "transport": "AJOUT-ERP",
                     "billetterie": "AJOUT-ERP", "colis": "AJOUT-ERP", "garage": "AJOUT-ERP", "personnel": "AJOUT-ERP"}

_compteur = itertools.count()


def SEP():
    return Element(f"sep{next(_compteur)}", "", separateur=True)


# ---------------------------------------------------------------------------
# Menus communs
# ---------------------------------------------------------------------------
def menu_fichier_comptabilite():
    """Fichier de Sage 100 Comptabilité, selon le découpage fonctionnel officiel S02 (matrice des 8 offres, sans
    numéro de build ; skill « sage100-matrices-menus-complement ») : Paramètres société et ses rubriques, puis
    lecture des informations, autorisations, import / export, impression et outils."""
    D, I = "DOC-V12", "INDICATIF"
    P = "fichier.parametres"
    return Onglet("fichier", "Fichier", "bi-folder2", [
        E("fichier.nouveau", "Nouveau", icone="bi-file-earmark-plus", preuve=D),
        E("fichier.ouvrir", "Ouvrir", icone="bi-folder2-open", preuve=D),
        E("fichier.favoris", "Favoris", icone="bi-star", preuve=D),
        E("fichier.fermer", "Fermer", icone="bi-x-square", action="fermer", preuve=D),
        SEP(),
        E(P, "Paramètres société", icone="bi-building", preuve=D, enfants=[
            E(f"{P}.identification", "Identification", preuve=D, enfants=[
                # « Fichiers liés » figure dans Monnaie & Formats : affiché sur la page Identification de l'ERP
                E(f"{P}.identification.identification", "Identification", "comptabilite:societe", preuve=D),
                E(f"{P}.identification.monnaie", "Monnaie & Formats", preuve=D),
                E(f"{P}.identification.preferences", "Préférences", preuve=D),
                E(f"{P}.identification.exercices", "Exercices", "comptabilite:exercices", preuve=D),
                E(f"{P}.identification.reports", "Reports à-nouveaux", preuve=D),
                E(f"{P}.identification.securite", "Sécurité", preuve=D),
            ]),
            E(f"{P}.comptes", "Comptes généraux", preuve=D),
            E(f"{P}.tiers", "Tiers", preuve=D),
            E(f"{P}.analytique", "Analytique", preuve=D),
            E(f"{P}.tva", "Tva et taxes", "comptabilite:structure", "taxes", preuve=D, vue="parametres"),
            E(f"{P}.fiscaux", "Paramètres fiscaux", preuve=D),
            E(f"{P}.contacts", "Contacts", preuve=D),
            E(f"{P}.international", "International", preuve=D),
            E(f"{P}.banque", "Banque", "comptabilite:structure", "banques", preuve=D, vue="parametres"),
            E(f"{P}.comptabilisation", "Comptabilisation", preuve=D),
            E(f"{P}.echanges", "Echange de données", preuve=D),
            E(f"{P}.rappel", "Rappel/ Recouvrement", preuve=D),
            E(f"{P}.efacture", "Factures électroniques", preuve=D),
            E(f"{P}.colonnage", "Colonnage", preuve=D),
            E(f"{P}.modeles", "Modèles", preuve=D),
            E(f"{P}.saisie", "Saisie - Personnalisation en saisie", preuve=D),
        ]),
        E("fichier.lire_infos", "Lire les informations", preuve=D),
        E("fichier.configuration", "Configuration système et partage", preuve=D),
        E("fichier.autorisations", "Autorisations d'accès", "comptabilite:autorisations", icone="bi-shield-lock", preuve=D),
        E("fichier.journal_evenements", "Journal des événements", "comptabilite:journal_evenements", icone="bi-clock-history", preuve="AJOUT-ERP"),
        E("fichier.echanges", "Échanges entre agences", "comptabilite:echanges", icone="bi-arrow-left-right", preuve="AJOUT-ERP"),
        E("fichier.corrections", "Demandes de correction (direction / agences)", "comptabilite:corrections", icone="bi-flag",
          preuve="AJOUT-ERP"),
        SEP(),
        E("fichier.importer", "Importer", icone="bi-box-arrow-in-down", preuve=D),
        E("fichier.exporter", "Exporter", icone="bi-box-arrow-up", preuve=D),
        SEP(),
        E("fichier.imprimer_parametres", "Imprimer les paramètres société", preuve=D),
        E("fichier.mise_en_page", "Mise en page", preuve=I),
        E("fichier.imprimer", "Imprimer…", icone="bi-printer", action="imprimer", preuve=I),
        E("fichier.impression_differee", "Impression différée", preuve=I),
        SEP(),
        E("fichier.outils", "Outils", icone="bi-tools", preuve=D, enfants=[
            E("fichier.outils.maintenance", "Maintenance", "core:poste", preuve=D),
            E("fichier.outils.sauvegarde", "Sauvegarder ma société", "comptabilite:sauvegarde", preuve=D),
            E("fichier.outils.restauration", "Restaurer ma société", "comptabilite:sauvegarde", preuve=D, vue="restaurer"),
            E("fichier.outils.historique", "Historique des modifications et des suppressions", preuve=D),
            E("fichier.outils.evenements_legaux", "Journal des événements légaux", preuve=D),
        ]),
        SEP(),
        E("fichier.quitter", "Quitter", icone="bi-power", action="quitter"),
    ])


def menu_fichier(module, societe_url, fermer=True):
    return Onglet("fichier", "Fichier", "bi-folder2", [
        E("fichier.societe", "Paramètres société", icone="bi-building", enfants=[
            E("fichier.societe.identification", "Identification", societe_url),
            *([E("fichier.societe.exercices", "Exercices comptables", "comptabilite:exercices")] if module == "comptabilite" else []),
        ]),
        E("fichier.autorisations", "Autorisations d'accès", f"{module}:autorisations", icone="bi-shield-lock"),
        E("fichier.journal_evenements", "Journal des événements", f"{module}:journal_evenements", icone="bi-clock-history", preuve="AJOUT-ERP"),
        E("fichier.sauvegarde", "Sauvegarde et restauration", f"{module}:sauvegarde", icone="bi-hdd", preuve="AJOUT-ERP"),
        E("fichier.poste", "Administration du poste", "core:poste", icone="bi-pc-display", preuve="AJOUT-ERP"),
        *([E("fichier.echanges", "Échanges entre agences", f"{module}:echanges", icone="bi-arrow-left-right",
             preuve="AJOUT-ERP")] if module in ("commercial", "transport") else []),
        *([E("fichier.reprise", "Reprise d'un dossier existant", f"{module}:reprise_dossier", icone="bi-database-down",
             preuve="AJOUT-ERP")] if module in ("commercial", "comptabilite") else []),
        SEP(),
        E("fichier.imprimer", "Imprimer…", icone="bi-printer", action="imprimer"),
        E("fichier.import", "Import", icone="bi-box-arrow-in-down"),
        E("fichier.export", "Export", icone="bi-box-arrow-up"),
        SEP(),
        *([E("fichier.fermer", "Fermer", icone="bi-x-square", action="fermer")] if fermer else []),
        E("fichier.quitter", "Quitter", icone="bi-power", action="quitter"),
    ])


def menu_edition():
    """Menu Édition : non détaillé par le découpage V12.10, repris de l'ergonomie Sage classique."""
    P = "ERG-CLASSIQUE"
    return Onglet("edition", "Édition", "bi-pencil", [
        E("edition.annuler", "Annuler", icone="bi-arrow-counterclockwise", action="annuler", preuve=P),
        SEP(),
        E("edition.couper", "Couper", icone="bi-scissors", action="couper", preuve=P),
        E("edition.copier", "Copier", icone="bi-files", action="copier", preuve=P),
        E("edition.coller", "Coller", icone="bi-clipboard", action="coller", preuve=P),
        E("edition.effacer", "Effacer", icone="bi-eraser", action="effacer", preuve=P),
        E("edition.selectionner_tout", "Sélectionner tout", action="selectionner_tout", preuve=P),
        SEP(),
        E("edition.ajouter", "Ajouter", icone="bi-plus-square", action="ajouter", preuve=P),
        E("edition.modifier", "Voir/Modifier", icone="bi-pencil-square", action="modifier", preuve=P),
        E("edition.supprimer", "Supprimer", icone="bi-trash", preuve=P),
        E("edition.dupliquer", "Dupliquer", icone="bi-copy", preuve=P),
        SEP(),
        E("edition.precedent", "Précédent", icone="bi-chevron-left", preuve=P),
        E("edition.suivant", "Suivant", icone="bi-chevron-right", preuve=P),
        SEP(),
        E("edition.rechercher", "Rechercher", icone="bi-search", action="rechercher", preuve=P),
        E("edition.atteindre", "Atteindre", preuve=P),
        SEP(),
        E("edition.inverseur", "Inverseur", preuve=P),
        E("edition.calculette", "Calculette", icone="bi-calculator", preuve=P),
        E("edition.journal", "Journal de traitement", preuve=P),
    ])


def menu_fenetre(module):
    return Onglet("fenetre", "Fenêtre", "bi-window-stack", [
        E("fenetre.reorganiser", "Réorganiser", icone="bi-grid-1x2", action="reorganiser"),
        E("fenetre.actualiser", "Actualiser", icone="bi-arrow-clockwise", action="actualiser"),
        E("fenetre.personnaliser", "Personnaliser"),
        E("fenetre.personnaliser_ecrans", "Personnaliser les écrans"),
        E("fenetre.personnaliser_liste", "Personnaliser la liste"),
        E("fenetre.ajustement", "Ajustement automatique des colonnes"),
        SEP(),
        E("fenetre.preferences", "Préférences"),
        E("fenetre.barre_verticale", "Barre verticale", icone="bi-layout-sidebar", action="barre_verticale"),
        E("fenetre.mode_assistant", "Mode assistant"),
        E("fenetre.mode_personnalise", "Mode personnalisé"),
        SEP(),
        E("fenetre.accueil", "Page d'accueil", MODULES_ACCUEIL[module], icone="bi-house", preuve="AJOUT-ERP"),
        E("fenetre.portail", "Portail ERP OHADA", "core:portail", icone="bi-grid-3x3-gap", preuve="AJOUT-ERP"),
        *[E(f"fenetre.{code}", titre, accueil, icone=icone, preuve="AJOUT-ERP")
          for code, titre, accueil, icone in AUTRES_LOGICIELS if code != module],
    ])


def menu_aide(module):
    return Onglet("aide", "?", "bi-question-circle", [
        E("aide.a_propos", "À propos de l'ERP OHADA", f"{module}:a_propos", icone="bi-info-circle", preuve="ERG-CLASSIQUE"),
    ])


MODULES_ACCUEIL = {"commercial": "commercial:accueil", "comptabilite": "comptabilite:accueil", "analytique": "analytique:accueil", "reporting": "reporting:dashboard",
                   "transport": "transport:accueil", "billetterie": "billetterie:accueil", "colis": "colis:accueil",
                   "garage": "garage:accueil", "personnel": "personnel:accueil"}
AUTRES_LOGICIELS = [
    ("commercial", "Gestion commerciale", "commercial:accueil", "bi-shop"),
    ("comptabilite", "Comptabilité générale", "comptabilite:accueil", "bi-calculator"),
    ("analytique", "Comptabilité analytique", "analytique:accueil", "bi-diagram-3"),
    ("reporting", "Reporting", "reporting:dashboard", "bi-bar-chart-line"),
    ("transport", "Direction de l'agence", "transport:accueil", "bi-building-gear"),
    ("billetterie", "Billetterie", "billetterie:accueil", "bi-ticket-perforated"),
    ("colis", "Colis et expéditions", "colis:accueil", "bi-box-seam"),
    ("garage", "Garage", "garage:accueil", "bi-wrench-adjustable"),
    ("personnel", "Personnel et paie", "personnel:accueil", "bi-people"),
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


TYPES_VENTE = [("DEVIS", "Devis"), ("COMMANDE", "Bon de commande"), ("PREPARATION", "Préparation de livraison"),
               ("LIVRAISON", "Bon de livraison"), ("RETOUR", "Bon de retour"), ("AVOIR_FINANCIER", "Bon d'avoir financier"),
               ("FACTURE", "Facture"), ("FACTURE_RETOUR", "Facture de retour"), ("AVOIR", "Facture d'avoir")]
TYPES_ACHAT = [("ACHAT_DEMANDE", "Demande d'achat"), ("ACHAT_PREPARATION", "Préparation de commande"),
               ("ACHAT_COMMANDE", "Bon de commande"), ("ACHAT_RECEPTION", "Bon de livraison"), ("ACHAT_RETOUR", "Bon de retour"),
               ("ACHAT_AVOIR_FINANCIER", "Bon d'avoir financier"), ("ACHAT_FACTURE", "Facture"),
               ("ACHAT_FACTURE_RETOUR", "Facture de retour"), ("ACHAT_AVOIR", "Facture d'avoir")]
TYPES_STOCK = [("STOCK_ENTREE", "Mouvement d'entrée"), ("STOCK_SORTIE", "Mouvement de sortie"),
               ("STOCK_VIREMENT", "Mouvement de transfert")]


# ---------------------------------------------------------------------------
# Gestion commerciale
# ---------------------------------------------------------------------------
GESTION_COMMERCIALE = Module(
    code="commercial",
    titre="Gestion commerciale",
    description="Tiers, articles, documents des ventes, des achats et des stocks, règlements",
    icone="bi-shop",
    couleur="#1565c0",
    prefixe="/commercial/",
    accueil="commercial:accueil",
    onglets=[
        Onglet("fichier", "Fichier", "bi-folder2", [
            E("fichier.nouveau", "Nouveau"),
            E("fichier.ouvrir", "Ouvrir"),
            E("fichier.favoris", "Favoris"),
            E("fichier.fermer", "Fermer", icone="bi-x-square", action="fermer"),
            SEP(),
            E("fichier.parametres", "Paramètres société", icone="bi-building", enfants=[
                E("fichier.parametres.identification", "Identification", "commercial:societe"),
                E("fichier.parametres.contacts", "Vos contacts"),
                E("fichier.parametres.securite", "Sécurité"),
                E("fichier.parametres.articles", "Articles"),
                E("fichier.parametres.comptes", "Comptes généraux"),
                E("fichier.parametres.tiers", "Tiers", enfants=[
                    E("fichier.parametres.tiers.categories", "Catégories tarifaires", "commercial:categories"),
                ]),
                E("fichier.parametres.ressources", "Ressources"),
                E("fichier.parametres.analytique", "Analytique"),
                E("fichier.parametres.tva", "Tva et taxes"),
                E("fichier.parametres.contacts_types", "Contacts"),
                E("fichier.parametres.international", "International"),
                E("fichier.parametres.banques", "Banques"),
                E("fichier.parametres.agences", "Agences", "commercial:agences", preuve="AJOUT-ERP"),
                E("fichier.parametres.documents", "Documents"),
                E("fichier.parametres.logistique", "Logistique", "commercial:societe", section="logistique"),
                E("fichier.parametres.comptabilisation", "Comptabilisation"),
                E("fichier.parametres.echanges", "Echanges de données"),
                E("fichier.parametres.agenda", "Agenda"),
                E("fichier.parametres.efacture", "Factures électroniques"),
                E("fichier.parametres.colonnage", "Colonnage"),
            ]),
            E("fichier.lire_infos", "Lire les informations"),
            E("fichier.configuration", "Configuration système et partage"),
            E("fichier.autorisations", "Autorisations d'accès", "commercial:autorisations", icone="bi-shield-lock"),
            E("fichier.journal_evenements", "Journal des événements", "commercial:journal_evenements", icone="bi-clock-history", preuve="AJOUT-ERP"),
            E("fichier.sauvegarde", "Sauvegarde et restauration", "commercial:sauvegarde", icone="bi-hdd", preuve="AJOUT-ERP"),
            E("fichier.reprise", "Reprise d'un dossier existant", "commercial:reprise_dossier", icone="bi-database-down",
              preuve="AJOUT-ERP"),
            E("fichier.echanges", "Échanges entre agences", "commercial:echanges", icone="bi-arrow-left-right", preuve="AJOUT-ERP"),
            SEP(),
            E("fichier.importer", "Importer", icone="bi-box-arrow-in-down"),
            E("fichier.exporter", "Exporter", icone="bi-box-arrow-up"),
            E("fichier.format_import", "Format import/export paramétrable"),
            E("fichier.site_a_site", "Communication site à site"),
            E("fichier.paiement_ligne", "Paiement en ligne"),
            SEP(),
            E("fichier.mise_en_page", "Mise en page"),
            E("fichier.imprimer", "Imprimer…", icone="bi-printer", action="imprimer", preuve="ERG-CLASSIQUE"),
            E("fichier.format_impression", "Format d'impression"),
            E("fichier.impression_differee", "Impression différée"),
            SEP(),
            E("fichier.outils", "Outils"),
            E("fichier.quitter", "Quitter", icone="bi-power", action="quitter", preuve="ERG-CLASSIQUE"),
        ]),
        menu_edition(),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("articles.familles", "Familles", "commercial:familles", icone="bi-tags"),
            E("articles.liste", "Articles", "commercial:articles", icone="bi-box-seam"),
            E("structure.nomenclatures", "Nomenclatures"),
            E("structure.comptabilite", "Comptabilité", icone="bi-calculator", enfants=[
                E("structure.plan_comptable", "Plan comptable", "comptabilite:comptes"),
                E("structure.plan_analytique", "Plan analytique", "comptabilite:structure", "sections", icone="bi-diagram-2"),
                E("structure.taux_taxes", "Taux de taxes", enfants=[
                    E("structure.taux_taxes.tva_debit", "TVA/ débit - Vente de biens"),
                    E("structure.taux_taxes.tva_encaissement", "TVA/ encaissement - Prestation de services"),
                    E("structure.taux_taxes.tp_ht", "TP/ HT"),
                    E("structure.taux_taxes.tp_ttc", "TP/ TTC"),
                    E("structure.taux_taxes.tp_poids", "TP/ poids"),
                    E("structure.taux_taxes.surtaxe", "Surtaxe"),
                ]),
                E("structure.codes_journaux", "Codes journaux", "comptabilite:journaux"),
                E("structure.banques", "Banques", "comptabilite:structure", "banques", icone="bi-bank2"),
                E("structure.modele_reglement", "Modèle de règlement"),
                E("structure.modele_grille", "Modèle de grille"),
            ]),
            E("structure.codes_affaires", "Codes affaires"),
            SEP(),
            E("tiers.clients", "Clients", "commercial:clients", icone="bi-people"),
            E("tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs", icone="bi-truck"),
            E("structure.baremes", "Barèmes", icone="bi-percent", enfants=[
                E("structure.baremes.commissions", "Commissions représentants", "commercial:baremes", type="COMMISSION"),
                E("structure.baremes.rrr_clients", "Rabais, remises et ristournes clients", "commercial:baremes", type="REMISE", sens="CLIENT"),
                E("structure.baremes.rrr_fournisseurs", "Rabais, remises et ristournes fournisseurs", "commercial:baremes", type="REMISE", sens="FOURNISSEUR"),
                E("structure.baremes.promos_clients", "Soldes et promotions clients", "commercial:baremes", type="PROMOTION", sens="CLIENT"),
                E("structure.baremes.promos_fournisseurs", "Soldes et promotions fournisseurs", "commercial:baremes", type="PROMOTION", sens="FOURNISSEUR"),
            ]),
            E("structure.glossaires", "Glossaires"),
            E("structure.modeles_enregistrement", "Modèles enregistrement"),
            E("structure.ressources", "Ressources"),
            E("structure.centre_charges", "Centre de charges"),
            E("structure.collaborateurs", "Collaborateurs", icone="bi-person-badge"),
            E("structure.depots", "Dépôts de stockage", "commercial:depots", icone="bi-house-gear"),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("ventes.documents", "Documents des ventes", icone="bi-receipt", enfants=[
                E("ventes.tous", "Tous les documents des ventes", "commercial:documents", "ventes", preuve="AJOUT-ERP"),
                SEP(),
                *_documents("ventes", TYPES_VENTE),
            ]),
            E("achats.documents", "Documents des achats", icone="bi-cart", enfants=[
                E("achats.tous", "Tous les documents des achats", "commercial:documents", "achats", preuve="AJOUT-ERP"),
                SEP(),
                *_documents("achats", TYPES_ACHAT),
                SEP(),
                E("achats.acheteur", "Gestion acheteur entête et ligne de document"),
                E("achats.bon_a_payer", "Gestion du Bon à payer"),
            ]),
            E("stocks.documents", "Documents des stocks", icone="bi-boxes", enfants=[
                E("stocks.tous", "Tous les documents des stocks", "commercial:documents", "stocks", preuve="AJOUT-ERP"),
                SEP(),
                *_documents("stocks", TYPES_STOCK),
                E("stocks.depreciation", "Dépréciation de stock"),
                SEP(),
                E("stocks.preparation_fabrication", "Préparation de fabrication"),
                E("stocks.ordre_fabrication", "Ordre de fabrication"),
                E("stocks.bon_fabrication", "Bon de fabrication"),
            ]),
            E("traitement.documents_internes", "Documents internes"),
            E("traitement.services_connectes", "Services connectés", enfants=[
                E("traitement.services_connectes.societe", "Accéder à la société"),
                E("traitement.services_connectes.transmission", "Transmission des factures clients"),
                E("traitement.services_connectes.reception", "Réception des factures fournisseurs"),
            ]),
            E("traitement.efacture", "Facture électronique"),
            SEP(),
            E("traitement.affaires", "Gestion des affaires"),
            E("traitement.fabrications", "Gestion des fabrications"),
            E("traitement.livraisons", "Gestion des livraisons clients", "commercial:documents", "ventes", type="COMMANDE", statut="VALIDE"),
            E("traitement.receptions", "Gestion des réceptions fournisseurs", "commercial:documents", "achats", type="ACHAT_COMMANDE", statut="VALIDE"),
            E("traitement.controle_qualite", "Contrôle qualité"),
            E("traitement.par_lot", "Traitement par lot"),
            E("traitement.planning", "Gestion du planning des ressources"),
            E("traitement.bon_a_payer", "Gestion du bon à payer"),
            E("reglements", "Gestion des règlements", icone="bi-cash-coin", enfants=[
                E("reglements.clients", "Gestion des règlements clients", "commercial:reglement_create", sens="E"),
                E("reglements.fournisseurs", "Gestion des règlements fournisseurs", "commercial:reglement_create", sens="D"),
                E("reglements.caisse", "Opérations de caisse (dépenses, hors recettes)", "commercial:operations_caisse",
                  preuve="AJOUT-ERP"),
                E("reglements.generation", "Génération des règlements"),
                E("reglements.paiements_ligne", "Intégration des paiements en ligne"),
            ]),
            E("traitement.modeles_prestations", "Modèles et prestations types"),
            E("traitement.abonnements", "Abonnements"),
            E("traitement.contremarque", "Contremarque"),
            SEP(),
            E("fiche_stock", "Fiche de stock (magasin)", icone="bi-clipboard-check", preuve="AJOUT-ERP", enfants=[
                E("fiche_stock.pointage", "Pointage des bons", "commercial:pointage", preuve="AJOUT-ERP"),
                E("fiche_stock.pointages", "Pointages effectués", "commercial:pointages", preuve="AJOUT-ERP"),
                E("fiche_stock.rapprochement", "Rapprochement fiche / ordinateur", "commercial:fiche_rapprochement", preuve="AJOUT-ERP"),
            ]),
            E("comptes", "Gestion des comptes", icone="bi-person-lines-fill", enfants=[
                E("comptes.clients", "Gestion des clients", "commercial:clients", vue="comptes"),
                E("comptes.fournisseurs", "Gestion des fournisseurs", "commercial:fournisseurs", vue="comptes"),
                E("comptes.articles", "Gestion des articles", "commercial:stock", vue="comptes"),
                E("comptes.affaires", "Gestion des affaires"),
                E("comptes.collaborateurs", "Gestion des collaborateurs"),
                E("comptes.ressources", "Gestion des ressources"),
                E("comptes.tracabilite", "Suivi traçabilité série/ lot"),
            ]),
            E("traitement.besoins", "Gestion des besoins", "commercial:besoins", icone="bi-exclamation-triangle"),
            E("traitement.tracabilite_documents", "Traçabilité des documents"),
            E("recherche", "Recherche de documents", icone="bi-search", enfants=[
                E("recherche.entetes", "Entêtes de documents", "commercial:recherche_entetes"),
                E("recherche.lignes", "Lignes de documents", "commercial:recherche_lignes"),
            ]),
            E("traitement.inventaire", "Saisie d'inventaire", "commercial:inventaires", icone="bi-clipboard-check"),
            E("traitement.agenda", "Evénements agenda"),
            SEP(),
            E("maj_compta", "Mise à jour de la comptabilité", icone="bi-journal-arrow-up", enfants=[
                E("maj_compta.factures_ventes", "Factures de ventes (journal VT)", "comptabilite:ecritures", journal="VT"),
                E("maj_compta.factures_achats", "Factures d'achats (journal AC)", "comptabilite:ecritures", journal="AC"),
                E("maj_compta.reglements", "Règlements achats/ ventes", "comptabilite:journal"),
                E("maj_compta.variation_stock", "Variation de stock (inventaire permanent)", "commercial:stock", vue="variation", preuve="AJOUT-ERP"),
                E("maj_compta.engagements", "Engagements achats/ ventes"),
            ]),
            E("traitement.archivage", "Archivage"),
            E("traitement.cloture_periode", "Clôture période"),
            E("traitement.sauvegarde_fiscale", "Sauvegarde fiscale des données"),
        ]),
        Onglet("etat", "Etat", "bi-printer", [
            E("etats.personnalises", "Etats personnalisés"),
            E("etats.rapport_commercial", "Rapport commercial journalier", "commercial:rapport_commercial",
              icone="bi-cash-stack", preuve="AJOUT-ERP"),
            E("etats.reglements_modes", "Règlements par mode de paiement", "commercial:statistique", "reglements_modes",
              icone="bi-wallet2", preuve="AJOUT-ERP"),
            E("etats.fiche_stock", "Fiche de stock d'un article", "commercial:fiche_article", icone="bi-card-list", preuve="AJOUT-ERP"),
            SEP(),
            E("etats.analyse_clients", "Analyse clients", icone="bi-person-check", enfants=[
                E("etats.clients.activite", "Activité clients", "commercial:statistique", "activite_clients"),
                E("etats.clients.rentabilite", "Rentabilité clients", "commercial:statistique", "rentabilite_clients"),
                E("etats.clients.risque", "Risque clients", "commercial:statistique", "risque_clients"),
                E("etats.clients.avoirs", "Avoirs et retours clients", "commercial:statistique", "avoirs_retours",
                  preuve="AJOUT-ERP"),
            ]),
            E("etats.cadencier_clients", "Cadencier clients", "commercial:statistique", "cadencier_clients"),
            E("etats.remises_accordees", "Remises et promotions accordées", "commercial:statistique", "remises_accordees", preuve="AJOUT-ERP"),
            E("etats.statistiques_clients", "Statistiques clients", icone="bi-graph-up", enfants=[
                E("etats.clients.familles", "Statistiques par familles d'articles", "commercial:statistique", "ventes_familles"),
                E("etats.clients.articles", "Statistiques par articles", "commercial:statistique", "ventes_articles"),
                E("etats.clients.palmares", "Palmarès des clients", "commercial:statistique", "palmares_clients"),
            ]),
            E("etats.mouvement_clients", "Mouvements clients", "comptabilite:grand_livre", compte_debut="411", compte_fin="411"),
            SEP(),
            E("etats.analyse_fournisseurs", "Analyse fournisseurs", icone="bi-truck", enfants=[
                E("etats.fournisseurs.activite", "Activité fournisseurs", "commercial:statistique", "activite_fournisseurs"),
                E("etats.fournisseurs.ca", "Chiffre d'affaires fournisseurs", "commercial:statistique", "ca_fournisseurs"),
            ]),
            E("etats.cadencier_fournisseurs", "Cadencier fournisseurs", "commercial:statistique", "cadencier_fournisseurs"),
            E("etats.statistiques_fournisseurs", "Statistiques fournisseurs", icone="bi-graph-down", enfants=[
                E("etats.fournisseurs.familles", "Statistiques par familles d'articles", "commercial:statistique", "achats_familles"),
                E("etats.fournisseurs.articles", "Statistiques par articles", "commercial:statistique", "achats_articles"),
            ]),
            E("etats.mouvement_fournisseurs", "Mouvements fournisseurs", "comptabilite:grand_livre", compte_debut="401", compte_fin="401"),
            SEP(),
            E("etats.statistiques_articles", "Statistiques articles", icone="bi-box-seam", enfants=[
                E("etats.articles.articles", "Statistiques articles", "commercial:statistique", "articles"),
                E("etats.articles.familles", "Statistiques familles", "commercial:statistique", "familles"),
                E("etats.articles.palmares", "Palmarès des ventes", "commercial:statistique", "palmares_ventes"),
                E("etats.articles.rotation", "Rotation des stocks et ruptures", "commercial:statistique", "rotation_stocks",
                  preuve="AJOUT-ERP"),
            ]),
            E("etats.mouvements", "Mouvements de stock", "commercial:mouvements", icone="bi-arrow-left-right", vue="etat"),
            E("etats.inventaire", "Inventaire", icone="bi-clipboard-data", enfants=[
                E("etats.inventaire.preparatoire", "Etat préparatoire", "commercial:etat_inventaire", vue="preparatoire"),
                E("etats.inventaire.livre", "Livre d'inventaire", "commercial:etat_inventaire", vue="livre"),
            ]),
            E("etats.cadencier_livraison", "Cadencier de livraison", "commercial:statistique", "cadencier_livraison"),
            SEP(),
            E("etats.stats_collaborateurs", "Statistiques collaborateurs"),
            E("etats.stats_ressources", "Statistiques ressources"),
            E("etats.commissions", "Commissions représentants", "commercial:statistique", "commissions"),
            SEP(),
            E("etats.tableaux_bord", "Tableaux de bord", "reporting:dashboard", icone="bi-speedometer2"),
            E("etats.journaux_comptables", "Journaux comptables", "comptabilite:journal"),
            E("etats.libres", "Etats libres"),
            SEP(),
            E("etats.colisage", "Étiquettes de colisage"),
            E("etats.releves_factures", "Relevés de factures", icone="bi-receipt", enfants=[
                E("etats.releves_factures.clients", "Clients", "commercial:statistique", "releve_factures_clients"),
                E("etats.releves_factures.fournisseurs", "Fournisseurs", "commercial:statistique", "releve_factures_fournisseurs"),
            ]),
            E("etats.listes_documents", "Listes des documents", icone="bi-list-ul", enfants=[
                E("etats.listes_documents.ventes", "Documents de vente", "commercial:statistique", "liste_documents_ventes"),
                E("etats.listes_documents.achats", "Documents d'achat", "commercial:statistique", "liste_documents_achats"),
            ]),
            E("etats.releves_echeances", "Relevés d'échéances", icone="bi-hourglass-split", enfants=[
                E("etats.echeances.clients", "Clients", "commercial:statistique", "echeances_clients"),
                E("etats.echeances.fournisseurs", "Fournisseurs", "commercial:statistique", "echeances_fournisseurs"),
            ]),
            E("etats.etiquettes", "Étiquettes et mailing", enfants=[
                E("etats.etiquettes.clients", "Clients"),
                E("etats.etiquettes.fournisseurs", "Fournisseurs"),
                E("etats.etiquettes.articles", "Étiquettes articles"),
            ]),
            E("etats.listes", "Listes", icone="bi-card-list", enfants=[
                E("etats.listes.clients", "Liste des clients", "commercial:statistique", "liste_clients"),
                E("etats.listes.fournisseurs", "Liste des fournisseurs", "commercial:statistique", "liste_fournisseurs"),
                E("etats.listes.articles", "Liste des articles", "commercial:statistique", "liste_articles"),
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
    titre="Comptabilité générale",
    description="Plan SYSCOHADA, saisie, journaux, grand livre, balance, états financiers",
    icone="bi-calculator",
    couleur="#2e7d32",
    prefixe="/comptabilite/",
    accueil="comptabilite:accueil",
    onglets=[
        menu_fichier_comptabilite(),
        menu_edition(),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("structure.plan", "Plan comptable", "comptabilite:comptes", icone="bi-list-ol"),
            E("structure.plan_tiers", "Plan tiers", icone="bi-people", enfants=[
                E("structure.plan_tiers.clients", "Clients", "commercial:clients", edition="commerce"),
                E("structure.plan_tiers.partenaires", "Partenaires (propriétaires de véhicules)", "partenaires:proprietaires",
                  preuve="AJOUT-ERP", edition="transport"),
                E("structure.plan_tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs"),
                E("structure.plan_tiers.personnel", "Personnel (salariés)", "personnel:employes", preuve="AJOUT-ERP",
                  edition="transport"),
            ]),
            E("structure.plan_analytique", "Plan analytique", "comptabilite:structure", "sections", icone="bi-diagram-2",
              edition="commerce"),
            E("structure.plan_analytique_transport", "Plan analytique du transport (11 axes)", "analytique:plan",
              icone="bi-diagram-3", preuve="AJOUT-ERP", edition="transport"),
            E("structure.plan_reporting", "Plan reporting"),
            SEP(),
            E("structure.taux_taxes", "Taux de taxes", "comptabilite:structure", "taxes", icone="bi-percent"),
            E("structure.journaux", "Codes journaux", "comptabilite:journaux", icone="bi-collection"),
            E("structure.journaux_analytiques", "Codes journaux analytiques"),
            E("structure.postes_budgetaires", "Postes budgétaires"),
            E("structure.devises", "Devises", preuve="INDICATIF"),
            SEP(),
            E("structure.banques", "Banques", "comptabilite:structure", "banques", icone="bi-bank2"),
            # « Structure > Modèles > Modèles de saisie » : fiche Sage (version non précisée, skill sage100-menus-droits-v12, S10)
            E("structure.modeles", "Modèles", icone="bi-files", enfants=[
                E("structure.modeles_saisie", "Modèles de saisie"),
                E("structure.modeles_grille", "Modèles de grille"),
                E("structure.modeles_reglement", "Modèles de règlement"),
            ]),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("traitement.saisie_journaux", "Saisie des journaux", icone="bi-journal-text", enfants=[
                E("traitement.saisie_journaux.tous", "Tous les journaux", "comptabilite:ecritures"),
                SEP(),
            ], dyn=_journaux("comptabilite:ecritures", "traitement.saisie_journaux")),
            E("traitement.saisie_piece", "Saisie par pièce", "comptabilite:ecriture_create", icone="bi-pencil-square"),
            E("traitement.saisie_bancaire", "Saisie des opérations bancaires"),
            E("traitement.saisie_lot", "Saisie par lot", preuve="INDICATIF"),
            E("traitement.saisie_analytique", "Saisie des écritures analytiques", "comptabilite:ventilation", icone="bi-diagram-2"),
            E("traitement.brouillard", "Écritures au brouillard", "comptabilite:ecritures", icone="bi-hourglass", statut="BROUILLARD"),
            SEP(),
            E("traitement.lettrage", "Interrogation et lettrage", "comptabilite:lettrage", icone="bi-link-45deg"),
            E("traitement.lettrage_auto", "Lettrage automatique", "comptabilite:lettrage_auto", icone="bi-magic"),
            E("traitement.recherche", "Recherche d'écritures", "comptabilite:ecritures", icone="bi-search", vue="recherche"),
            E("traitement.rapprochement", "Rapprochement bancaire manuel", "comptabilite:rapprochement", icone="bi-check2-square"),
            E("traitement.rapprochement_auto", "Rapprochement bancaire automatique", preuve="INDICATIF"),
            E("traitement.extraits", "Gestion des extraits", preuve="INDICATIF"),
            E("traitement.reglement_tiers", "Règlement tiers", "commercial:reglement_create"),
            E("traitement.relance", "Rappel / relance clients", "comptabilite:balance_agee", type="CLIENT", vue="relance"),
            SEP(),
            E("traitement.tva", "Déclaration de taxes", "comptabilite:tva", icone="bi-percent"),
            E("traitement.revision", "Révision par cycle"),
            # Fiche Sage « Gérer les bons à payer » (version 7.50, S07) : à confirmer en V12 ; droits BAP non codés (BAP-01)
            E("traitement.bon_a_payer", "Gestion du bon à payer", icone="bi-check2-circle", enfants=[
                E("traitement.bon_a_payer.acheteurs", "Affectation Bon à payer acheteurs"),
                E("traitement.bon_a_payer.financiers", "Affectation Bon à payer responsables financiers"),
                E("traitement.bon_a_payer.transmission", "Transmission des autorisations de bon à payer (E-Facture)"),
            ]),
            E("traitement.abonnements", "Abonnements", preuve="INDICATIF"),
            SEP(),
            E("traitement.fin_exercice", "Fin d'exercice", icone="bi-calendar-check", enfants=[
                E("traitement.fin_exercice.nouvel", "Nouvel exercice", "comptabilite:exercice_create"),
                E("traitement.fin_exercice.cloture", "Clôture de l'exercice et reports à nouveau", "comptabilite:cloture_exercice"),
                E("traitement.fin_exercice.journaux", "Clôture des journaux", "comptabilite:cloture_journaux"),
                E("traitement.fin_exercice.archivage", "Archivage", preuve="INDICATIF"),
            ]),
        ]),
        # Menu Etat de Sage 100 Comptabilité. Jusqu'au groupe « Etats tiers » : découpage fonctionnel officiel
        # Comptabilité, PDF p. 8 (skill sage100-menus-droits-v12, source S02) ; rangs et séparateurs non relevés.
        Onglet("etat", "Etat", "bi-printer", [
            E("etats.brouillard", "Brouillard", "comptabilite:journal", icone="bi-hourglass", statut="BROUILLARD",
              preuve="DOC-V12"),
            E("etats.journaux", "Journal", icone="bi-journals", preuve="DOC-V12", enfants=[
                E("etats.journal.liste", "Journal", dyn=_journaux("comptabilite:journal", "etats.journal"), preuve="DOC-V12"),
                E("etats.journal_centralise", "Journal centralisé", preuve="DOC-V12"),
                E("etats.journal_general", "Journal général", "comptabilite:journal", preuve="DOC-V12"),
            ]),
            E("etats.gl.general", "Grand-livre des comptes", "comptabilite:grand_livre", icone="bi-book", preuve="DOC-V12"),
            E("etats.balance.generale", "Balance des comptes", "comptabilite:balance", icone="bi-table", preuve="DOC-V12"),
            E("etats.echeancier", "Echéancier", "comptabilite:balance_agee", icone="bi-calendar3", type="CLIENT",
              vue="echeancier", preuve="DOC-V12"),
            E("etats.balance.agee", "Balance âgée", "comptabilite:balance_agee", icone="bi-hourglass-split", type="CLIENT",
              preuve="DOC-V12"),
            E("etats.tiers", "Etats tiers", icone="bi-people", preuve="DOC-V12", enfants=[
                E("etats.gl.tiers", "Grand-livre des tiers", "comptabilite:grand_livre", compte_debut="4", compte_fin="4",
                  preuve="DOC-V12"),
                E("etats.balance.tiers", "Balance des tiers", "comptabilite:balance", compte_debut="4", compte_fin="4",
                  preuve="DOC-V12"),
                E("etats.tiers.justificatif", "Justificatif de solde à date", "comptabilite:justificatif_solde", type="CLIENT",
                  preuve="DOC-V12"),
                E("etats.tiers.delais", "Rapport des délais de paiement", preuve="DOC-V12"),
                E("etats.tiers.statistiques", "Statistiques tiers", "comptabilite:statistiques_tiers", type="CLIENT",
                  preuve="DOC-V12"),
                E("etats.tiers.rappels", "Historique des rappels", preuve="DOC-V12"),
            ]),
            SEP(),
            E("etats.analytique", "Sections analytiques (contrôle)", icone="bi-diagram-2", preuve="ERG-CLASSIQUE", enfants=[
                E("etats.analytique.journal", "Journal analytique", preuve="ERG-CLASSIQUE"),
                E("etats.analytique.grand_livre", "Grand-livre analytique", preuve="ERG-CLASSIQUE"),
                E("etats.analytique.balance", "Balance analytique", "comptabilite:balance_analytique", preuve="ERG-CLASSIQUE"),
            ]),
            SEP(),
            E("etats.analytique_module", "Comptabilité analytique (Véhicules, Propriétaires)", "analytique:accueil",
              icone="bi-diagram-3", preuve="AJOUT-ERP"),
            SEP(),
            E("etats.budgetaires", "Etats budgétaires", icone="bi-bullseye", preuve="INDICATIF"),
            E("etats.tresorerie_projetee", "Trésorerie projetée", "comptabilite:tresorerie_projetee", icone="bi-graph-up-arrow",
              preuve="AJOUT-ERP"),
            SEP(),
            E("etats.financiers", "Bilan / Compte de résultat", icone="bi-bank", preuve="ERG-CLASSIQUE", enfants=[
                E("etats.financiers.bilan", "Bilan", "comptabilite:bilan", preuve="ERG-CLASSIQUE"),
                E("etats.financiers.resultat", "Compte de résultat", "comptabilite:compte_resultat", preuve="ERG-CLASSIQUE"),
                E("etats.financiers.sig", "Soldes intermédiaires de gestion", "comptabilite:compte_resultat", vue="sig",
                  preuve="ERG-CLASSIQUE"),
            ]),
            E("etats.declarations", "Déclarations", icone="bi-file-earmark-text", preuve="AJOUT-ERP", enfants=[
                E("etats.fiscal.tva", "Déclaration de TVA", "comptabilite:tva", vue="etat", preuve="AJOUT-ERP"),
                E("etats.dsf", "Déclaration statistique et fiscale (DSF)", preuve="AJOUT-ERP"),
            ]),
            E("etats.controles", "Analyse et contrôles", icone="bi-clipboard-check", preuve="INDICATIF", enfants=[
                E("etats.controles.cloture", "Contrôles de clôture", "comptabilite:controles_cloture", preuve="AJOUT-ERP"),
                E("etats.controles.liaison", "Contrôle de la liaison commerciale", "comptabilite:controle_liaison",
                  preuve="AJOUT-ERP"),
            ]),
        ]),
        menu_fenetre("comptabilite"),
        menu_aide("comptabilite"),
    ],
)

# ---------------------------------------------------------------------------
# Comptabilité analytique : logiciel distinct à l'écran, mais une seule comptabilité. Chaque montant analytique est
# lu sur une ligne d'écriture générale validée (véhicule, section) ; rien n'est saisi deux fois.
# ---------------------------------------------------------------------------
def _axes_analytiques():
    """Une entrée par axe du plan analytique du dossier (gares, véhicules… et plans de sections)."""
    from apps.comptabilite.plan_analytique import axes

    return [E(f"analytique.axes.{code}", titre, "analytique:axe", code, preuve="AJOUT-ERP") for code, titre, _ in axes()]


ANALYTIQUE = Module(
    code="analytique",
    titre="Comptabilité analytique",
    description="Véhicules, propriétaires et sections, issus des écritures de la comptabilité générale",
    icone="bi-diagram-3",
    couleur="#00695c",
    prefixe="/comptabilite/analytique/",
    accueil="analytique:accueil",
    onglets=[
        menu_fichier("analytique", "commercial:societe"),
        menu_edition(),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("structure.plan_transport", "Plan analytique du transport", icone="bi-diagram-3",
              preuve="AJOUT-ERP", edition="transport", enfants=[
                E("structure.plan_transport.tous", "Les 11 axes et leurs éléments", "analytique:plan", preuve="AJOUT-ERP",
                  vue="structure"),
                E("structure.plan_transport.agences", "Agences et points de vente", "transport:fiches", "gares", preuve="AJOUT-ERP"),
                E("structure.vehicules", "Véhicules", "transport:vehicules", icone="bi-bus-front", preuve="AJOUT-ERP"),
                E("structure.plan_transport.proprietaires", "Propriétaires (partenaires)", "partenaires:proprietaires",
                  preuve="AJOUT-ERP"),
                E("structure.contrats", "Contrats des propriétaires", "partenaires:contrats", icone="bi-file-earmark-text",
                  preuve="AJOUT-ERP"),
                E("structure.plan_transport.lignes", "Lignes (itinéraires) et tarifs", "transport:fiches", "lignes", preuve="AJOUT-ERP"),
                E("structure.plan_transport.services", "Services", "analytique:axe", "services", preuve="AJOUT-ERP", vue="structure"),
                E("structure.plan_transport.activites", "Activités", "analytique:axe", "activites", preuve="AJOUT-ERP", vue="structure"),
                E("structure.plan_transport.gammes", "Gammes (Classique / VIP)", "analytique:axe", "gammes", preuve="AJOUT-ERP", vue="structure"),
                E("structure.plan_transport.villes", "Villes", "analytique:axe", "villes", preuve="AJOUT-ERP", vue="structure"),
                E("structure.plan_transport.voyages", "Voyages (départs)", "transport:departs", preuve="AJOUT-ERP"),
            ]),
            E("structure.sections", "Plan analytique (sections)", "analytique:sections", icone="bi-diagram-2", preuve="AJOUT-ERP",
              edition="commerce"),
            E("structure.sections_libres", "Autres plans (sections libres)", "analytique:sections", icone="bi-diagram-2",
              preuve="AJOUT-ERP", edition="transport"),
            E("structure.budgets", "Budgets", "analytique:budgets", icone="bi-calculator", preuve="AJOUT-ERP"),
        ]),
        Onglet("traitement", "Traitement", "bi-gear-wide-connected", [
            E("traitement.ventilation", "Affecter une section aux écritures", "comptabilite:ventilation", icone="bi-diagram-2",
              preuve="AJOUT-ERP"),
        ]),
        Onglet("etat", "Etat", "bi-printer", [
            E("analytique.plan", "Plan analytique (tous les axes)", "analytique:plan", icone="bi-diagram-3", preuve="AJOUT-ERP"),
            E("analytique.budget_reel", "Budget / réel", "analytique:budgets", icone="bi-calculator", preuve="AJOUT-ERP", vue="reel"),
            E("analytique.axes", "États par axe", icone="bi-list-nested", preuve="AJOUT-ERP", dyn=_axes_analytiques),
            SEP(),
            E("analytique.vehicules", "Comptabilité analytique : Véhicules", icone="bi-bus-front", preuve="AJOUT-ERP",
              edition="transport", enfants=[
                E("analytique.vehicules.comptes", "Comptes d'exploitation des véhicules", "comptabilite:analytique_vehicules",
                  preuve="AJOUT-ERP"),
                E("analytique.vehicules.grand_livre", "Grand-livre des véhicules", "comptabilite:grand_livre_vehicules",
                  preuve="AJOUT-ERP"),
                E("analytique.vehicules.balance", "Balance des véhicules", "comptabilite:balance_vehicules", preuve="AJOUT-ERP"),
            ]),
            E("analytique.proprietaires", "Comptabilité analytique : Propriétaires", icone="bi-people", preuve="AJOUT-ERP",
              edition="transport", enfants=[
                E("analytique.proprietaires.portefeuilles", "Portefeuilles et résultats", "comptabilite:analytique_proprietaires",
                  preuve="AJOUT-ERP"),
                E("analytique.proprietaires.releves", "Relevés et règlements", "comptabilite:analytique_releves",
                  preuve="AJOUT-ERP"),
            ]),
            SEP(),
            E("analytique.sections", "Sections analytiques", icone="bi-diagram-2", preuve="AJOUT-ERP", enfants=[
                E("analytique.sections.balance", "Balance analytique", "comptabilite:balance_analytique", preuve="AJOUT-ERP"),
            ]),
        ]),
        menu_fenetre("analytique"),
        menu_aide("analytique"),
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
        menu_edition(),
        Onglet("etat", "Etat", "bi-printer", [
            E("synthese.catalogue", "Catalogue de tous les états", "reporting:catalogue", icone="bi-collection", preuve="AJOUT-ERP"),
            E("synthese.dashboard", "Tableau de bord", "reporting:dashboard", icone="bi-speedometer2", edition="commerce"),
            E("transport.tableau_de_bord", "Tableau de bord du transport", "reporting:transport_tableau_de_bord",
              icone="bi-speedometer2", preuve="AJOUT-ERP", edition="transport"),
            E("analyses.evolution", "Évolution de la société (mois par mois)", "reporting:evolution", icone="bi-graph-up-arrow",
              preuve="AJOUT-ERP"),
            E("analyses.axes", "Analyses par axe analytique", icone="bi-diagram-3", preuve="AJOUT-ERP", enfants=[
                E("analyses.comparaison", "Comparaison de deux périodes", "reporting:comparaison", preuve="AJOUT-ERP"),
                E("analyses.matrice", "Tableau mensuel par élément", "reporting:matrice", preuve="AJOUT-ERP"),
                E("analyses.classement", "Classements (meilleurs, moins bons)", "reporting:classement", preuve="AJOUT-ERP"),
                E("analytique.plan", "Plan analytique et états détaillés", "analytique:plan", preuve="AJOUT-ERP"),
            ]),
            E("synthese.rapport_commercial", "Rapport commercial journalier", "reporting:rapport_commercial", icone="bi-cash-stack",
              edition="commerce"),
            SEP(),
            E("transport.recettes", "Recettes et caisses", icone="bi-cash-coin", preuve="AJOUT-ERP", edition="transport", enfants=[
                E("transport.recettes.journalier", "Rapport journalier d'agence", "transport:rapport_journalier", preuve="AJOUT-ERP"),
                E("transport.recettes.jour", "Recette du jour par agence", "transport:recette", preuve="AJOUT-ERP"),
                E("transport.recettes.billetterie", "Billetterie par point de vente", "reporting:transport_billetterie",
                  preuve="AJOUT-ERP"),
                E("transport.recettes.colis", "Colis, courrier et fret", "reporting:transport_colis", preuve="AJOUT-ERP"),
                E("transport.recettes.colis_non_livres", "Colis arrivés non livrés", "reporting:transport_colis_non_livres", preuve="AJOUT-ERP"),
                E("transport.recettes.sessions", "Sessions de caisse", "transport:sessions_caisse", preuve="AJOUT-ERP"),
                E("transport.recettes.transferts", "Transferts entre caisses", "transport:transferts", preuve="AJOUT-ERP"),
            ]),
            E("transport.rentabilite", "Rentabilité", icone="bi-graph-up-arrow", preuve="AJOUT-ERP", edition="transport", enfants=[
                E("transport.rentabilite.vehicules", "Par véhicule", "transport:rentabilite", preuve="AJOUT-ERP"),
                E("transport.rentabilite.comptes", "Comptes d'exploitation des véhicules", "comptabilite:analytique_vehicules",
                  preuve="AJOUT-ERP"),
                E("transport.rentabilite.balance", "Balance des véhicules", "transport:balance_vehicules", preuve="AJOUT-ERP"),
                E("transport.rentabilite.grand_livre", "Grand-livre des véhicules", "transport:grand_livre_vehicules",
                  preuve="AJOUT-ERP"),
                E("transport.rentabilite.lignes", "Par ligne", "analytique:axe", "lignes", preuve="AJOUT-ERP"),
                E("transport.rentabilite.agences", "Par agence", "analytique:axe", "agences", preuve="AJOUT-ERP"),
                E("transport.rentabilite.services", "Par service", "analytique:axe", "services", preuve="AJOUT-ERP"),
                E("transport.rentabilite.gammes", "Classique / VIP", "analytique:axe", "gammes", preuve="AJOUT-ERP"),
            ]),
            E("transport.flotte", "Flotte et garage", icone="bi-tools", preuve="AJOUT-ERP", edition="transport", enfants=[
                E("transport.flotte.consommation", "Consommation de carburant", "garage:consommation", preuve="AJOUT-ERP"),
                E("transport.flotte.reparations", "Réparations", "garage:reparations", preuve="AJOUT-ERP"),
                E("transport.flotte.echeances", "Échéances des véhicules (papiers, entretien)", "garage:echeances",
                  preuve="AJOUT-ERP"),
                E("transport.flotte.magasin", "Stock du magasin", "garage:magasin_stock", preuve="AJOUT-ERP"),
            ]),
            E("transport.proprietaires", "Propriétaires", icone="bi-people", preuve="AJOUT-ERP", edition="transport", enfants=[
                E("transport.proprietaires.liste", "Partenaires et soldes", "partenaires:proprietaires", preuve="AJOUT-ERP"),
                E("transport.proprietaires.portefeuilles", "Portefeuilles et résultats", "comptabilite:analytique_proprietaires",
                  preuve="AJOUT-ERP"),
                E("transport.proprietaires.decomptes", "Décomptes", "partenaires:decomptes", preuve="AJOUT-ERP"),
                E("transport.proprietaires.releves", "Relevés", "partenaires:releves", preuve="AJOUT-ERP"),
            ]),
            E("ventes.analyses", "Statistiques des ventes", icone="bi-graph-up", edition="commerce", enfants=[
                E("ventes.mois", "Évolution mensuelle", "reporting:ventes", vue="mois"),
                E("ventes.clients", "Par client", "reporting:ventes", vue="clients"),
                E("ventes.articles", "Par article", "reporting:ventes", vue="articles"),
            ]),
            E("transport.comparaisons", "Comparaisons de deux périodes", icone="bi-bar-chart-steps", edition="transport", enfants=[
                E("transport.comparaisons.agence", "Par agence", "reporting:comparaisons_transport", axe="agence"),
                E("transport.comparaisons.gamme", "Classique / VIP", "reporting:comparaisons_transport", axe="gamme"),
                E("transport.comparaisons.ligne", "Par ligne", "reporting:comparaisons_transport", axe="ligne"),
                E("transport.comparaisons.vehicule", "Par véhicule", "reporting:comparaisons_transport", axe="vehicule"),
                E("transport.comparaisons.proprietaire", "Par propriétaire", "reporting:comparaisons_transport",
                  axe="proprietaire"),
            ]),
            E("tiers.echeances", "Échéanciers", icone="bi-hourglass-split", enfants=[
                E("tiers.balance_agee_clients", "Clients", "reporting:balance_agee", type="CLIENT", edition="commerce"),
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

# Transport interurbain de voyageurs (version 2) : propre à l'ERP, sur le modèle des menus Sage
def _module_service(code, titre, description, icone, couleur, prefixe, structure, traitement, etat, accueil=None):
    """Logiciel d'un service (billetterie, colis, garage, personnel) : même barre de menus que les autres."""
    return Module(code=code, titre=titre, description=description, icone=icone, couleur=couleur, prefixe=prefixe,
                  accueil=accueil or f"{code}:accueil", onglets=[
                      menu_fichier(code, "commercial:societe"), menu_edition(),
                      *([Onglet("structure", "Structure", "bi-diagram-3", structure)] if structure else []),
                      Onglet("traitement", "Traitement", "bi-gear", traitement),
                      Onglet("etat", "Etat", "bi-printer", etat),
                      menu_fenetre(code), menu_aide(code)])


# Transport interurbain : un logiciel par service ; chacun travaille dans le sien, selon ses droits. Tout se regroupe
# automatiquement dans la comptabilité, sur chaque véhicule, et dans le rapport journalier de la Direction.
BILLETTERIE = _module_service(
    "billetterie", "Billetterie", "Départs, vente des billets, correspondances, annulations, encaissements du guichet",
    "bi-ticket-perforated", "#e65100", "/transport/billetterie/",
    structure=[E("structure.clients", "Clients en compte", "commercial:clients", icone="bi-people")],
    traitement=[
        E("billetterie.departs", "Départs du jour", "transport:departs", icone="bi-bus-front"),
        E("billetterie.programmer", "Programmer un départ", "transport:depart_create", icone="bi-calendar-plus"),
        E("billetterie.vendre", "Vendre un billet", "transport:billet_vente", icone="bi-ticket-perforated"),
        E("billetterie.billets", "Billets vendus (annulation, report)", "transport:billets", icone="bi-list-ul"),
        E("billetterie.remboursements", "Remboursements à payer", "transport:billets", icone="bi-arrow-counterclockwise",
          remboursement="AUTORISE"),
        SEP(),
        E("billetterie.ma_caisse", "Ma caisse (ouverture, fermeture)", "transport:ma_caisse_billetterie", icone="bi-safe"),
        E("billetterie.caisse", "Opérations de caisse", "commercial:operations_caisse", icone="bi-cash-coin"),
        E("billetterie.cloture", "Clôturer la journée de la billetterie", "transport:cloture_billetterie", icone="bi-lock"),
    ],
    etat=[E("billetterie.recette", "Recette de la billetterie", "transport:recette_billetterie", icone="bi-cash-stack")])

COLIS = _module_service(
    "colis", "Colis et expéditions", "Enregistrement, chargement, arrivée, remise, contre-remboursements",
    "bi-box-seam", "#6d4c41", "/transport/colis/", structure=None,
    traitement=[
        E("colis.enregistrer", "Enregistrer un colis", "transport:colis_create", icone="bi-box-seam", nature="COLIS"),
        E("colis.courrier", "Enregistrer un courrier", "transport:colis_create", icone="bi-envelope", nature="COURRIER"),
        E("colis.fret", "Enregistrer du fret", "transport:colis_create", icone="bi-truck", nature="FRET"),
        SEP(),
        E("colis.a_charger", "Envois à charger", "transport:colis", icone="bi-box-arrow-up", statut="ENREGISTRE"),
        E("colis.a_remettre", "Envois arrivés à remettre", "transport:colis", icone="bi-box-arrow-in-down", statut="ARRIVE"),
        E("colis.reverser", "Contre-remboursements à reverser", "transport:colis", icone="bi-arrow-return-left", statut="LIVRE"),
        E("colis.liste", "Suivi des envois", "transport:colis", icone="bi-search"),
        SEP(),
        E("colis.ma_caisse", "Ma caisse (ouverture, fermeture)", "transport:ma_caisse_colis", icone="bi-safe"),
        E("colis.cloture", "Clôturer la journée des colis", "transport:cloture_colis", icone="bi-lock"),
    ],
    etat=[E("colis.recette", "Recette des colis", "transport:recette_colis", icone="bi-cash-stack")])

GARAGE = _module_service(
    "garage", "Garage", "Véhicules, carburant, réparations, pièces, échéances des papiers",
    "bi-wrench-adjustable", "#455a64", "/transport/garage/",
    structure=[E("garage.vehicules", "Véhicules", "transport:vehicules", icone="bi-bus-front"),
               E("garage.chauffeurs", "Chauffeurs", "transport:fiches", "chauffeurs", icone="bi-person-badge")],
    traitement=[
        E("garage.plein", "Saisir un plein de carburant", "garage:plein_create", icone="bi-fuel-pump"),
        E("garage.pleins", "Pleins de carburant", "garage:pleins", icone="bi-list-ul"),
        SEP(),
        E("garage.entree", "Entrée d'un véhicule au garage", "garage:reparation_create", icone="bi-wrench"),
        E("garage.reparations", "Réparations en cours", "garage:reparations", icone="bi-tools"),
        SEP(),
        E("garage.magasin_achat", "Achat de pièces, fournitures, matériel", "garage:magasin_achat", icone="bi-cart-plus"),
        E("garage.magasin_achats", "Achats du magasin", "garage:magasin_achats", icone="bi-receipt-cutoff"),
        E("garage.magasin_sorties", "Sorties du magasin (utilisation)", "garage:magasin_sorties", icone="bi-box-arrow-right"),
        E("garage.magasin_stock", "Stock du magasin", "garage:magasin_stock", icone="bi-boxes"),
        E("garage.depense", "Autre dépense de véhicule", "transport:depense_create", icone="bi-receipt"),
        E("garage.depenses", "Autres dépenses", "transport:depenses", icone="bi-list-ul"),
        SEP(),
        E("garage.cloture", "Clôturer la journée du garage", "transport:cloture_garage", icone="bi-lock"),
    ],
    etat=[E("garage.consommation", "Carburant et consommation par véhicule", "garage:consommation", icone="bi-speedometer"),
          E("garage.echeances", "Papiers des véhicules (assurance, visite)", "garage:echeances", icone="bi-calendar-event"),
          E("garage.balance", "Coûts des véhicules", "transport:balance_vehicules", icone="bi-bus-front")])

PERSONNEL = _module_service(
    "personnel", "Personnel et paie", "Employés par service, avances, paie du mois, bulletins",
    "bi-people", "#5e35b1", "/personnel/",
    structure=[E("personnel.employes", "Employés", "personnel:employes", icone="bi-person-vcard"),
               E("personnel.rubriques", "Rubriques de paie", "personnel:rubriques", icone="bi-list-check")],
    traitement=[E("personnel.avance", "Verser une avance", "personnel:avance_create", icone="bi-cash"),
                E("personnel.avances", "Avances sur salaire", "personnel:avances", icone="bi-list-ul"),
                E("personnel.paie", "Paie du mois", "personnel:paies", icone="bi-wallet2")],
    etat=[E("personnel.livre", "Livre de paie", "personnel:paies", icone="bi-journal-text", vue="livre")])

TRANSPORT = Module(
    code="transport",
    titre="Direction de l'agence",
    description="Rapport journalier de toute l'agence, comptes des véhicules, rentabilité, lignes et tarifs, échanges",
    icone="bi-building-gear",
    couleur="#bf360c",
    prefixe="/transport/",
    accueil="transport:accueil",
    onglets=[
        menu_fichier("transport", "commercial:societe"),
        menu_edition(),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("structure.gares", "Gares", "transport:fiches", "gares", icone="bi-geo-alt"),
            E("structure.lignes", "Lignes et tarifs", "transport:fiches", "lignes", icone="bi-signpost-split"),
            E("structure.vehicules", "Véhicules", "transport:vehicules", icone="bi-bus-front"),
            E("structure.chauffeurs", "Chauffeurs", "transport:fiches", "chauffeurs", icone="bi-person-badge"),
            SEP(),
            E("structure.clients", "Clients en compte", "commercial:clients", icone="bi-people"),
            E("structure.parametres", "Paramètres transport (comptes et taxes)", "transport:parametres", icone="bi-sliders"),
        ]),
        Onglet("traitement", "Traitement", "bi-gear", [
            E("traitement.departs", "Départs du jour", "transport:departs", icone="bi-bus-front"),
            E("traitement.voyages", "Voyages à clôturer, avances de mission", "transport:voyages_a_cloturer", icone="bi-flag"),
            E("traitement.sessions", "Contrôle des caisses des guichets", "transport:sessions_caisse", icone="bi-safe"),
            E("traitement.transferts", "Transferts de fonds (banque, siège)", "transport:transferts", icone="bi-arrow-left-right"),
            E("traitement.depenses_fonctionnement", "Dépenses de fonctionnement (autorisation du siège)",
              "transport:depenses_fonctionnement", icone="bi-receipt-cutoff"),
            E("traitement.cloture", "Clôture de la journée", "transport:cloture", icone="bi-lock"),
            SEP(),
            E("traitement.partenaires", "Véhicules des partenaires", icone="bi-people", enfants=[
                E("traitement.partenaires.contrats", "Contrats (commission, location)", "partenaires:contrats"),
                E("traitement.partenaires.decomptes", "Décomptes de période", "partenaires:decomptes"),
                E("traitement.partenaires.releves", "Relevés et règlements", "partenaires:releves"),
            ]),
            SEP(),
            E("traitement.caisse", "Opérations de caisse", "commercial:operations_caisse", icone="bi-cash-coin"),
            E("traitement.reglement", "Règlement d'un client en compte", "commercial:reglement_create", icone="bi-wallet2"),
        ]),
        Onglet("etat", "Etat", "bi-printer", [
            E("etat.rapport", "Rapport journalier de l'agence", "transport:rapport_journalier", icone="bi-clipboard-data"),
            E("etat.rapport_a4", "Rapport journalier à imprimer (A4)", "transport:rapport_journalier_imprimer", icone="bi-printer"),
            E("etat.recette", "Recette journalière par gare", "transport:recette", icone="bi-cash-stack"),
            E("etat.vehicules", "Comptes des véhicules", icone="bi-bus-front", enfants=[
                E("etat.vehicules.balance", "Balance des véhicules", "transport:balance_vehicules"),
                E("etat.vehicules.grand_livre", "Grand-livre des véhicules", "transport:grand_livre_vehicules"),
                E("etat.vehicules.carburant", "Carburant et consommation", "garage:consommation"),
            ]),
            E("etat.rentabilite", "Rentabilité", icone="bi-graph-up", enfants=[
                E("etat.rentabilite.ligne", "Par ligne", "transport:rentabilite", axe="ligne"),
                E("etat.rentabilite.depart", "Par départ", "transport:rentabilite", axe="depart"),
            ]),
            SEP(),
            E("etat.balance", "Balance générale", "comptabilite:balance", icone="bi-journal-text"),
        ]),
        menu_fenetre("transport"),
        menu_aide("transport"),
    ],
)

# Ordre : les préfixes les plus précis d'abord (/transport/billetterie/ avant /transport/)
MODULES = [GESTION_COMMERCIALE, ANALYTIQUE, COMPTABILITE, REPORTING, BILLETTERIE, COLIS, GARAGE, TRANSPORT, PERSONNEL]
SERVICES_TRANSPORT = {"transport", "billetterie", "colis", "garage"}
MODULES_PAR_CODE = {m.code: m for m in MODULES}


def modules_proposes(societe):
    """Logiciels proposés selon l'activité de la société (ceux du métier en premier)."""
    ordre = ["transport", "billetterie", "colis", "garage", "personnel", "commercial", "comptabilite", "analytique", "reporting"]
    if societe.activite == societe.ACTIVITE_COMMERCE:
        return [m for m in MODULES if m.code not in SERVICES_TRANSPORT]
    modules = sorted(MODULES, key=lambda m: ordre.index(m.code))
    if societe.activite == societe.ACTIVITE_TRANSPORT:
        return [m for m in modules if m.code != "commercial"]
    return modules


# ---------------------------------------------------------------------------
# Résolution de l'élément actif
# ---------------------------------------------------------------------------
# Barre verticale de Sage 100 V12 : raccourcis par domaine, en accordéon (un domaine ouvert, les autres empilés en
# bas). Gestion des ventes relevée sur une Gestion commerciale Premium V12 ; les autres domaines sont construits sur
# le même modèle (Gestion des fabrications, des affaires et Sage eFacture n'existent pas dans l'ERP).
# (titre, nom d'URL ou "", arguments, paramètres)
BARRE_VERTICALE = {
    "commercial": [
        ("Gestion des ventes", [
            ("Liste des clients", "commercial:clients", (), {}),
            ("Liste des documents de vente", "commercial:documents", ("ventes",), {}),
            ("Saisir un document de vente", "commercial:document_create", ("FACTURE",), {}),
            ("Saisir une commande client", "commercial:document_create", ("COMMANDE",), {}),
            ("Gestion des comptes clients", "commercial:clients", (), {"vue": "comptes"}),
            ("Opérations de caisse", "commercial:operations_caisse", (), {}),
            ("Rapport commercial journalier", "commercial:rapport_commercial", (), {}),
            ("CRM", "", (), {}),
        ]),
        ("Gestion des achats", [
            ("Liste des fournisseurs", "commercial:fournisseurs", (), {}),
            ("Liste des documents d'achat", "commercial:documents", ("achats",), {}),
            ("Saisir un document d'achat", "commercial:document_create", ("ACHAT_FACTURE",), {}),
            ("Saisir une commande fournisseur", "commercial:document_create", ("ACHAT_COMMANDE",), {}),
            ("Gestion des comptes fournisseurs", "commercial:fournisseurs", (), {"vue": "comptes"}),
        ]),
        ("Gestion des articles et stocks", [
            ("Liste des articles", "commercial:articles", (), {}),
            ("Liste des documents de stock", "commercial:documents", ("stocks",), {}),
            ("Saisir un document de stock", "commercial:document_create", ("STOCK_ENTREE",), {}),
            ("Gestion des comptes articles", "commercial:stock", (), {}),
            ("Saisie d'inventaire", "commercial:inventaires", (), {}),
            ("Livre d'inventaire", "commercial:etat_inventaire", (), {"vue": "livre"}),
            ("Pointage des bons (fiche de stock)", "commercial:pointage", (), {}),
            ("Rapprochement fiche / ordinateur", "commercial:fiche_rapprochement", (), {}),
        ]),
    ],
}


def barre_verticale(module):
    """[{titre, liens: [{titre, url}]}] du logiciel (vide si Sage n'en a pas été relevée)."""
    groupes = []
    for titre, liens in BARRE_VERTICALE.get(module.code, []):
        groupes.append({"titre": titre, "liens": [
            {"titre": t, "url": (reverse(nom, args=args) + (f"?{urlencode(query)}" if query else "")) if nom else None}
            for t, nom, args, query in liens]})
    return groupes


# Fichiers liés (Fichier › À propos de votre société) : dans Sage, le fichier commercial pointe vers le fichier
# comptable et inversement. Ici les logiciels partagent une seule base : tout ce qui est créé dans l'un est
# aussitôt présent dans l'autre.
PARTAGE = {
    frozenset({"commercial", "comptabilite"}): "Tiers, plan comptable, codes journaux, banques, taux de taxes, plan analytique, "
                                               "exercices, utilisateurs, profils et droits des écrans communs",
    frozenset({"commercial", "reporting"}): "Lecture des documents, articles, familles, stocks et tiers",
    frozenset({"comptabilite", "reporting"}): "Lecture des écritures, comptes, balances et états financiers",
    frozenset({"transport", "commercial"}): "Clients en compte, opérations de caisse, règlements",
    frozenset({"transport", "comptabilite"}): "Écritures des billets, colis, fret et dépenses ; plan comptable, journaux, analytique "
                                              "(gares, véhicules)",
    frozenset({"transport", "reporting"}): "Lecture des recettes et des écritures",
}


def fichiers_lies(module):
    """[(logiciel lié, données partagées)…] d'un logiciel."""
    return [(m, PARTAGE.get(frozenset({module.code, m.code}), "Même base : tiers, plan comptable, journaux, véhicules, agences"))
            for m in MODULES if m is not module]


def module_pour_chemin(chemin):
    for module in MODULES:
        if chemin.startswith(module.prefixe):
            return module
    return None


def _module_cible(module, lien):
    """Code du logiciel qui affiche ce lien (« » si c'est le module lui-même, « web » hors logiciel)."""
    if not lien:
        return ""
    autre = module_pour_chemin(lien)               # le préfixe le plus précis (/transport/garage/ avant /transport/)
    if autre is module:
        return ""
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
            noeuds.append({"code": el.code, "separateur": True, "titre": "", "enfants": [], "url": None, "preuve": "",
                           "actif": False, "ouvert": False, "disponible": False, "action": "", "module": ""})
            continue
        enfants = _arbre(module, el.tous_enfants(), chemin, parametres, meilleur)
        lien = el.lien()
        cible = _module_cible(module, lien)
        preuve = el.preuve or PREUVE_PAR_DEFAUT.get(module.code, "")
        noeud = {"code": el.code, "titre": el.titre, "icone": el.icone, "url": lien, "enfants": enfants,
                 "action": el.action, "module": cible, "separateur": False, "preuve": preuve,
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


def _metier():
    """Métiers affichés : transport, commerce, ou les deux (activité mixte)."""
    from .models import Societe

    activite = Societe.get().activite
    return {"transport"} if activite == Societe.ACTIVITE_TRANSPORT else (
        {"commerce"} if activite == Societe.ACTIVITE_COMMERCE else {"transport", "commerce"})


def selon_metier(elements, metiers):
    """Entrées du métier de la société : le Transport et le Commerce n'ont ni le même plan tiers, ni le même plan
    analytique, ni le même reporting (une entrée sans métier est commune)."""
    import dataclasses

    return [dataclasses.replace(e, enfants=selon_metier(e.enfants, metiers)) if e.enfants else e
            for e in elements if not e.edition or e.edition in metiers]


def structure_module(module, chemin="", parametres=None):
    """Menus du module, avec le menu et l'élément actifs."""
    parametres = parametres or {}
    meilleur = {"score": None, "noeud": None}
    onglets = []
    metiers = _metier()
    for onglet in module.onglets:
        avant = meilleur["noeud"]
        arbre = _arbre(module, selon_metier(onglet.elements, metiers), chemin, parametres, meilleur)
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
