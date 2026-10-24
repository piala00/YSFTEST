"""Indicateurs de pilotage : chiffre d'affaires, créances, trésorerie, marges."""
import datetime
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth

from apps.commercial.models import Article, Document, LigneDocument, Tiers
from apps.comptabilite import etats, services
from apps.core.models import Exercice

ZERO = Decimal("0")
MOIS = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]


def _periode(exercice=None):
    exercice = exercice or Exercice.courant()
    if exercice:
        return exercice.date_debut, exercice.date_fin
    today = datetime.date.today()
    return today.replace(month=1, day=1), today.replace(month=12, day=31)


def _factures(types, debut, fin):
    return Document.objects.filter(type_document__in=types, statut__in=[Document.VALIDE, Document.TRANSFORME],
                                   date__gte=debut, date__lte=fin)


def chiffre_affaires(debut, fin):
    """CA HT net des avoirs."""
    factures = _factures([Document.FACTURE], debut, fin).aggregate(s=Sum("total_ht"))["s"] or ZERO
    avoirs = _factures([Document.AVOIR, Document.FACTURE_RETOUR], debut, fin).aggregate(s=Sum("total_ht"))["s"] or ZERO
    return factures - avoirs


def ca_mensuel(debut, fin, types_plus=(Document.FACTURE,), types_moins=(Document.AVOIR, Document.FACTURE_RETOUR)):
    valeurs = {}
    for signe, types in ((1, types_plus), (-1, types_moins)):
        rows = (_factures(types, debut, fin).annotate(mois=TruncMonth("date"))
                .values("mois").annotate(total=Sum("total_ht")))
        for r in rows:
            cle = (r["mois"].year, r["mois"].month)
            valeurs[cle] = valeurs.get(cle, ZERO) + signe * (r["total"] or ZERO)
    serie = []
    courant = debut.replace(day=1)
    while courant <= fin:
        serie.append({"mois": f"{MOIS[courant.month - 1]} {courant.year % 100:02d}",
                      "montant": valeurs.get((courant.year, courant.month), ZERO)})
        courant = (courant.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return serie


def top_clients(debut, fin, limite=5):
    return list(_factures([Document.FACTURE], debut, fin).values("tiers__id", "tiers__nom")
                .annotate(total=Sum("total_ht")).order_by("-total")[:limite])


def ventes_par_article(debut, fin, limite=None):
    qs = (LigneDocument.objects.filter(document__type_document=Document.FACTURE,
                                       document__statut__in=[Document.VALIDE, Document.TRANSFORME],
                                       document__date__gte=debut, document__date__lte=fin, article__isnull=False)
          .values("article__id", "article__reference", "article__designation", "article__cmup", "article__prix_achat")
          .annotate(quantite=Sum("quantite"), total=Sum("montant_ht")).order_by("-total"))
    resultat = []
    for r in qs[:limite] if limite else qs:
        cout = (r["quantite"] or ZERO) * (r["article__cmup"] or r["article__prix_achat"] or ZERO)
        r["marge"] = r["total"] - cout
        r["taux_marge"] = (r["marge"] / r["total"] * 100) if r["total"] else ZERO
        resultat.append(r)
    return resultat


def ventes_par_client(debut, fin):
    lignes = []
    for t in Tiers.objects.filter(type_tiers=Tiers.CLIENT):
        docs = Document.objects.filter(tiers=t, statut__in=[Document.VALIDE, Document.TRANSFORME],
                                       date__gte=debut, date__lte=fin)
        fa = docs.filter(type_document=Document.FACTURE).aggregate(ht=Sum("total_ht"), ttc=Sum("total_ttc"))
        av = docs.filter(type_document__in=(Document.AVOIR, Document.FACTURE_RETOUR)).aggregate(ht=Sum("total_ht"))
        ca = (fa["ht"] or ZERO) - (av["ht"] or ZERO)
        if ca:
            lignes.append({"tiers": t, "nb": docs.filter(type_document=Document.FACTURE).count(),
                           "ca_ht": ca, "ttc": fa["ttc"] or ZERO, "encours": t.encours()})
    return sorted(lignes, key=lambda l: -l["ca_ht"])


def achats_par_fournisseur(debut, fin):
    lignes = []
    for t in Tiers.objects.filter(type_tiers=Tiers.FOURNISSEUR):
        docs = Document.objects.filter(tiers=t, statut__in=[Document.VALIDE, Document.TRANSFORME],
                                       date__gte=debut, date__lte=fin)
        fa = docs.filter(type_document=Document.ACHAT_FACTURE).aggregate(ht=Sum("total_ht"), ttc=Sum("total_ttc"))
        av = docs.filter(type_document__in=(Document.ACHAT_AVOIR, Document.ACHAT_FACTURE_RETOUR)).aggregate(ht=Sum("total_ht"))
        montant = (fa["ht"] or ZERO) - (av["ht"] or ZERO)
        if montant:
            lignes.append({"tiers": t, "nb": docs.filter(type_document=Document.ACHAT_FACTURE).count(),
                           "ca_ht": montant, "ttc": fa["ttc"] or ZERO, "encours": t.encours()})
    return sorted(lignes, key=lambda l: -l["ca_ht"])


# Balance âgée, fenêtre de sélection Sage (skill sage100-fenetres-selection-v12, P008) : « D'après la date
# d'écriture » ou d'échéance ; trois délais, 30, 45 et 60 jours par défaut. Ces défauts viennent du manuel
# historique 8.50 : ils ne sont pas confirmés en V12 (skill sage100-v12-etats-fiches-achats-complement, A-P008).
D_APRES_ECRITURE, D_APRES_ECHEANCE = "ECRITURE", "ECHEANCE"
DELAIS_SAGE = (30, 45, 60)


def delais_valides(delais):
    """Trois délais croissants et positifs, sinon ceux de Sage."""
    try:
        d1, d2, d3 = (int(d) for d in delais)
    except (TypeError, ValueError):
        return DELAIS_SAGE
    return (d1, d2, d3) if 0 < d1 < d2 < d3 else DELAIS_SAGE


def balance_agee(type_tiers=Tiers.CLIENT, date_ref=None, tiers=None, d_apres=D_APRES_ECRITURE, delais=DELAIS_SAGE):
    """Factures non soldées, émises au plus tard à la date de situation, réparties par ancienneté : depuis la
    date de la facture (date d'écriture) ou depuis son échéance (la colonne « Non échu » n'existe qu'alors)."""
    date_ref = date_ref or datetime.date.today()
    type_facture = Document.FACTURE if type_tiers == Tiers.CLIENT else Document.ACHAT_FACTURE
    d1, d2, d3 = delais_valides(delais)
    echeance = d_apres == D_APRES_ECHEANCE
    tranches = ([("non_echu", "Non échu"), ("j30", f"1-{d1} j")] if echeance else [("j30", f"0-{d1} j")]) + [
        ("j60", f"{d1 + 1}-{d2} j"), ("j90", f"{d2 + 1}-{d3} j"), ("plus", f"> {d3} j")]
    cles = ["non_echu", "j30", "j60", "j90", "plus"]
    par_tiers = {}
    factures = Document.objects.filter(type_document=type_facture, statut=Document.VALIDE, date__lte=date_ref)
    if tiers:
        factures = factures.filter(Q(payeur_id=tiers) | Q(payeur__isnull=True, tiers_id=tiers))
    for doc in factures.select_related("tiers", "payeur"):
        reste = doc.reste_a_payer
        if reste <= 0:
            continue
        age = (date_ref - ((doc.date_echeance or doc.date) if echeance else doc.date)).days
        cle = ("non_echu" if echeance and age <= 0 else "j30" if age <= d1 else "j60" if age <= d2
               else "j90" if age <= d3 else "plus")
        payeur = doc.tiers_payeur                         # la dette est suivie chez le payeur
        ligne = par_tiers.setdefault(payeur.pk, {"tiers": payeur, "total": ZERO, **{k: ZERO for k in cles}})
        ligne[cle] += reste
        ligne["total"] += reste
    lignes = sorted(par_tiers.values(), key=lambda l: -l["total"])
    totaux = {k: sum((l[k] for l in lignes), ZERO) for k in cles + ["total"]}
    return {"tranches": tranches, "lignes": lignes, "totaux": totaux, "d_apres": D_APRES_ECHEANCE if echeance else D_APRES_ECRITURE,
            "delais": [d1, d2, d3]}


def tresorerie(date_fin):
    soldes = services.soldes_par_compte(date_fin)
    return sum((s for n, s in soldes.items() if n[:2] in ("52", "53", "55", "57")), ZERO) - \
        sum((-s for n, s in soldes.items() if n.startswith("56") and s < 0), ZERO)


def tableau_de_bord(exercice=None):
    debut, fin = _periode(exercice)
    today = datetime.date.today()
    fin_effective = min(fin, today) if debut <= today else fin
    mois_debut = today.replace(day=1)
    soldes = services.soldes_par_compte(fin_effective)
    creances = sum((s for n, s in soldes.items() if n.startswith("41")), ZERO)
    dettes = -sum((s for n, s in soldes.items() if n.startswith("40")), ZERO)
    cr = etats.compte_de_resultat(debut, fin_effective)
    return {
        "debut": debut,
        "fin": fin,
        "ca_exercice": chiffre_affaires(debut, fin),
        "ca_mois": chiffre_affaires(mois_debut, today),
        "achats_exercice": (_factures([Document.ACHAT_FACTURE], debut, fin).aggregate(s=Sum("total_ht"))["s"] or ZERO)
        - (_factures([Document.ACHAT_AVOIR, Document.ACHAT_FACTURE_RETOUR], debut, fin).aggregate(s=Sum("total_ht"))["s"] or ZERO),
        "creances_clients": creances,
        "dettes_fournisseurs": dettes,
        "tresorerie": tresorerie(fin_effective),
        "resultat": cr["resultat_net"],
        "marge_commerciale": cr["valeurs"]["XA"],
        "valeur_stock": sum((a.valeur_stock for a in Article.objects.filter(suivi_stock=True)), ZERO),
        "alertes_stock": [a for a in Article.objects.filter(suivi_stock=True, actif=True) if a.en_alerte],
        "ca_mensuel": ca_mensuel(debut, fin),
        "achats_mensuels": ca_mensuel(debut, fin, (Document.ACHAT_FACTURE,), (Document.ACHAT_AVOIR, Document.ACHAT_FACTURE_RETOUR)),
        "top_clients": top_clients(debut, fin),
        "top_articles": ventes_par_article(debut, fin, limite=5),
        "devis_en_cours": Document.objects.filter(type_document=Document.DEVIS, statut=Document.VALIDE).count(),
        "factures_impayees": sum(1 for d in Document.objects.filter(type_document=Document.FACTURE, statut=Document.VALIDE)
                                 if d.reste_a_payer > 0),
    }


# ---------------------------------------------------------------------------
# Rapport commercial journalier (rapport de caisse d'une agence)
# ---------------------------------------------------------------------------
def rapport_commercial(jour, journal=None):
    """Rapport du jour d'une caisse : ventes (factures et bons de commande), encaissements, versements hors
    recettes, sorties et dépenses, puis solde de caisse (ouverture, mouvements, clôture) rapproché du compte."""
    from apps.commercial.models import Imputation, OperationCaisse, Reglement
    from apps.comptabilite.models import Ecriture, Journal, LigneEcriture

    journal = journal or Journal.objects.filter(code="CA").first() or Journal.objects.filter(
        type_journal=Journal.TYPE_TRESORERIE).first()
    D = Document

    # 1. Ventes du jour : factures (comptant, payées d'avance, en compte) et bons de commande
    factures = []
    for f in (Document.objects.filter(type_document__in=(D.FACTURE, D.FACTURE_RETOUR, D.AVOIR), date=jour)
              .exclude(statut__in=(D.BROUILLON, D.ANNULE)).select_related("tiers").order_by("numero")):
        signe = -1 if f.est_avoir else 1
        # Photographie du jour du rapport : les règlements postérieurs ne modifient pas un rapport passé
        imputations = Imputation.objects.filter(document=f, reglement__date__lte=jour).select_related("reglement")
        acompte = sum((i.montant for i in imputations if i.reglement.commande_id and i.reglement.date < jour), ZERO)
        encaisse = sum((i.montant for i in imputations if i.reglement.date == jour), ZERO)
        reste = ZERO if f.est_avoir else f.total_ttc - sum((i.montant for i in imputations), ZERO)
        nature = ("Avoir" if f.est_avoir else "Comptant" if reste <= 0 and encaisse and not acompte
                  else "Payée d'avance" if reste <= 0 and acompte else "Comptant (partiel)" if encaisse else "En compte")
        if reste > 0 and f.tiers_id and not f.tiers_payeur.vente_credit:
            nature += " · client au comptant non soldé"
        factures.append({"doc": f, "ttc": signe * f.total_ttc, "acompte": acompte, "encaisse": encaisse,
                         "reste": reste, "nature": nature})
    commandes = []
    for c in (Document.objects.filter(type_document=D.COMMANDE, date=jour).exclude(statut=D.ANNULE)
              .select_related("tiers").order_by("numero")):
        avance = c.acomptes.filter(date__lte=jour).aggregate(s=Sum("montant"))["s"] or ZERO
        facture = c.facture_issue()
        if facture and facture.date > jour:                # facturée plus tard : pas encore au jour du rapport
            facture = None
        commandes.append({"doc": c, "ttc": c.total_ttc, "avance": avance,
                          "nature": "Payé d'avance" if avance >= c.total_ttc > 0 else "Acompte" if avance else "En compte",
                          "facture": facture, "facturee_jour": bool(facture and facture.date == jour)})
    ventes = {
        "factures": factures, "commandes": commandes,
        "total_factures": sum((l["ttc"] for l in factures), ZERO),
        "comptant": sum((l["ttc"] for l in factures if l["nature"] in ("Comptant", "Payée d'avance")), ZERO),
        "credit": sum((l["reste"] for l in factures), ZERO),
        "total_commandes": sum((l["ttc"] for l in commandes), ZERO),
        "avances_commandes": sum((l["avance"] for l in commandes), ZERO),
    }

    # 2. Encaissements du jour sur cette caisse
    encaissements = []
    for r in (Reglement.objects.filter(date=jour, journal=journal, tiers__type_tiers=Tiers.CLIENT)
              .select_related("tiers", "commande").order_by("numero")):
        docs = [i.document for i in r.imputations.select_related("document")]
        nature = ("Acompte sur commande" if r.commande_id else "Vente du jour" if docs and all(d.date == jour for d in docs)
                  else "Recouvrement de créance" if docs else "Avance (non imputée)")
        encaissements.append({"reglement": r, "nature": nature, "montant": r.montant})
    operations = OperationCaisse.objects.filter(date=jour, journal=journal).select_related("agence", "compte")
    hors_recettes = [o for o in operations if o.nature == OperationCaisse.HORS_RECETTE]
    autres_entrees = [o for o in operations if o.nature == OperationCaisse.AUTRE_ENTREE]

    # 3. Sorties du jour
    depenses = [o for o in operations if o.nature == OperationCaisse.DEPENSE]
    sorties_agences = [o for o in operations if o.nature == OperationCaisse.SORTIE_AGENCE]
    autres_sorties = [o for o in operations if o.nature == OperationCaisse.AUTRE_SORTIE]
    fournisseurs = list(Reglement.objects.filter(date=jour, journal=journal, tiers__type_tiers=Tiers.FOURNISSEUR)
                        .select_related("tiers").order_by("numero"))

    total = lambda objets, champ="montant": sum((getattr(o, champ) if not isinstance(o, dict) else o[champ] for o in objets), ZERO)
    entrees = total(encaissements) + total(hors_recettes) + total(autres_entrees)
    sorties = total(depenses) + total(sorties_agences) + total(autres_sorties) + total(fournisseurs)

    # 4. Solde de caisse, rapproché du compte de trésorerie
    solde = {"ouverture": ZERO, "entrees": entrees, "sorties": sorties, "cloture": entrees - sorties, "compte": None,
             "cloture_comptable": None, "ecart": ZERO}
    compte = journal.compte_tresorerie if journal else None
    if compte:
        lignes = LigneEcriture.objects.filter(compte=compte, ecriture__statut=Ecriture.STATUT_VALIDEE)
        avant = lignes.filter(ecriture__date__lt=jour).aggregate(d=Sum("debit"), c=Sum("credit"))
        ouverture = (avant["d"] or ZERO) - (avant["c"] or ZERO)
        jusqua = lignes.filter(ecriture__date__lte=jour).aggregate(d=Sum("debit"), c=Sum("credit"))
        cloture_comptable = (jusqua["d"] or ZERO) - (jusqua["c"] or ZERO)
        cloture = ouverture + entrees - sorties
        solde.update(ouverture=ouverture, cloture=cloture, compte=compte, cloture_comptable=cloture_comptable,
                     ecart=cloture_comptable - cloture)
    return {
        "jour": jour, "journal": journal, "ventes": ventes,
        "encaissements": encaissements, "total_encaissements": total(encaissements),
        "hors_recettes": hors_recettes, "total_hors_recettes": total(hors_recettes),
        "autres_entrees": autres_entrees, "total_autres_entrees": total(autres_entrees),
        "depenses": depenses, "total_depenses": total(depenses),
        "sorties_agences": sorties_agences, "total_sorties_agences": total(sorties_agences),
        "autres_sorties": autres_sorties, "total_autres_sorties": total(autres_sorties),
        "fournisseurs": fournisseurs, "total_fournisseurs": total(fournisseurs),
        "solde": solde,
        # Hors caisse : nos clients ont versé dans une autre agence (compte de liaison), créance soldée ici
        # Encaissements clients du jour sur les autres trésoreries (banque, Mobile Money) : hors caisse, séparés
        "autres_tresoreries": list(Reglement.objects.filter(date=jour, tiers__type_tiers=Tiers.CLIENT,
                                                            journal__type_journal=Journal.TYPE_TRESORERIE)
                                   .exclude(journal=journal).values("journal__code", "journal__intitule", "mode")
                                   .annotate(total=Sum("montant"), nombre=Count("id")).order_by("journal__code", "mode")),
        "recus_autres_agences": list(Reglement.objects.filter(date=jour, agence_encaissement__isnull=False)
                                     .select_related("tiers", "facture", "agence_encaissement").order_by("numero")),
    }
