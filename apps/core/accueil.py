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
        # Blocs de tuiles de l'écran d'accueil (modèle étudié : Gestion commerciale V12)
        "raccourcis": [
            {"groupe": "Gestion des ventes", "liens": [
                _raccourci("Liste des clients", "bi-person", "commercial:clients"),
                _raccourci("Saisir un document de vente", "bi-file-earmark-plus", "commercial:document_create", D.FACTURE),
                _raccourci("Saisir un règlement client", "bi-plus-lg", "commercial:reglement_create"),
                _raccourci("Gestion des comptes clients", "bi-archive", "commercial:clients", query="vue=comptes"),
            ]},
            {"groupe": "Gestion des achats", "liens": [
                _raccourci("Liste des fournisseurs", "bi-person-badge", "commercial:fournisseurs"),
                _raccourci("Saisir un document d'achat", "bi-file-earmark-plus", "commercial:document_create", D.ACHAT_FACTURE),
                _raccourci("Saisir un règlement fournisseur", "bi-plus-lg", "commercial:reglement_create"),
                _raccourci("Gestion des comptes fournisseurs", "bi-archive", "commercial:fournisseurs", query="vue=comptes"),
            ]},
            {"groupe": "Gestion des stocks", "liens": [
                _raccourci("Liste des articles", "bi-box", "commercial:articles"),
                _raccourci("Saisir un document de stock", "bi-file-earmark-plus", "commercial:document_create", D.STOCK_ENTREE),
                _raccourci("Gestion des comptes articles", "bi-archive", "commercial:stock"),
                _raccourci("Livre d'inventaire", "bi-printer", "commercial:etat_inventaire"),
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


def transport():
    from apps.transport.models import Billet, Colis, Depart

    today = datetime.date.today()
    departs = Depart.objects.filter(date=today).exclude(statut=Depart.ANNULE)
    billets = Billet.objects.filter(date_vente=today).exclude(statut=Billet.ANNULE)
    a_remettre = Colis.objects.filter(statut=Colis.ARRIVE)
    cr = Colis.objects.filter(statut=Colis.LIVRE, contre_remboursement__gt=0, cr_reverse_le__isnull=True)
    return {
        "raccourcis": [
            {"groupe": "Billetterie", "liens": [
                _raccourci("Départs du jour", "bi-bus-front", "transport:departs"),
                _raccourci("Vendre un billet", "bi-ticket-perforated", "transport:billet_vente"),
                _raccourci("Billets vendus", "bi-list-ul", "transport:billets"),
                _raccourci("Programmer un départ", "bi-calendar-plus", "transport:depart_create"),
            ]},
            {"groupe": "Colis et courrier", "liens": [
                _raccourci("Enregistrer un colis", "bi-box-seam", "transport:colis_create", query="nature=COLIS"),
                _raccourci("Enregistrer un courrier", "bi-envelope", "transport:colis_create", query="nature=COURRIER"),
                _raccourci("Envois à remettre", "bi-box-arrow-in-down", "transport:colis", query="statut=ARRIVE"),
            ]},
            {"groupe": "Logistique et états", "liens": [
                _raccourci("Enregistrer du fret", "bi-truck", "transport:colis_create", query="nature=FRET"),
                _raccourci("Dépense de véhicule", "bi-fuel-pump", "transport:depense_create"),
                _raccourci("Recette journalière", "bi-cash-stack", "transport:recette"),
                _raccourci("Rentabilité par ligne", "bi-graph-up", "transport:rentabilite"),
            ]},
        ],
        "indicateurs": [
            _indicateur("Départs du jour", departs.count(), reverse("transport:departs"), genre="nombre"),
            _indicateur("Billets vendus aujourd'hui", billets.count(), reverse("transport:billets"), genre="nombre"),
            _indicateur("Recette billets du jour", sum((b.prix for b in billets), ZERO), reverse("transport:recette")),
            _indicateur("Envois à remettre", a_remettre.count(), reverse("transport:colis") + "?statut=ARRIVE", genre="nombre",
                        alerte=a_remettre.exists()),
            _indicateur("Contre-remboursements à reverser", sum((c.contre_remboursement for c in cr), ZERO),
                        reverse("transport:colis") + "?statut=LIVRE", alerte=cr.exists()),
        ],
        "titre_dernieres": "Derniers billets",
        "dernieres": [{"date": b.date_vente, "piece": b.numero, "libelle": f"{b.voyageur} · {b.depart.ligne.code}",
                       "montant": b.prix, "statut": b.get_statut_display(), "url": reverse("transport:billet_detail", args=[b.pk])}
                      for b in Billet.objects.select_related("depart__ligne").order_by("-cree_le")[:10]],
    }


PAGES = {"commercial": commercial, "comptabilite": comptabilite, "transport": transport}
