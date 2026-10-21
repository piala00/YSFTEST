"""Page d'accueil de chaque logiciel : raccourcis des tâches courantes, indicateurs et dernières pièces.

Comme l'écran d'accueil de Sage 100 V12, elle ne reprend pas les menus : ceux-ci restent dans la barre de menus.
"""
import datetime
from decimal import Decimal

from django.db.models import Sum
from django.urls import reverse

ZERO = Decimal("0")


def _raccourci(titre, icone, url_name, *args, query="", aide=""):
    return {"titre": titre, "icone": icone, "url": reverse(url_name, args=args) + (f"?{query}" if query else ""), "aide": aide}


def _indicateur(titre, valeur, url="", genre="montant", alerte=False, detail=""):
    return {"titre": titre, "valeur": valeur, "url": url, "genre": genre, "alerte": alerte, "detail": detail}


def commercial():
    from apps.commercial.models import Article, Document
    from apps.reporting import services

    debut, fin = services._periode()
    today = datetime.date.today()
    factures = [d for d in Document.objects.filter(type_document=Document.FACTURE, statut=Document.VALIDE) if d.reste_a_payer > 0]
    alertes = [a for a in Article.objects.filter(suivi_stock=True, actif=True) if a.en_alerte]
    D = Document
    return {
        "raccourcis": [
            {"groupe": "Ventes", "liens": [
                _raccourci("Devis", "bi-file-earmark-text", "commercial:document_create", D.DEVIS),
                _raccourci("Bon de livraison", "bi-truck", "commercial:document_create", D.LIVRAISON),
                _raccourci("Facture", "bi-receipt", "commercial:document_create", D.FACTURE),
                _raccourci("Règlement", "bi-cash-coin", "commercial:reglement_create"),
            ]},
            {"groupe": "Achats", "liens": [
                _raccourci("Bon de commande", "bi-cart", "commercial:document_create", D.ACHAT_COMMANDE),
                _raccourci("Bon de réception", "bi-box-arrow-in-down", "commercial:document_create", D.ACHAT_RECEPTION),
                _raccourci("Facture fournisseur", "bi-receipt-cutoff", "commercial:document_create", D.ACHAT_FACTURE),
            ]},
            {"groupe": "Stocks", "liens": [
                _raccourci("Mouvement d'entrée", "bi-box-arrow-in-right", "commercial:document_create", D.STOCK_ENTREE),
                _raccourci("Mouvement de sortie", "bi-box-arrow-right", "commercial:document_create", D.STOCK_SORTIE),
                _raccourci("Transfert de dépôt", "bi-arrow-left-right", "commercial:document_create", D.STOCK_VIREMENT),
                _raccourci("État du stock", "bi-boxes", "commercial:stock"),
            ]},
            {"groupe": "Fichiers", "liens": [
                _raccourci("Clients", "bi-people", "commercial:clients"),
                _raccourci("Fournisseurs", "bi-truck-front", "commercial:fournisseurs"),
                _raccourci("Articles", "bi-box-seam", "commercial:articles"),
            ]},
        ],
        "indicateurs": [
            _indicateur("Chiffre d'affaires du mois (HT)", services.chiffre_affaires(today.replace(day=1), today),
                        reverse("reporting:ventes")),
            _indicateur("Chiffre d'affaires de l'exercice (HT)", services.chiffre_affaires(debut, fin), reverse("reporting:ventes")),
            _indicateur("Factures clients non réglées", sum((d.reste_a_payer for d in factures), ZERO),
                        reverse("commercial:documents", args=["ventes"]) + f"?type={D.FACTURE}", alerte=bool(factures),
                        detail=f"{len(factures)} facture(s)"),
            _indicateur("Devis en cours", Document.objects.filter(type_document=D.DEVIS, statut=D.VALIDE).count(),
                        reverse("commercial:documents", args=["ventes"]) + f"?type={D.DEVIS}", genre="nombre"),
            _indicateur("Valeur du stock", sum((a.valeur_stock for a in Article.objects.filter(suivi_stock=True)), ZERO),
                        reverse("commercial:stock")),
            _indicateur("Articles sous le stock d'alerte", len(alertes), reverse("commercial:besoins"), genre="nombre",
                        alerte=bool(alertes)),
        ],
        "dernieres": [
            {"date": d.date, "piece": d.numero, "libelle": f"{d.get_type_document_display()} · {d.tiers.nom if d.tiers else (d.depot or '')}",
             "montant": d.total_ttc, "statut": d.get_statut_display(), "url": reverse("commercial:document_detail", args=[d.pk])}
            for d in Document.objects.select_related("tiers", "depot").order_by("-date", "-id")[:8]
        ],
        "titre_dernieres": "Derniers documents",
    }


