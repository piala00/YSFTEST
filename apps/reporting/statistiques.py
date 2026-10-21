"""États et statistiques de la Gestion commerciale (menu Etat, découpage Sage 100 V12.10).

Chaque état est déclaré dans ETATS : titre, besoin d'une période, colonnes et fonction de calcul.
Types de colonnes : texte, date, entier, quantite, montant, pourcent.
Les colonnes « quantite » et « montant » sont totalisées.
"""
import datetime
from collections import OrderedDict, defaultdict
from decimal import Decimal

from apps.commercial.models import Article, Document, LigneDocument, Tiers

from .services import MOIS

ZERO = Decimal("0")
VALIDES = (Document.VALIDE, Document.TRANSFORME)
VENTES_PLUS, VENTES_MOINS = (Document.FACTURE,), (Document.FACTURE_RETOUR, Document.AVOIR)
ACHATS_PLUS, ACHATS_MOINS = (Document.ACHAT_FACTURE,), (Document.ACHAT_FACTURE_RETOUR, Document.ACHAT_AVOIR)


def _lignes(debut, fin, plus, moins):
    """Lignes de factures de la période, avec signe (+1 facture, -1 retour / avoir)."""
    qs = (LigneDocument.objects.filter(document__type_document__in=plus + moins, document__statut__in=VALIDES,
                                       document__date__gte=debut, document__date__lte=fin)
          .select_related("document", "document__tiers", "article", "article__famille"))
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
    docs = (Document.objects.filter(type_document__in=types, statut__in=VALIDES, date__gte=debut, date__lte=fin)
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
    docs = (Document.objects.filter(type_document__in=types, date__gte=debut, date__lte=fin)
            .exclude(statut=Document.ANNULE).select_related("tiers", "depot").order_by("type_document", "date", "numero"))
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
    for d in (Document.objects.filter(type_document=type_facture, statut=Document.VALIDE)
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
              for t in Tiers.objects.filter(type_tiers=type_tiers).order_by("code")]
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
              for a in Article.objects.select_related("famille").order_by("reference")]
    return colonnes, lignes


# code : (titre, période requise, fonction)
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
}


def calculer(code, debut, fin):
    titre, periode, fonction = ETATS[code]
    colonnes, lignes = fonction(debut, fin)
    totaux = {cle: sum((l.get(cle) or ZERO for l in lignes), ZERO)
              for cle, _, genre in colonnes if genre in ("montant", "quantite") and cle not in ("prix_moyen", "stock")}
    return {"titre": titre, "periode": periode, "colonnes": colonnes, "lignes": lignes, "totaux": totaux}
