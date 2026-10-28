"""États et statistiques de la Gestion commerciale (menu Etat, découpage Sage 100 V12.10).

Chaque état est déclaré dans ETATS : titre, besoin d'une période, colonnes et fonction de calcul.
Types de colonnes : texte, date, entier, quantite, montant, pourcent.
Les colonnes « quantite » et « montant » sont totalisées.
"""
import contextvars
import datetime
from collections import OrderedDict, defaultdict
from decimal import Decimal

from apps.commercial.models import Article, Document, LigneDocument, Tiers

from .services import MOIS

ZERO = Decimal("0")
VALIDES = (Document.VALIDE, Document.TRANSFORME)
VENTES_PLUS, VENTES_MOINS = (Document.FACTURE,), (Document.FACTURE_RETOUR, Document.AVOIR)
ACHATS_PLUS, ACHATS_MOINS = (Document.ACHAT_FACTURE,), (Document.ACHAT_FACTURE_RETOUR, Document.ACHAT_AVOIR)


# Critères de la fenêtre de sélection (tiers, dépôt, famille, article) de l'état en cours de calcul
_criteres = contextvars.ContextVar("criteres_etat", default={})


def _filtrer_documents(qs, prefixe=""):
    c = _criteres.get()
    if c.get("tiers"):
        qs = qs.filter(**{f"{prefixe}tiers_id": c["tiers"]})
    if c.get("depot"):
        qs = qs.filter(**{f"{prefixe}depot_id": c["depot"]})
    return qs


def _filtrer_articles(qs, sur_lignes=False):
    """Famille et article choisis : sur des lignes de documents (article__…) ou sur des articles."""
    c = _criteres.get()
    if c.get("famille"):
        qs = qs.filter(**{"article__famille_id" if sur_lignes else "famille_id": c["famille"]})
    if c.get("article"):
        qs = qs.filter(**{"article_id" if sur_lignes else "pk": c["article"]})
    return qs


def _lignes(debut, fin, plus, moins):
    """Lignes de factures de la période, avec signe (+1 facture, -1 retour / avoir)."""
    qs = (LigneDocument.objects.filter(document__type_document__in=plus + moins, document__statut__in=VALIDES,
                                       document__date__gte=debut, document__date__lte=fin)
          .select_related("document", "document__tiers", "article", "article__famille"))
    qs = _filtrer_articles(_filtrer_documents(qs, "document__"), sur_lignes=True)
    for ligne in qs:
        yield ligne, (-1 if ligne.document.type_document in moins else 1)


def _cout(ligne):
    article = ligne.article
    return ligne.quantite * (article.cout_unitaire if article else ZERO)


def _pourcent(part, total):
    return (part / total * 100) if total else ZERO