def comptabilite():
    from apps.comptabilite import etats, services as compta
    from apps.comptabilite.models import Ecriture
    from apps.reporting import services

    debut, fin = services._periode()
    today = datetime.date.today()
    fin_effective = min(fin, today) if debut <= today else fin
    soldes = compta.soldes_par_compte(fin_effective)
    brouillard = Ecriture.objects.filter(statut=Ecriture.STATUT_BROUILLARD).count()
    tva = compta.declaration_tva(debut, fin_effective)
    return {
        "raccourcis": [
            {"groupe": "Saisie", "liens": [
                _raccourci("Saisie par pièce", "bi-pencil-square", "comptabilite:ecriture_create"),
                _raccourci("Écritures", "bi-journal-text", "comptabilite:ecritures"),
                _raccourci("Interrogation et lettrage", "bi-link-45deg", "comptabilite:lettrage"),
                _raccourci("Rapprochement bancaire", "bi-check2-square", "comptabilite:rapprochement"),
            ]},
            {"groupe": "États", "liens": [
                _raccourci("Balance", "bi-table", "comptabilite:balance"),
                _raccourci("Grand-livre", "bi-book", "comptabilite:grand_livre"),
                _raccourci("Journal général", "bi-journals", "comptabilite:journal"),
                _raccourci("Balance âgée", "bi-hourglass-split", "comptabilite:balance_agee", query="type=CLIENT"),
            ]},
            {"groupe": "Fin de période", "liens": [
                _raccourci("Déclaration de TVA", "bi-percent", "comptabilite:tva"),
                _raccourci("Bilan", "bi-bank", "comptabilite:bilan"),
                _raccourci("Compte de résultat", "bi-graph-up", "comptabilite:compte_resultat"),
                _raccourci("Clôture de l'exercice", "bi-calendar-check", "comptabilite:cloture_exercice"),
            ]},
            {"groupe": "Structure", "liens": [
                _raccourci("Plan comptable", "bi-list-ol", "comptabilite:comptes"),
                _raccourci("Codes journaux", "bi-collection", "comptabilite:journaux"),
            ]},
        ],
        "indicateurs": [
            _indicateur("Trésorerie", services.tresorerie(fin_effective), reverse("comptabilite:balance") + "?compte_debut=5&compte_fin=5"),
            _indicateur("Créances clients", sum((s for n, s in soldes.items() if n.startswith("41")), ZERO),
                        reverse("comptabilite:balance_agee") + "?type=CLIENT"),
            _indicateur("Dettes fournisseurs", -sum((s for n, s in soldes.items() if n.startswith("40")), ZERO),
                        reverse("comptabilite:balance_agee") + "?type=FOURNISSEUR"),
            _indicateur("Résultat de l'exercice", etats.compte_de_resultat(debut, fin_effective)["resultat_net"],
                        reverse("comptabilite:compte_resultat")),
            _indicateur("TVA à reverser" if tva["solde"] >= 0 else "Crédit de TVA", abs(tva["solde"]), reverse("comptabilite:tva")),
            _indicateur("Écritures au brouillard", brouillard, reverse("comptabilite:ecritures") + "?statut=BROUILLARD",
                        genre="nombre", alerte=bool(brouillard), detail="à valider avant la clôture" if brouillard else ""),
        ],
        "dernieres": [
            {"date": e.date, "piece": e.numero, "libelle": f"{e.journal.code} · {e.libelle}", "montant": e.total or ZERO,
             "statut": e.get_statut_display(), "url": reverse("comptabilite:ecriture_detail", args=[e.pk])}
            for e in Ecriture.objects.select_related("journal").annotate(total=Sum("lignes__debit")).order_by("-date", "-id")[:8]
        ],
        "titre_dernieres": "Dernières écritures",
    }


PAGES = {"commercial": commercial, "comptabilite": comptabilite}
