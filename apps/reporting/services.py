"""Indicateurs de pilotage : chiffre d'affaires, créances, trésorerie, marges."""
import datetime
from decimal import Decimal

from django.db.models import F, Sum
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


def balance_agee(type_tiers=Tiers.CLIENT, date_ref=None, tiers=None):
    """Factures non soldées, émises au plus tard à la date de situation, réparties par ancienneté de l'échéance."""
    date_ref = date_ref or datetime.date.today()
    type_facture = Document.FACTURE if type_tiers == Tiers.CLIENT else Document.ACHAT_FACTURE
    tranches = [("non_echu", "Non échu"), ("j30", "1-30 j"), ("j60", "31-60 j"), ("j90", "61-90 j"), ("plus", "> 90 j")]
    par_tiers = {}
    factures = Document.objects.filter(type_document=type_facture, statut=Document.VALIDE, date__lte=date_ref)
    if tiers:
        factures = factures.filter(tiers_id=tiers)
    for doc in factures.select_related("tiers"):
        reste = doc.reste_a_payer
        if reste <= 0:
            continue
        retard = (date_ref - (doc.date_echeance or doc.date)).days
        cle = "non_echu" if retard <= 0 else "j30" if retard <= 30 else "j60" if retard <= 60 else "j90" if retard <= 90 else "plus"
        ligne = par_tiers.setdefault(doc.tiers_id, {"tiers": doc.tiers, "total": ZERO, **{k: ZERO for k, _ in tranches}})
        ligne[cle] += reste
        ligne["total"] += reste
    lignes = sorted(par_tiers.values(), key=lambda l: -l["total"])
    totaux = {k: sum(l[k] for l in lignes) for k, _ in tranches + [("total", "")]}
    return {"tranches": tranches, "lignes": lignes, "totaux": totaux}


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