# ---------------------------------------------------------------------------
# Analyse et statistiques tiers
# ---------------------------------------------------------------------------
def _activite(debut, fin, plus, moins):
    mois = []
    courant = debut.replace(day=1)
    while courant <= fin:
        mois.append((courant.year, courant.month))
        courant = (courant.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    par_tiers = OrderedDict()
    for ligne, signe in _lignes(debut, fin, plus, moins):
        t = ligne.document.tiers
        row = par_tiers.setdefault(t.pk, {"tiers": t.nom, **{f"m{a}{m:02d}": ZERO for a, m in mois}, "total": ZERO})
        d = ligne.document.date
        row[f"m{d.year}{d.month:02d}"] += signe * ligne.montant_ht
        row["total"] += signe * ligne.montant_ht
    colonnes = [("tiers", "Tiers", "texte")] + [(f"m{a}{m:02d}", f"{MOIS[m - 1]} {a % 100:02d}", "montant") for a, m in mois] \
        + [("total", "Total HT", "montant")]
    return colonnes, sorted(par_tiers.values(), key=lambda r: -r["total"])


def activite_clients(debut, fin, **_):
    return _activite(debut, fin, VENTES_PLUS, VENTES_MOINS)


def activite_fournisseurs(debut, fin, **_):
    return _activite(debut, fin, ACHATS_PLUS, ACHATS_MOINS)


def rentabilite_clients(debut, fin, **_):
    par_tiers = {}
    for ligne, signe in _lignes(debut, fin, VENTES_PLUS, VENTES_MOINS):
        t = ligne.document.tiers
        row = par_tiers.setdefault(t.pk, {"code": t.code, "tiers": t.nom, "ca": ZERO, "cout": ZERO})
        row["ca"] += signe * ligne.montant_ht
        row["cout"] += signe * _cout(ligne)
    lignes = []
    for row in par_tiers.values():
        row["cout"] = round(row["cout"])
        row["marge"] = row["ca"] - row["cout"]
        row["taux"] = _pourcent(row["marge"], row["ca"])
        lignes.append(row)
    colonnes = [("code", "Code", "texte"), ("tiers", "Client", "texte"), ("ca", "CA HT", "montant"),
                ("cout", "Coût de revient (CMUP)", "montant"), ("marge", "Marge", "montant"), ("taux", "Taux de marge", "pourcent")]
    return colonnes, sorted(lignes, key=lambda r: -r["marge"])


def risque_clients(debut, fin, **_):
    today = datetime.date.today()
    lignes = []
    for t in Tiers.objects.filter(type_tiers=Tiers.CLIENT, actif=True):
        encours = echu = ZERO
        for doc in t.documents.filter(type_document=Document.FACTURE, statut=Document.VALIDE):
            reste = doc.reste_a_payer
            if reste > 0:
                encours += reste
                if (doc.date_echeance or doc.date) < today:
                    echu += reste
        depassement = encours - t.plafond_credit if t.plafond_credit and encours > t.plafond_credit else ZERO
        if encours or t.plafond_credit:
            lignes.append({"code": t.code, "tiers": t.nom, "plafond": t.plafond_credit, "encours": encours,
                           "echu": echu, "depassement": depassement, "solde": t.solde_comptable()})
    colonnes = [("code", "Code", "texte"), ("tiers", "Client", "texte"), ("plafond", "Plafond d'encours", "montant"),
                ("encours", "Encours (reste dû)", "montant"), ("echu", "Dont échu", "montant"),
                ("depassement", "Dépassement", "montant"), ("solde", "Solde comptable", "montant")]
    return colonnes, sorted(lignes, key=lambda r: (-r["depassement"], -r["echu"], -r["encours"]))


def _par_famille(debut, fin, plus, moins, avec_marge):
    par_famille = {}
    for ligne, signe in _lignes(debut, fin, plus, moins):
        famille = ligne.article.famille.libelle if ligne.article and ligne.article.famille else "(sans famille)"
        row = par_famille.setdefault(famille, {"famille": famille, "quantite": ZERO, "montant": ZERO, "cout": ZERO})
        row["quantite"] += signe * ligne.quantite
        row["montant"] += signe * ligne.montant_ht
        row["cout"] += signe * _cout(ligne)
    total = sum((r["montant"] for r in par_famille.values()), ZERO)
    lignes = []
    for row in par_famille.values():
        row["part"] = _pourcent(row["montant"], total)
        row["marge"] = row["montant"] - round(row["cout"])
        row["taux"] = _pourcent(row["marge"], row["montant"])
        lignes.append(row)
    colonnes = [("famille", "Famille", "texte"), ("quantite", "Quantité", "quantite"), ("montant", "Montant HT", "montant"),
                ("part", "Part", "pourcent")]
    if avec_marge:
        colonnes += [("marge", "Marge (CMUP)", "montant"), ("taux", "Taux de marge", "pourcent")]
    return colonnes, sorted(lignes, key=lambda r: -r["montant"])


def ventes_familles(debut, fin, **_):
    return _par_famille(debut, fin, VENTES_PLUS, VENTES_MOINS, True)


def achats_familles(debut, fin, **_):
    return _par_famille(debut, fin, ACHATS_PLUS, ACHATS_MOINS, False)


def _par_article(debut, fin, plus, moins, avec_marge, palmares=False):
    par_article = {}
    for ligne, signe in _lignes(debut, fin, plus, moins):
        cle = ligne.article_id or ligne.designation
        row = par_article.setdefault(cle, {
            "reference": ligne.article.reference if ligne.article else "", "designation": ligne.designation,
            "famille": ligne.article.famille.libelle if ligne.article and ligne.article.famille else "",
            "quantite": ZERO, "montant": ZERO, "cout": ZERO,
            "stock": ligne.article.stock if ligne.article and ligne.article.suivi_stock else None})
        row["quantite"] += signe * ligne.quantite
        row["montant"] += signe * ligne.montant_ht
        row["cout"] += signe * _cout(ligne)
    lignes = sorted(par_article.values(), key=lambda r: -r["montant"])
    total = sum((r["montant"] for r in lignes), ZERO)
    cumul = ZERO
    for rang, row in enumerate(lignes, 1):
        row["marge"] = row["montant"] - round(row["cout"])
        row["taux"] = _pourcent(row["marge"], row["montant"])
        row["prix_moyen"] = (row["montant"] / row["quantite"]) if row["quantite"] else ZERO
        cumul += row["montant"]
        row.update(rang=rang, part=_pourcent(row["montant"], total), cumul=_pourcent(cumul, total))
    if palmares:
        colonnes = [("rang", "Rang", "entier"), ("reference", "Référence", "texte"), ("designation", "Désignation", "texte"),
                    ("quantite", "Quantité", "quantite"), ("montant", "CA HT", "montant"), ("part", "Part", "pourcent"),
                    ("cumul", "Cumul", "pourcent")]
        return colonnes, lignes
    colonnes = [("reference", "Référence", "texte"), ("designation", "Désignation", "texte"), ("famille", "Famille", "texte"),
                ("quantite", "Quantité", "quantite"), ("prix_moyen", "Prix moyen HT", "montant"), ("montant", "Montant HT", "montant")]
    if avec_marge:
        colonnes += [("marge", "Marge (CMUP)", "montant"), ("taux", "Taux de marge", "pourcent"), ("stock", "Stock actuel", "quantite")]
    return colonnes, lignes


def ventes_articles(debut, fin, **_):
    return _par_article(debut, fin, VENTES_PLUS, VENTES_MOINS, True)


def achats_articles(debut, fin, **_):
    return _par_article(debut, fin, ACHATS_PLUS, ACHATS_MOINS, False)


def palmares_ventes(debut, fin, **_):
    return _par_article(debut, fin, VENTES_PLUS, VENTES_MOINS, True, palmares=True)


def _palmares_tiers(debut, fin, plus, moins, libelle):
    par_tiers = {}
    for ligne, signe in _lignes(debut, fin, plus, moins):
        t = ligne.document.tiers
        row = par_tiers.setdefault(t.pk, {"code": t.code, "tiers": t.nom, "ville": t.ville, "montant": ZERO, "factures": set()})
        row["montant"] += signe * ligne.montant_ht
        if signe > 0:
            row["factures"].add(ligne.document_id)
    lignes = sorted(par_tiers.values(), key=lambda r: -r["montant"])
    total = sum((r["montant"] for r in lignes), ZERO)
    cumul = ZERO
    for rang, row in enumerate(lignes, 1):
        cumul += row["montant"]
        row.update(rang=rang, nb=len(row.pop("factures")), part=_pourcent(row["montant"], total), cumul=_pourcent(cumul, total))
    colonnes = [("rang", "Rang", "entier"), ("code", "Code", "texte"), ("tiers", libelle, "texte"), ("ville", "Ville", "texte"),
                ("nb", "Factures", "entier"), ("montant", "Montant HT", "montant"), ("part", "Part", "pourcent"), ("cumul", "Cumul", "pourcent")]
    return colonnes, lignes


def palmares_clients(debut, fin, **_):
    return _palmares_tiers(debut, fin, VENTES_PLUS, VENTES_MOINS, "Client")


def ca_fournisseurs(debut, fin, **_):
    return _palmares_tiers(debut, fin, ACHATS_PLUS, ACHATS_MOINS, "Fournisseur")


# ---------------------------------------------------------------------------
# Relevés, échéances et listes
# ---------------------------------------------------------------------------
def _releve_factures(debut, fin, types):
    lignes = []
    docs = _filtrer_documents(Document.objects.filter(type_document__in=types, statut__in=VALIDES, date__gte=debut, date__lte=fin)
                              .select_related("tiers").order_by("tiers__nom", "date", "numero"))
    for d in docs:
        signe = -1 if d.est_avoir else 1
        lignes.append({"tiers": d.tiers.nom, "numero": d.numero, "type": d.get_type_document_display(), "date": d.date,
                       "echeance": d.date_echeance, "ttc": signe * d.total_ttc, "regle": d.montant_regle,
                       "reste": d.reste_a_payer, "lien": f"/commercial/document/{d.pk}/"})
    colonnes = [("tiers", "Tiers", "texte"), ("numero", "N° pièce", "texte"), ("type", "Type", "texte"), ("date", "Date", "date"),
                ("echeance", "Échéance", "date"), ("ttc", "Montant TTC", "montant"), ("regle", "Réglé", "montant"), ("reste", "Reste dû", "montant")]
    return colonnes, lignes


def releve_factures_clients(debut, fin, **_):
    return _releve_factures(debut, fin, VENTES_PLUS + VENTES_MOINS)


def releve_factures_fournisseurs(debut, fin, **_):
    return _releve_factures(debut, fin, ACHATS_PLUS + ACHATS_MOINS)


def _liste_documents(debut, fin, types):
    docs = _filtrer_documents(Document.objects.filter(type_document__in=types, date__gte=debut, date__lte=fin)
                              .exclude(statut=Document.ANNULE).select_related("tiers", "depot")
                              .order_by("type_document", "date", "numero"))
    lignes = [{"numero": d.numero_affiche, "type": d.get_type_document_display(), "date": d.date,
               "tiers": d.tiers.nom if d.tiers_id else "", "depot": str(d.depot or ""), "ht": d.total_ht, "ttc": d.total_ttc,
               "statut": d.get_statut_display(), "lien": f"/commercial/document/{d.pk}/"} for d in docs]
    colonnes = [("numero", "N° pièce", "texte"), ("type", "Type", "texte"), ("date", "Date", "date"), ("tiers", "Tiers", "texte"),
                ("depot", "Dépôt", "texte"), ("ht", "Total HT", "montant"), ("ttc", "Total TTC", "montant"), ("statut", "Statut", "texte")]
    return colonnes, lignes


def liste_documents_ventes(debut, fin, **_):
    return _liste_documents(debut, fin, Document.TYPES_VENTE)


def liste_documents_achats(debut, fin, **_):
    return _liste_documents(debut, fin, Document.TYPES_ACHAT)


def _echeances(type_facture):
    today = datetime.date.today()
    lignes = []
    for d in _filtrer_documents(Document.objects.filter(type_document=type_facture, statut=Document.VALIDE)
                                .select_related("tiers").order_by("date_echeance", "numero")):
        reste = d.reste_a_payer
        if reste <= 0:
            continue
        echeance = d.date_echeance or d.date
        lignes.append({"tiers": d.tiers.nom, "numero": d.numero, "date": d.date, "echeance": echeance,
                       "retard": max((today - echeance).days, 0), "ttc": d.total_ttc, "reste": reste,
                       "lien": f"/commercial/document/{d.pk}/"})
    colonnes = [("echeance", "Échéance", "date"), ("tiers", "Tiers", "texte"), ("numero", "N° facture", "texte"),
                ("date", "Date", "date"), ("retard", "Retard (jours)", "entier"), ("ttc", "Montant TTC", "montant"),
                ("reste", "Reste dû", "montant")]
    return colonnes, lignes


def echeances_clients(debut, fin, **_):
    return _echeances(Document.FACTURE)


def echeances_fournisseurs(debut, fin, **_):
    return _echeances(Document.ACHAT_FACTURE)


def _liste_tiers(type_tiers):
    colonnes = [("code", "Code", "texte"), ("nom", "Nom", "texte"), ("ville", "Ville", "texte"), ("telephone", "Téléphone", "texte"),
                ("email", "E-mail", "texte"), ("niu", "NIU", "texte"), ("rccm", "RCCM", "texte"), ("delai", "Délai (j)", "entier")]
    lignes = [{"code": t.code, "nom": t.nom, "ville": t.ville, "telephone": t.telephone, "email": t.email, "niu": t.niu,
               "rccm": t.rccm, "delai": t.delai_paiement, "lien": f"/commercial/tiers/{t.pk}/"}
              for t in Tiers.objects.filter(type_tiers=type_tiers).order_by("code")
              if not _criteres.get().get("tiers") or str(t.pk) == str(_criteres.get()["tiers"])]
    return colonnes, lignes


def liste_clients(debut, fin, **_):
    return _liste_tiers(Tiers.CLIENT)


def liste_fournisseurs(debut, fin, **_):
    return _liste_tiers(Tiers.FOURNISSEUR)


def liste_articles(debut, fin, **_):
    colonnes = [("reference", "Référence", "texte"), ("designation", "Désignation", "texte"), ("famille", "Famille", "texte"),
                ("nature", "Nature", "texte"), ("unite", "Unité", "texte"), ("prix_achat", "Prix d'achat HT", "montant"),
                ("prix_vente", "Prix de vente HT", "montant"), ("tva", "TVA", "pourcent"), ("stock", "Stock", "quantite")]
    lignes = [{"reference": a.reference, "designation": a.designation, "famille": a.famille.libelle if a.famille else "",
               "nature": a.get_nature_display(), "unite": a.unite, "prix_achat": a.prix_achat, "prix_vente": a.prix_vente,
               "tva": a.taux_tva, "stock": a.stock if a.suivi_stock else None, "lien": f"/commercial/articles/{a.pk}/"}
              for a in _filtrer_articles(Article.objects.select_related("famille").order_by("reference"))]
    return colonnes, lignes


# code : (titre, période requise, fonction)
# ---------------------------------------------------------------------------
# Stocks et retours (compléments au découpage Sage : audit du reporting)
# ---------------------------------------------------------------------------
def rotation_stocks(debut, fin, **_):
    """Par article suivi en stock : stock au début et à la fin, entrées, sorties, rotation (sorties / stock moyen),
    couverture (jours de sorties que le stock final permet) et alerte de rupture. Sans dépôt choisi, les transferts
    entre dépôts ne comptent ni en entrée ni en sortie."""
    from django.db.models import Q, Sum

    from apps.commercial.models import MouvementStock

    c = _criteres.get()
    mouvements = MouvementStock.objects.filter(date__lte=fin, article__suivi_stock=True)
    if c.get("depot"):
        mouvements = mouvements.filter(depot_id=c["depot"])
    else:
        mouvements = mouvements.exclude(document__type_document=Document.STOCK_VIREMENT)
    mouvements = _filtrer_articles(mouvements, sur_lignes=True)
    periode = Q(date__gte=debut)
    totaux = {r["article"]: r for r in mouvements.values("article").annotate(
        avant=Sum("quantite", filter=Q(date__lt=debut)),
        entrees=Sum("quantite", filter=periode & Q(quantite__gt=0)),
        sorties=Sum("quantite", filter=periode & Q(quantite__lt=0)))}
    jours = (fin - debut).days + 1
    lignes = []
    for article in Article.objects.filter(pk__in=totaux).order_by("reference"):
        t = totaux[article.pk]
        avant, entrees, sorties = t["avant"] or ZERO, t["entrees"] or ZERO, -(t["sorties"] or ZERO)
        apres = avant + entrees - sorties
        moyen = (avant + apres) / 2
        rotation = sorties / moyen if moyen > 0 else None
        couverture = int(apres / (sorties / jours)) if sorties > 0 and apres > 0 else None
        alerte = "Rupture" if apres <= 0 else ("Sous le stock d'alerte" if article.stock_minimum and apres <= article.stock_minimum
                                              else ("Sans sortie" if not sorties else ""))
        lignes.append({"reference": article.reference, "designation": article.designation, "debut": avant,
                       "entrees": entrees, "sorties": sorties, "fin_stock": apres,
                       "rotation": f"{rotation:.1f}".replace(".", ",") if rotation is not None else "—",
                       "couverture": couverture, "alerte": alerte, "lien": f"/commercial/articles/{article.pk}/"})
    lignes.sort(key=lambda l: ({"Rupture": 0, "Sous le stock d'alerte": 1}.get(l["alerte"], 2), l["reference"]))
    colonnes = [("reference", "Référence", "texte"), ("designation", "Désignation", "texte"),
                ("debut", "Stock début", "quantite"), ("entrees", "Entrées", "quantite"), ("sorties", "Sorties", "quantite"),
                ("fin_stock", "Stock fin", "quantite"), ("rotation", "Rotation", "texte"),
                ("couverture", "Couverture (jours)", "entier"), ("alerte", "Alerte", "texte")]
    return colonnes, lignes


def avoirs_retours(debut, fin, **_):
    """Factures de retour et d'avoir clients de la période, rapprochées de la pièce d'origine et du chiffre d'affaires."""
    docs = _filtrer_documents(Document.objects.filter(type_document__in=VENTES_MOINS, statut__in=VALIDES,
                                                      date__gte=debut, date__lte=fin)
                              .select_related("tiers", "origine").order_by("date", "numero"))
    ca = sum((l.montant_ht * signe for l, signe in _lignes(debut, fin, VENTES_PLUS, ())), ZERO)
    lignes = [{"date": d.date, "numero": d.numero_affiche, "type": d.get_type_document_display(),
               "tiers": d.tiers.nom if d.tiers_id else "", "origine": d.origine.numero if d.origine_id else "",
               "ht": d.total_ht, "ttc": d.total_ttc, "part": _pourcent(d.total_ht, ca),
               "lien": f"/commercial/document/{d.pk}/"} for d in docs]
    colonnes = [("date", "Date", "date"), ("numero", "N° pièce", "texte"), ("type", "Type", "texte"), ("tiers", "Client", "texte"),
                ("origine", "Pièce d'origine", "texte"), ("ht", "Montant HT", "montant"), ("ttc", "Montant TTC", "montant"),
                ("part", "Part du CA facturé", "pourcent")]
    return colonnes, lignes


def reglements_modes(debut, fin, **_):
    """Encaissements (clients) et décaissements (fournisseurs) de la période par mode de paiement."""
    from apps.commercial.models import Reglement

    qs = _filtrer_documents(Reglement.objects.filter(date__gte=debut, date__lte=fin).select_related("tiers"))
    par_mode = {code: {"mode": libelle, "nb": 0, "encaisse": ZERO, "decaisse": ZERO} for code, libelle in Reglement.MODES}
    for r in qs:
        ligne = par_mode.setdefault(r.mode, {"mode": r.get_mode_display(), "nb": 0, "encaisse": ZERO, "decaisse": ZERO})
        ligne["nb"] += 1
        ligne["encaisse" if r.est_encaissement else "decaisse"] += r.montant
    total = sum((l["encaisse"] for l in par_mode.values()), ZERO)
    lignes = [{**l, "net": l["encaisse"] - l["decaisse"], "part": _pourcent(l["encaisse"], total)}
              for l in par_mode.values() if l["nb"]]
    colonnes = [("mode", "Mode de paiement", "texte"), ("nb", "Nombre", "entier"), ("encaisse", "Encaissé (clients)", "montant"),
                ("decaisse", "Décaissé (fournisseurs)", "montant"), ("net", "Net", "montant"),
                ("part", "Part des encaissements", "pourcent")]
    return colonnes, sorted(lignes, key=lambda l: -l["encaisse"])


def _mois_de(debut, fin):
    """Liste des (année, mois) de la période, bornée à 36 mois pour garder le tableau lisible."""
    mois, y, m = [], debut.year, debut.month
    while (y, m) <= (fin.year, fin.month) and len(mois) < 36:
        mois.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return mois


def _cadencier(debut, fin, plus, moins):
    """Quantités par article (lignes) et par mois (colonnes) : rythme des ventes/achats/livraisons."""
    mois = _mois_de(debut, fin)
    cols_mois = {f"m{y}_{m}": ZERO for (y, m) in mois}
    par_article = {}
    for ligne, signe in _lignes(debut, fin, plus, moins):
        cle = ligne.article_id or ligne.designation
        row = par_article.setdefault(cle, {
            "reference": ligne.article.reference if ligne.article else "",
            "designation": ligne.designation or (ligne.article.designation if ligne.article else ""),
            **dict(cols_mois), "total": ZERO})
        d = ligne.document.date
        q = signe * ligne.quantite
        cle_mois = f"m{d.year}_{d.month}"
        if cle_mois in row:                                       # toujours vrai (document dans la période)
            row[cle_mois] += q
        row["total"] += q
    lignes = sorted(par_article.values(), key=lambda r: -r["total"])
    colonnes = ([("reference", "Référence", "texte"), ("designation", "Désignation", "texte")]
                + [(f"m{y}_{m}", f"{m:02d}/{str(y)[2:]}", "quantite") for (y, m) in mois]
                + [("total", "Total", "quantite")])
    return colonnes, lignes


def cadencier_clients(debut, fin, **_):
    return _cadencier(debut, fin, VENTES_PLUS, VENTES_MOINS)


def cadencier_fournisseurs(debut, fin, **_):
    return _cadencier(debut, fin, ACHATS_PLUS, ACHATS_MOINS)


def cadencier_livraison(debut, fin, **_):
    return _cadencier(debut, fin, (Document.LIVRAISON,), (Document.RETOUR,))


ETATS = {
    "activite_clients": ("Activité clients", True, activite_clients),
    "rentabilite_clients": ("Rentabilité clients", True, rentabilite_clients),
    "risque_clients": ("Risque clients", False, risque_clients),
    "ventes_familles": ("Statistiques clients par familles d'articles", True, ventes_familles),
    "ventes_articles": ("Statistiques clients par articles", True, ventes_articles),
    "palmares_clients": ("Palmarès des clients", True, palmares_clients),
    "activite_fournisseurs": ("Activité fournisseurs", True, activite_fournisseurs),
    "ca_fournisseurs": ("Chiffre d'affaires fournisseurs", True, ca_fournisseurs),
    "achats_familles": ("Statistiques fournisseurs par familles d'articles", True, achats_familles),
    "achats_articles": ("Statistiques fournisseurs par articles", True, achats_articles),
    "articles": ("Statistiques articles", True, ventes_articles),
    "familles": ("Statistiques familles", True, ventes_familles),
    "palmares_ventes": ("Palmarès des ventes", True, palmares_ventes),
    "releve_factures_clients": ("Relevé de factures clients", True, releve_factures_clients),
    "releve_factures_fournisseurs": ("Relevé de factures fournisseurs", True, releve_factures_fournisseurs),
    "liste_documents_ventes": ("Liste des documents de vente", True, liste_documents_ventes),
    "liste_documents_achats": ("Liste des documents d'achat", True, liste_documents_achats),
    "echeances_clients": ("Relevé d'échéances clients", False, echeances_clients),
    "echeances_fournisseurs": ("Relevé d'échéances fournisseurs", False, echeances_fournisseurs),
    "liste_clients": ("Liste des clients", False, liste_clients),
    "liste_fournisseurs": ("Liste des fournisseurs", False, liste_fournisseurs),
    "liste_articles": ("Liste des articles", False, liste_articles),
    "rotation_stocks": ("Rotation des stocks et ruptures", True, rotation_stocks),
    "avoirs_retours": ("Avoirs et retours clients", True, avoirs_retours),
    "reglements_modes": ("Règlements par mode de paiement", True, reglements_modes),
    "cadencier_clients": ("Cadencier clients (quantités vendues par mois)", True, cadencier_clients),
    "cadencier_fournisseurs": ("Cadencier fournisseurs (quantités achetées par mois)", True, cadencier_fournisseurs),
    "cadencier_livraison": ("Cadencier de livraison (quantités livrées par mois)", True, cadencier_livraison),
}


def calculer(code, debut, fin, **criteres):
    """Calcule un état ; `criteres` : tiers, depot, famille, article (identifiants) de la fenêtre de sélection."""
    titre, periode, fonction = ETATS[code]
    jeton = _criteres.set({k: v for k, v in criteres.items() if v})
    try:
        colonnes, lignes = fonction(debut, fin)
    finally:
        _criteres.reset(jeton)
    totaux = {cle: sum((l.get(cle) or ZERO for l in lignes), ZERO)
              for cle, _, genre in colonnes if genre in ("montant", "quantite") and cle not in ("prix_moyen", "stock")}
    return {"titre": titre, "periode": periode, "colonnes": colonnes, "lignes": lignes, "totaux": totaux}
