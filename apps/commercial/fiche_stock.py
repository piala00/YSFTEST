"""Fiche de stock numérique du magasin : bons à pointer, écarts, rapprochement fiche / ordinateur, fiche d'un article.

Le fichiste pointe chaque bon qui fait bouger le stock en saisissant les quantités lues sur le bon papier. La « fiche »
est donc tenue avec ses quantités ; l'ordinateur garde les siennes. Le rapprochement compare les deux à tout moment.
"""
from decimal import Decimal

from .models import Document, LignePointage, MouvementStock, PointageFiche, StockDepot

ZERO = Decimal("0")


def trouver_bon(numero):
    """Bon saisi par le fichiste : numéro exact, sinon fin de numéro sans ambiguïté (« 00012 » pour BL2026-00012)."""
    numero = (numero or "").strip()
    if not numero:
        return None
    doc = Document.objects.filter(numero__iexact=numero).first()
    if doc is None:
        candidats = list(Document.objects.filter(numero__iendswith=numero)[:2])
        doc = candidats[0] if len(candidats) == 1 else None
    return doc


def bons_a_pointer(depot, debut, fin):
    """Bons qui ont fait bouger le stock du dépôt sur la période et que le fichiste n'a pas encore pointés."""
    pointes = PointageFiche.objects.filter(depot=depot).values_list("document_id", flat=True)
    ids = (MouvementStock.objects.filter(depot=depot, date__range=(debut, fin), document__isnull=False)
           .exclude(document_id__in=pointes).values_list("document_id", flat=True).distinct())
    return Document.objects.filter(pk__in=ids).select_related("tiers").order_by("date", "numero")


def ecarts(depot, debut, fin):
    """Lignes pointées dont la quantité du fichiste diffère de celle de l'ordinateur."""
    lignes = (LignePointage.objects.filter(pointage__depot=depot, pointage__document__date__range=(debut, fin))
              .select_related("pointage__document", "article"))
    return [l for l in lignes if l.ecart]


def _ecart_signe(pointage, ligne):
    """Effet de l'écart sur le stock de la fiche : une sortie notée en trop fait baisser la fiche."""
    return PointageFiche.sens(pointage.document, pointage.depot) * ligne.ecart


def rapprochement(depot, ecarts_seulement=True):
    """Par article : stock de l'ordinateur, cumul des écarts de pointage, stock de la fiche."""
    cumul = {}
    for pointage in PointageFiche.objects.filter(depot=depot).select_related("document").prefetch_related("lignes__article"):
        for ligne in pointage.lignes.all():
            if ligne.ecart:
                cumul[ligne.article] = cumul.get(ligne.article, ZERO) + _ecart_signe(pointage, ligne)
    lignes = []
    for stock in StockDepot.objects.filter(depot=depot).select_related("article").order_by("article__reference"):
        ecart = cumul.pop(stock.article, ZERO)
        if ecarts_seulement and not ecart:
            continue
        lignes.append({"article": stock.article, "machine": stock.quantite, "ecart": ecart, "fiche": stock.quantite + ecart})
    for article, ecart in cumul.items():                       # article sans ligne de stock dans ce dépôt
        lignes.append({"article": article, "machine": ZERO, "ecart": ecart, "fiche": ecart})
    return lignes


def fiche_article(article, depot, debut, fin):
    """Fiche de stock d'un article : chaque bon avec entrée / sortie et solde, tels que tenus par le fichiste
    (quantités pointées ; quantités de l'ordinateur pour les bons pas encore pointés, signalés)."""
    saisies = {(l.pointage.document_id): l for l in LignePointage.objects.filter(
        article=article, pointage__depot=depot).select_related("pointage")}
    par_bon = {}
    for m in (MouvementStock.objects.filter(article=article, depot=depot, date__lte=fin)
              .select_related("document").order_by("date", "id")):
        cle = m.document_id or f"m{m.pk}"
        ligne = par_bon.setdefault(cle, {"date": m.date, "document": m.document, "libelle": m.libelle, "machine": ZERO})
        ligne["machine"] += m.quantite
    solde_fiche = solde_machine = ZERO
    ouverture, lignes = None, []
    for ligne in par_bon.values():
        pointage = saisies.get(ligne["document"].pk) if ligne["document"] else None
        signe = 1 if ligne["machine"] >= 0 else -1
        fiche = signe * pointage.quantite_saisie if pointage else ligne["machine"]
        if ligne["date"] < debut:
            solde_fiche += fiche
            solde_machine += ligne["machine"]
            continue
        if ouverture is None:
            ouverture = {"fiche": solde_fiche, "machine": solde_machine}
        solde_fiche += fiche
        solde_machine += ligne["machine"]
        lignes.append({**ligne, "pointe": bool(pointage), "entree": fiche if fiche > 0 else ZERO,
                       "sortie": -fiche if fiche < 0 else ZERO, "solde": solde_fiche, "ecart": fiche - ligne["machine"]})
    if ouverture is None:
        ouverture = {"fiche": solde_fiche, "machine": solde_machine}
    return {"ouverture": ouverture, "lignes": lignes, "solde_fiche": solde_fiche, "solde_machine": solde_machine,
            "ecart": solde_fiche - solde_machine}
