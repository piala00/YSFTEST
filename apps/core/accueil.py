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


def analytique():
    """Comptabilité analytique : lue sur les écritures générales validées (véhicule, section…), jamais ressaisie."""
    from apps.comptabilite import plan_analytique as pa
    from apps.core.models import Societe

    du, au, _ = pa.periode({})                                         # mois en cours
    periode = f"du={du.isoformat()}&au={au.isoformat()}"
    plan = [{"groupe": "Plan analytique", "liens": [
        _raccourci("Tous les axes", "bi-diagram-3", "analytique:plan", query=periode),
        *[_raccourci(titre, "bi-list-nested", "analytique:axe", code, query=periode) for code, titre, _ in pa.axes()]]}]
    if Societe.get().activite == Societe.ACTIVITE_COMMERCE:
        s = pa.synthese_axes(du, au)
        return {
            "raccourcis": plan + [{"groupe": "Sections", "liens": [
                _raccourci("Balance analytique", "bi-diagram-2", "comptabilite:balance_analytique"),
                _raccourci("Affecter une section", "bi-pencil-square", "comptabilite:ventilation"),
                _raccourci("Plan analytique (sections)", "bi-list-ol", "analytique:sections")]}],
            "indicateurs": [_indicateur("Produits du mois", s["gl"]["produits"], reverse("analytique:plan") + "?" + periode),
                            _indicateur("Charges du mois", s["gl"]["charges"], reverse("analytique:plan") + "?" + periode),
                            *[_indicateur(f"Non affecté : {a['titre']}", a["charges_non_affectees"] + a["produits_non_affectes"],
                                          reverse("analytique:axe", args=[a["code"]]) + "?" + periode,
                                          alerte=bool(a["charges_non_affectees"] + a["produits_non_affectes"]))
                              for a in s["axes"][:3]]],
            "dernieres": [], "titre_dernieres": "",
        }
    from apps.reporting import services
    from apps.transport import analytique as ana

    debut, fin = services._periode()
    fin_effective = min(fin, datetime.date.today()) if debut <= datetime.date.today() else fin
    r = ana.vehicules(debut, fin_effective)
    c = r["controle"]
    vehicules = sorted((l for l in r["lignes"] if l["produits"] or l["charges"]), key=lambda l: l["resultat_societe"])
    return {
        "raccourcis": plan + [
            {"groupe": "Véhicules", "liens": [
                _raccourci("Comptes d'exploitation", "bi-bus-front", "comptabilite:analytique_vehicules"),
                _raccourci("Grand-livre des véhicules", "bi-book", "comptabilite:grand_livre_vehicules"),
                _raccourci("Balance des véhicules", "bi-table", "comptabilite:balance_vehicules"),
            ]},
            {"groupe": "Propriétaires", "liens": [
                _raccourci("Portefeuilles et résultats", "bi-people", "comptabilite:analytique_proprietaires"),
                _raccourci("Relevés et règlements", "bi-receipt", "comptabilite:analytique_releves"),
            ]},
            {"groupe": "Sections", "liens": [
                _raccourci("Balance analytique", "bi-diagram-2", "comptabilite:balance_analytique"),
                _raccourci("Affecter une section", "bi-pencil-square", "comptabilite:ventilation"),
                _raccourci("Plan analytique (sections)", "bi-list-ol", "analytique:sections"),
            ]},
        ],
        "indicateurs": [
            _indicateur("Produits affectés aux véhicules", c["produits_affectes"], reverse("comptabilite:analytique_vehicules"),
                        detail=f"sur {c['produits_gl']:,.0f} en comptabilité générale".replace(",", " ")),
            _indicateur("Charges affectées aux véhicules", c["charges_affectees"], reverse("comptabilite:analytique_vehicules")),
            _indicateur("Charges non affectées", c["charges_non_affectees"], reverse("comptabilite:analytique_vehicules"),
                        alerte=bool(c["produits_non_affectes"]), detail="frais généraux, siège, gares"),
            _indicateur("Résultat des véhicules", r["total"]["resultat_societe"], reverse("comptabilite:analytique_vehicules")),
        ],
        "dernieres": [
            {"date": fin_effective, "piece": l["vehicule"].immatriculation, "libelle": str(l["vehicule"]),
             "montant": l["resultat_societe"], "statut": "résultat de la période",
             "url": reverse("comptabilite:analytique_vehicule", args=[l["vehicule"].pk])}
            for l in vehicules[:8]
        ],
        "titre_dernieres": "Véhicules au résultat le plus faible",
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
            {"groupe": "Direction", "liens": [
                _raccourci("Rapport journalier de l'agence", "bi-clipboard-data", "transport:rapport_journalier"),
                _raccourci("Balance des véhicules", "bi-bus-front", "transport:balance_vehicules"),
                _raccourci("Départs du jour", "bi-calendar-check", "transport:departs"),
                _raccourci("Échanges entre agences", "bi-arrow-left-right", "transport:echanges"),
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
                _raccourci("Balance des véhicules", "bi-bus-front", "transport:balance_vehicules"),
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


def billetterie():
    from apps.transport.models import Billet, Depart, Troncon

    today = datetime.date.today()
    departs = Depart.objects.filter(date=today, statut=Depart.PROGRAMME)
    billets = Billet.objects.filter(date_vente=today).exclude(statut=Billet.ANNULE)
    correspondances = Troncon.objects.filter(depart__isnull=True, statut=Troncon.A_VOYAGER, billet__statut=Billet.VENDU).count()
    return {
        "raccourcis": [{"groupe": "Guichet", "liens": [
            _raccourci("Vendre un billet", "bi-ticket-perforated", "transport:billet_vente"),
            _raccourci("Départs du jour", "bi-bus-front", "transport:departs"),
            _raccourci("Billets vendus", "bi-list-ul", "transport:billets"),
            _raccourci("Programmer un départ", "bi-calendar-plus", "transport:depart_create"),
            _raccourci("Recette de la billetterie", "bi-cash-stack", "transport:recette_billetterie"),
        ]}],
        "indicateurs": [
            _indicateur("Départs encore à la vente", departs.count(), reverse("transport:departs"), genre="nombre"),
            _indicateur("Billets vendus aujourd'hui", billets.count(), reverse("transport:billets"), genre="nombre"),
            _indicateur("Encaissé aujourd'hui", sum((b.prix for b in billets if b.paiement != Billet.COMPTE), ZERO),
                        reverse("transport:recette_billetterie")),
            _indicateur("Correspondances à placer", correspondances, reverse("transport:departs"), genre="nombre",
                        alerte=bool(correspondances)),
        ],
        "titre_dernieres": "Derniers billets",
        "dernieres": [{"date": b.date_vente, "piece": b.numero, "libelle": f"{b.voyageur} · {b.depart.ligne.code}", "montant": b.prix,
                       "statut": b.get_statut_display(), "url": reverse("transport:billet_detail", args=[b.pk])}
                      for b in Billet.objects.select_related("depart__ligne").order_by("-cree_le")[:10]],
    }


def colis():
    from apps.transport.models import Colis

    today = datetime.date.today()
    a_charger, a_remettre = Colis.objects.filter(statut=Colis.ENREGISTRE), Colis.objects.filter(statut=Colis.ARRIVE)
    cr = Colis.objects.filter(statut=Colis.LIVRE, contre_remboursement__gt=0, cr_reverse_le__isnull=True, site_origine="")
    return {
        "raccourcis": [{"groupe": "Expéditions", "liens": [
            _raccourci("Enregistrer un colis", "bi-box-seam", "transport:colis_create", query="nature=COLIS"),
            _raccourci("Enregistrer un courrier", "bi-envelope", "transport:colis_create", query="nature=COURRIER"),
            _raccourci("Envois à charger", "bi-box-arrow-up", "transport:colis", query="statut=ENREGISTRE"),
            _raccourci("Envois à remettre", "bi-box-arrow-in-down", "transport:colis", query="statut=ARRIVE"),
            _raccourci("Recette des colis", "bi-cash-stack", "transport:recette_colis"),
        ]}],
        "indicateurs": [
            _indicateur("Envois du jour", Colis.objects.filter(date=today).count(), reverse("transport:colis"), genre="nombre"),
            _indicateur("À charger", a_charger.count(), reverse("transport:colis") + "?statut=ENREGISTRE", genre="nombre",
                        alerte=a_charger.exists()),
            _indicateur("À remettre aux destinataires", a_remettre.count(), reverse("transport:colis") + "?statut=ARRIVE",
                        genre="nombre", alerte=a_remettre.exists()),
            _indicateur("Contre-remboursements à reverser", sum((c.contre_remboursement for c in cr), ZERO),
                        reverse("transport:colis") + "?statut=LIVRE", alerte=cr.exists()),
        ],
        "titre_dernieres": "Derniers envois",
        "dernieres": [{"date": c.date, "piece": c.numero, "libelle": f"{c.expediteur} → {c.destinataire}", "montant": c.prix,
                       "statut": c.get_statut_display(), "url": reverse("transport:colis_detail", args=[c.pk])}
                      for c in Colis.objects.order_by("-cree_le")[:10]],
    }


def garage():
    from apps.garage.models import OrdreReparation, PleinCarburant
    from apps.transport.models import Vehicule

    today = datetime.date.today()
    pleins = PleinCarburant.objects.filter(date__year=today.year, date__month=today.month)
    au_garage = OrdreReparation.objects.filter(statut=OrdreReparation.OUVERT)
    papiers = [v for v in Vehicule.objects.filter(actif=True) if v.alertes()]
    return {
        "raccourcis": [{"groupe": "Garage", "liens": [
            _raccourci("Saisir un plein", "bi-fuel-pump", "garage:plein_create"),
            _raccourci("Entrée au garage", "bi-wrench", "garage:reparation_create"),
            _raccourci("Réparations en cours", "bi-tools", "garage:reparations"),
            _raccourci("Véhicules", "bi-bus-front", "transport:vehicules"),
            _raccourci("Consommation", "bi-speedometer", "garage:consommation"),
        ]}],
        "indicateurs": [
            _indicateur("Véhicules au garage", au_garage.count(), reverse("garage:reparations"), genre="nombre",
                        alerte=au_garage.exists()),
            _indicateur("Carburant du mois (litres)", int(sum((p.litres for p in pleins), ZERO)), reverse("garage:pleins"), genre="nombre"),
            _indicateur("Carburant du mois", sum((p.montant for p in pleins), ZERO), reverse("garage:pleins")),
            _indicateur("Papiers à renouveler", len(papiers), reverse("garage:echeances"), genre="nombre", alerte=bool(papiers)),
        ],
        "titre_dernieres": "Derniers pleins",
        "dernieres": [{"date": p.date, "piece": p.numero, "libelle": f"{p.vehicule.immatriculation} · {p.litres} L", "montant": p.montant,
                       "statut": p.station, "url": reverse("transport:vehicule_fiche", args=[p.vehicule_id])}
                      for p in PleinCarburant.objects.select_related("vehicule").order_by("-cree_le")[:10]],
    }


def personnel():
    from apps.personnel.models import Avance, Employe, PeriodePaie

    employes = Employe.objects.filter(actif=True)
    derniere = PeriodePaie.objects.first()
    return {
        "raccourcis": [{"groupe": "Personnel", "liens": [
            _raccourci("Employés", "bi-person-vcard", "personnel:employes"),
            _raccourci("Verser une avance", "bi-cash", "personnel:avance_create"),
            _raccourci("Paie du mois", "bi-wallet2", "personnel:paies"),
            _raccourci("Rubriques de paie", "bi-list-check", "personnel:rubriques"),
        ]}],
        "indicateurs": [
            _indicateur("Employés", employes.count(), reverse("personnel:employes"), genre="nombre"),
            _indicateur("Masse salariale de base", sum((e.salaire_base for e in employes), ZERO), reverse("personnel:employes")),
            _indicateur("Avances à reprendre", sum((a.montant for a in Avance.objects.filter(bulletin__isnull=True, ecriture__isnull=False)), ZERO),
                        reverse("personnel:avances")),
            _indicateur("Dernière paie", str(derniere or "—"), reverse("personnel:paies"), genre="nombre",
                        detail=derniere.get_statut_display() if derniere else ""),
        ],
        "titre_dernieres": "Dernières avances",
        "dernieres": [{"date": a.date, "piece": a.employe.matricule, "libelle": a.employe.nom, "montant": a.montant,
                       "statut": "reprise" if a.bulletin_id else "à reprendre", "url": reverse("personnel:avances")}
                      for a in Avance.objects.select_related("employe")[:10]],
    }


PAGES = {"commercial": commercial, "comptabilite": comptabilite, "analytique": analytique, "transport": transport, "billetterie": billetterie,
         "colis": colis, "garage": garage, "personnel": personnel}
