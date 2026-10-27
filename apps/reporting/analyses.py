"""Reporting construit sur les états : comptabilité générale (écritures validées) et comptabilité analytique (le même
moteur que la Comptabilité analytique, apps.comptabilite.plan_analytique). Aucun montant n'est recalculé autrement :
un chiffre du reporting se retrouve, au franc près, dans l'état analytique ou général correspondant.
"""
import calendar
import datetime
from collections import OrderedDict
from decimal import Decimal

from django.db.models import Sum

from apps.comptabilite import plan_analytique as pa

ZERO = Decimal("0")
CRITERES = [("resultat", "Résultat"), ("produits", "Produits"), ("charges", "Charges"), ("marge", "Marge (%)")]
INDICATEURS = [("resultat", "Résultat"), ("produits", "Produits"), ("charges", "Charges")]


def mois_de(debut, fin, limite=36):
    """Premiers jours des mois de la période (au plus `limite`)."""
    mois, d = [], debut.replace(day=1)
    while d <= fin and len(mois) < limite:
        mois.append(d)
        d = (d.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return mois


def fin_de_mois(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def _marge(e):
    return round(100 * e["resultat"] / e["produits"]) if e["produits"] else None


# ---------------------------------------------------------------- Comptabilité générale
def evolution_societe(debut, fin):
    """Mois par mois : produits, charges, résultat (classes 7 et 6) et soldes de fin de mois de la trésorerie (5),
    des clients (411), des fournisseurs (401) et des propriétaires (467). Écritures validées seulement."""
    from apps.comptabilite.models import Ecriture, LigneEcriture

    validees = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE)

    def mouvement(d, f, prefixe):
        a = validees.filter(ecriture__date__range=(d, f), compte__numero__startswith=prefixe).aggregate(
            d=Sum("debit"), c=Sum("credit"))
        return (a["d"] or ZERO) - (a["c"] or ZERO)

    def solde(f, prefixe):
        a = validees.filter(ecriture__date__lte=f, compte__numero__startswith=prefixe).aggregate(d=Sum("debit"), c=Sum("credit"))
        return (a["d"] or ZERO) - (a["c"] or ZERO)

    lignes = []
    for m in mois_de(debut, fin):
        d, f = max(m, debut), min(fin_de_mois(m), fin)
        produits, charges = -mouvement(d, f, "7"), mouvement(d, f, "6")
        lignes.append({"mois": m, "produits": produits, "charges": charges, "resultat": produits - charges,
                       "tresorerie": solde(f, "5"), "clients": solde(f, "411"), "fournisseurs": -solde(f, "401"),
                       "proprietaires": -solde(f, "467")})
    total = {k: sum((l[k] for l in lignes), ZERO) for k in ("produits", "charges", "resultat")}
    return {"lignes": lignes, "total": total}


# ---------------------------------------------------------------- Comptabilité analytique
def comparaison_axe(axe, periode_a, periode_b):
    """Chaque élément d'un axe sur deux périodes : produits, charges, résultat, écart et variation."""
    a, b = pa.balance_axe(axe, *periode_a), pa.balance_axe(axe, *periode_b)
    vide = {"produits": ZERO, "charges": ZERO, "resultat": ZERO, "lignes": 0}
    par_cle = OrderedDict()
    for cote, bal in (("a", a), ("b", b)):
        for e in bal["elements"]:
            par_cle.setdefault(e["cle"], {"cle": e["cle"], "libelle": e["libelle"], "a": vide, "b": vide})[cote] = e
    lignes = []
    for g in par_cle.values():
        g["ecart"] = g["a"]["resultat"] - g["b"]["resultat"]
        g["variation"] = round(100 * g["ecart"] / abs(g["b"]["resultat"])) if g["b"]["resultat"] else None
        g["variation_produits"] = (round(100 * (g["a"]["produits"] - g["b"]["produits"]) / g["b"]["produits"])
                                   if g["b"]["produits"] else None)
        lignes.append(g)
    lignes.sort(key=lambda g: g["libelle"])
    return {"lignes": lignes, "total_a": a["total_elements"], "total_b": b["total_elements"],
            "non_affecte_a": a["non_affecte"], "non_affecte_b": b["non_affecte"], "gl_a": a["gl"], "gl_b": b["gl"],
            "rapproche": a["rapproche"] and b["rapproche"]}


def matrice_axe(axe, debut, fin, indicateur="resultat"):
    """Éléments × mois d'un indicateur (une seule lecture des écritures)."""
    mois = mois_de(debut, fin)
    cellules, totaux = {}, {m: ZERO for m in mois}
    for f in pa.faits(debut, fin):
        m = f["date"].replace(day=1)
        if m not in totaux:
            continue
        for cle, montant in pa.parts(f, axe):
            if indicateur == "produits" and not f["produit"]:
                continue
            if indicateur == "charges" and f["produit"]:
                continue
            valeur = montant if indicateur != "charges" else -montant
            cellules.setdefault(cle, {}).setdefault(m, ZERO)
            cellules[cle][m] += valeur
            totaux[m] += valeur
    noms = pa.libelles(axe, list(cellules))
    lignes = [{"cle": c, "libelle": noms.get(c, str(c)) if c is not None else "Non affecté",
               "valeurs": [v.get(m, ZERO) for m in mois], "total": sum(v.values(), ZERO)} for c, v in cellules.items()]
    lignes.sort(key=lambda l: (l["cle"] is None, l["libelle"]))
    return {"mois": mois, "lignes": lignes, "totaux": [totaux[m] for m in mois], "total": sum(totaux.values(), ZERO)}


def classement(axe, debut, fin, critere="resultat", nombre=10):
    """Les meilleurs et les moins bons éléments d'un axe (hors non affecté)."""
    elements = pa.balance_axe(axe, debut, fin)["elements"]
    for e in elements:
        e["marge"] = _marge(e)
    cle = (lambda e: (e["marge"] is not None, e["marge"] or 0)) if critere == "marge" else (lambda e: e[critere])
    tries = sorted(elements, key=cle, reverse=True)
    meilleurs = tries[:nombre]
    moins_bons = [e for e in reversed(tries) if e not in meilleurs][:nombre]
    return {"meilleurs": meilleurs, "moins_bons": moins_bons, "nombre_elements": len(elements)}


# ---------------------------------------------------------------- Catalogue
def catalogue():
    """Tous les états consultables, par famille : (famille, [(titre, nom d'URL, arguments, paramètres, description)])."""
    general = [
        ("Balance des comptes", "comptabilite:balance", (), {}, "Mouvements et soldes de chaque compte"),
        ("Grand-livre des comptes", "comptabilite:grand_livre", (), {}, "Chaque écriture de chaque compte"),
        ("Journal général", "comptabilite:journal", (), {}, "Écritures par journal"),
        ("Balance des tiers", "comptabilite:balance", (), {"compte_debut": "4", "compte_fin": "4"}, "Clients, fournisseurs, propriétaires"),
        ("Balance âgée et échéancier", "comptabilite:balance_agee", (), {"type": "CLIENT"}, "Créances par ancienneté"),
        ("Bilan", "comptabilite:bilan", (), {}, "Selon le système du dossier (normal ou SMT)"),
        ("Compte de résultat", "comptabilite:compte_resultat", (), {}, "Charges et produits de l'exercice"),
        ("Soldes intermédiaires de gestion", "comptabilite:compte_resultat", (), {"vue": "sig"}, "Marge, valeur ajoutée, EBE…"),
        ("Déclaration de TVA", "comptabilite:tva", (), {}, "Taxes collectées et déductibles"),
        ("Trésorerie projetée", "comptabilite:tresorerie_projetee", (), {}, "Échéances, prévisions et budget, mois par mois"),
    ]
    analytique = [("Plan analytique (tous les axes)", "analytique:plan", (), {}, "Ce qui est affecté à chaque axe et le non affecté")]
    analytique += [(f"Balance : {titre}", "analytique:axe", (code,), {}, desc) for code, titre, desc in pa.axes()]
    analytique += [
        ("Comptes d'exploitation des véhicules", "comptabilite:analytique_vehicules", (), {}, "Par rubrique, avec la part du propriétaire"),
        ("Portefeuilles des propriétaires", "comptabilite:analytique_proprietaires", (), {}, "Résultats et situation financière séparée"),
        ("Relevés des propriétaires", "comptabilite:analytique_releves", (), {}, "Compte du véhicule, règlements, retraits"),
        ("Balance analytique des sections", "comptabilite:balance_analytique", (), {}, "Plans de sections"),
        ("Budgets et budget / réel", "analytique:budgets", (), {}, "Par plan ou pour la société : écarts et réalisation"),
    ]
    reporting = [
        ("Évolution de la société", "reporting:evolution", (), {}, "Produits, charges, résultat, trésorerie, créances et dettes, mois par mois"),
        ("Comparaison de deux périodes", "reporting:comparaison", (), {}, "Sur n'importe quel axe : écart et variation"),
        ("Tableau mensuel par axe", "reporting:matrice", (), {}, "Chaque élément mois par mois"),
        ("Classements", "reporting:classement", (), {}, "Meilleurs et moins bons éléments"),
        ("Comparaisons du transport", "reporting:comparaisons_transport", (), {}, "Avec voyages, voyageurs et remplissage"),
        ("Tableau de bord", "reporting:dashboard", (), {}, "Indicateurs du moment"),
    ]
    return [("Comptabilité générale", general), ("Comptabilité analytique", analytique), ("Analyses du reporting", reporting)]
