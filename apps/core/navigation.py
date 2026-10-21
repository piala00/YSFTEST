"""Menus de l'ERP, organisés comme Sage 100c.

Chaque module est un logiciel à part entière doté d'une barre de menus :

    Fichier · Structure · Traitement · Etat · Fenêtre · ?

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
        E("fenetre.reorganiser", "Réorganiser"),
        E("fenetre.actualiser", "Actualiser", icone="bi-arrow-clockwise", action="actualiser"),
        E("fenetre.personnaliser", "Personnaliser"),
        E("fenetre.personnaliser_ecrans", "Personnaliser les écrans"),
        E("fenetre.personnaliser_liste", "Personnaliser la liste"),
        E("fenetre.ajustement", "Ajustement automatique des colonnes"),
        SEP(),
        E("fenetre.preferences", "Préférences"),
        E("fenetre.barre_verticale", "Barre verticale"),
        E("fenetre.mode_assistant", "Mode assistant"),
        E("fenetre.mode_personnalise", "Mode personnalisé"),
        SEP(),
        E("fenetre.accueil", "Page d'accueil", MODULES_ACCUEIL[module], icone="bi-house"),
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
                E("fichier.parametres.tiers", "Tiers"),
                E("fichier.parametres.ressources", "Ressources"),
                E("fichier.parametres.analytique", "Analytique"),
                E("fichier.parametres.tva", "Tva et taxes"),
                E("fichier.parametres.contacts_types", "Contacts"),
                E("fichier.parametres.international", "International"),
                E("fichier.parametres.banques", "Banques"),
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
            E("fichier.autorisations", "Autorisations d'accès", "admin:auth_user_changelist", icone="bi-shield-lock"),
            SEP(),
            E("fichier.importer", "Importer", icone="bi-box-arrow-in-down"),
            E("fichier.exporter", "Exporter", icone="bi-box-arrow-up"),
            E("fichier.format_import", "Format import/export paramétrable"),
            E("fichier.site_a_site", "Communication site à site"),
            E("fichier.paiement_ligne", "Paiement en ligne"),
            SEP(),
            E("fichier.mise_en_page", "Mise en page"),
            E("fichier.imprimer", "Imprimer…", icone="bi-printer", action="imprimer"),
            E("fichier.format_impression", "Format d'impression"),
            E("fichier.impression_differee", "Impression différée"),
            SEP(),
            E("fichier.outils", "Outils"),
            E("fichier.quitter", "Quitter", icone="bi-power", action="quitter"),
        ]),
        Onglet("structure", "Structure", "bi-diagram-3", [
            E("articles.familles", "Familles", "commercial:familles", icone="bi-tags"),
            E("articles.liste", "Articles", "commercial:articles", icone="bi-box-seam"),
            E("structure.nomenclatures", "Nomenclatures"),
            E("structure.comptabilite", "Comptabilité", icone="bi-calculator", enfants=[
                E("structure.plan_comptable", "Plan comptable", "comptabilite:comptes"),
                E("structure.plan_analytique", "Plan analytique"),
                E("structure.taux_taxes", "Taux de taxes", enfants=[
                    E("structure.taux_taxes.tva_debit", "TVA/ débit - Vente de biens"),
                    E("structure.taux_taxes.tva_encaissement", "TVA/ encaissement - Prestation de services"),
                    E("structure.taux_taxes.tp_ht", "TP/ HT"),
                    E("structure.taux_taxes.tp_ttc", "TP/ TTC"),
                    E("structure.taux_taxes.tp_poids", "TP/ poids"),
                    E("structure.taux_taxes.surtaxe", "Surtaxe"),
                ]),
                E("structure.codes_journaux", "Codes journaux", "comptabilite:journaux"),
                E("structure.banques", "Banques"),
                E("structure.modele_reglement", "Modèle de règlement"),
                E("structure.modele_grille", "Modèle de grille"),
            ]),
            E("structure.codes_affaires", "Codes affaires"),
            SEP(),
            E("tiers.clients", "Clients", "commercial:clients", icone="bi-people"),
            E("tiers.fournisseurs", "Fournisseurs", "commercial:fournisseurs", icone="bi-truck"),
            E("structure.baremes", "Barèmes", icone="bi-percent", enfants=[
                E("structure.baremes.commissions", "Commissions représentants"),
                E("structure.baremes.rrr_clients", "Rabais, remises et ristournes clients"),
                E("structure.baremes.rrr_fournisseurs", "Rabais, remises et ristournes fournisseurs"),
                E("structure.baremes.promos_clients", "Soldes et promotions clients"),
                E("structure.baremes.promos_fournisseurs", "Soldes et promotions fournisseurs"),
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
                E("ventes.tous", "Tous les documents des ventes", "commercial:documents", "ventes"),
                SEP(),
                *_documents("ventes", TYPES_VENTE),
            ]),
            E("achats.documents", "Documents des achats", icone="bi-cart", enfants=[
                E("achats.tous", "Tous les documents des achats", "commercial:documents", "achats"),
                SEP(),
                *_documents("achats", TYPES_ACHAT),
                SEP(),
                E("achats.acheteur", "Gestion acheteur entête et ligne de document"),
                E("achats.bon_a_payer", "Gestion du Bon à payer"),
            ]),
            E("stocks.documents", "Documents des stocks", icone="bi-boxes", enfants=[
                E("stocks.tous", "Tous les documents des stocks", "commercial:documents", "stocks"),
                SEP(),
                *_documents("stocks", TYPES_STOCK),
                E("stocks.depreciation", "Dépréciation de stock"),
                SEP(),
                E("stocks.preparation_fabrication", "Préparation de fabrication"),
                E("stocks.ordre_fabrication", "Ordre de fabrication"),
                E("stocks.bon_fabrication", "Bon de fabrication"),
            ]),
            E("traitement.documents_internes", "Documents internes"),
            E("traitement.sage_connect", "Sage Connect", enfants=[
                E("traitement.sage_connect.societe", "Accéder à la société"),
                E("traitement.sage_connect.transmission", "Transmission des factures clients"),
                E("traitement.sage_connect.reception", "Réception des factures fournisseurs"),
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
                E("reglements.clients", "Gestion des règlements clients", "commercial:reglements", sens="E"),
                E("reglements.fournisseurs", "Gestion des règlements fournisseurs", "commercial:reglements", sens="D"),
                E("reglements.generation", "Génération des règlements"),
                E("reglements.paiements_ligne", "Intégration des paiements en ligne"),
            ]),
            E("traitement.modeles_prestations", "Modèles et prestations types"),
            E("traitement.abonnements", "Abonnements"),
            E("traitement.contremarque", "Contremarque"),
            SEP(),
            E("comptes", "Gestion des comptes", icone="bi-person-lines-fill", enfants=[
                E("comptes.clients", "Gestion des clients", "commercial:clients", vue="comptes"),
                E("comptes.fournisseurs", "Gestion des fournisseurs", "commercial:fournisseurs", vue="comptes"),
                E("comptes.articles", "Gestion des articles", "commercial:stock", vue="comptes"),
                E("comptes.affaires", "Gestion des affaires"),
                E("comptes.collaborateurs", "Gestion des collaborateurs"),
                E("comptes.ressources", "Gestion des ressources"),
                E("comptes.tracabilite", "Suivi traçabilité série/ lot"),
            ]),
            E("traitement.besoins", "Gestion des besoins", "commercial:articles", icone="bi-exclamation-triangle", alerte=1),
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
                E("maj_compta.variation_stock", "Variation de stock (inventaire permanent)", "commercial:stock", vue="variation"),
                E("maj_compta.engagements", "Engagements achats/ ventes"),
            ]),
            E("traitement.archivage", "Archivage"),
            E("traitement.cloture_periode", "Clôture période"),
            E("traitement.sauvegarde_fiscale", "Sauvegarde fiscale des données"),
        ]),
        Onglet("etat", "Etat", "bi-printer", [
            E("etats.personnalises", "Etats personnalisés"),
            SEP(),
            E("etats.analyse_clients", "Analyse clients", "commercial:etat_balance_agee", type="CLIENT"),
            E("etats.cadencier_clients", "Cadencier clients"),
            E("etats.ventes.clients", "Statistiques clients", "commercial:etat_ventes", vue="clients"),
            E("etats.mouvement_clients", "Mouvement clients", "comptabilite:grand_livre", compte_debut="411", compte_fin="411"),
            SEP(),
            E("etats.analyse_fournisseurs", "Analyse fournisseurs", "commercial:etat_balance_agee", type="FOURNISSEUR"),
            E("etats.cadencier_fournisseurs", "Cadencier fournisseurs"),
            E("etats.stats_fournisseurs", "Statistiques fournisseurs", "commercial:etat_achats"),
            E("etats.mouvement_fournisseurs", "Mouvement fournisseurs", "comptabilite:grand_livre", compte_debut="401", compte_fin="401"),
            SEP(),
            E("etats.ventes.articles", "Statistiques articles", "commercial:etat_ventes", vue="articles"),
            E("etats.mouvements", "Mouvements de stock", "commercial:mouvements", icone="bi-arrow-left-right", vue="etat"),
            E("etats.inventaire", "Inventaire", icone="bi-clipboard-data", enfants=[
                E("etats.inventaire.preparatoire", "Etat préparatoire", "commercial:etat_inventaire", vue="preparatoire"),
                E("etats.inventaire.livre", "Livre d'inventaire", "commercial:etat_inventaire", vue="livre"),
            ]),
            E("etats.cadencier_livraison", "Cadencier de livraison"),
            SEP(),
            E("etats.stats_ressources", "Statistiques ressources"),
            E("etats.stats_collaborateurs", "Statistiques collaborateurs"),
            E("etats.commissions", "Commissions représentants"),
            SEP(),
            E("etats.tableaux_bord", "Tableaux de bord", "reporting:dashboard", icone="bi-speedometer2"),
            E("etats.journaux_comptables", "Journaux comptables", "comptabilite:journal"),
            E("etats.libres", "Etats libres"),
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
        Onglet("etat", "Etat", "bi-printer", [
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
        Onglet("etat", "Etat", "bi-printer", [
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
