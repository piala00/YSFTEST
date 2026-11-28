"""Budgets et état budget / réel.

Le réel vient du même moteur que la comptabilité analytique (écritures générales validées, classes 6 et 7) : un montant
réel se retrouve au franc près dans la balance analytique ou générale. Le budget est saisi par mois de l'exercice ;
sur une période, on retient les mois entiers qu'elle couvre. Montants positifs : produits (7) et charges (6).
Écart = réel − budget ; il est favorable si les produits dépassent le budget ou si les charges restent en dessous.
Ce qui n'est prévu par aucune ligne apparaît en « hors budget » : rien n'est perdu.
"""
import datetime
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from . import plan_analytique as pa
from .models import LigneBudget

ZERO = Decimal("0")


def mois_exercice(exercice):
    """Premiers jours des mois de l'exercice (12 au plus : colonnes m01…m12)."""
    mois, d = [], exercice.date_debut.replace(day=1)
    while d <= exercice.date_fin and len(mois) < 12:
        mois.append(d)
        d = (d.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return mois


def verifier_ligne(budget, element, compte, exclure=None):
    compte = (compte or "").strip()
    if not compte.isdigit() or compte[0] not in "67":
        raise ValidationError("Le compte doit être un compte (ou une racine) de charges 6 ou de produits 7.")
    if budget.axe and not element:
        raise ValidationError("Choisissez l'élément du plan analytique.")
    autres = budget.lignes.filter(element=element or "").exclude(pk=exclure)
    for l in autres:
        if l.compte.startswith(compte) or compte.startswith(l.compte):
            raise ValidationError(f"Le compte {compte} recoupe la ligne {l.compte} déjà budgétée pour cet élément "
                                  "(le réel serait compté deux fois).")
    return compte


def repartir(montant_annuel, nb_mois=12):
    """Montant annuel réparti par mois, au franc près (le dernier mois prend l'arrondi)."""
    montant = Decimal(str(montant_annuel or 0))
    part = (montant / nb_mois).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return [part] * (nb_mois - 1) + [montant - part * (nb_mois - 1)]


def _cle(valeur):
    return "" if valeur is None else str(valeur)


def _indices_mois(budget, debut, fin):
    """Rangs (0…11) des mois de l'exercice entièrement ou partiellement couverts par la période."""
    return [i for i, m in enumerate(mois_exercice(budget.exercice)) if debut.replace(day=1) <= m <= fin]


def rapport(budget, debut, fin):
    """Budget / réel de chaque ligne, sous-totaux par élément, total, et réel hors budget."""
    indices = _indices_mois(budget, debut, fin)
    lignes = list(budget.lignes.all())
    par_element = {}
    for l in lignes:
        par_element.setdefault(l.element, []).append(l)
    for ls in par_element.values():
        ls.sort(key=lambda l: -len(l.compte))                     # la racine la plus précise d'abord
    reel = {l.pk: ZERO for l in lignes}
    hors = OrderedDict()
    for f in pa.faits(debut, fin):
        for cle, montant in (pa.parts(f, budget.axe) if budget.axe else [(None, f["montant"])]):
            element = _cle(cle) if budget.axe else ""
            valeur = montant if f["produit"] else -montant
            ligne = next((l for l in par_element.get(element, []) if f["compte"].startswith(l.compte)), None)
            if ligne is not None:
                reel[ligne.pk] += valeur
            else:
                hors.setdefault((element, f["compte"][:2]), ZERO)
                hors[(element, f["compte"][:2])] += valeur
    noms = pa.libelles(budget.axe, [pa.cle_depuis_url(budget.axe, e) for e in par_element if e]) if budget.axe else {}
    nom = (lambda e: noms.get(pa.cle_depuis_url(budget.axe, e), e) if e else ("Non affecté" if budget.axe else "Société"))

    def ligne_rapport(element, compte, libelle, prevu, realise, produit):
        ecart = realise - prevu
        return {"element": element, "element_nom": nom(element), "compte": compte, "libelle": libelle, "produit": produit,
                "budget": prevu, "reel": realise, "ecart": ecart,
                "taux": round(100 * realise / prevu) if prevu else None,
                "favorable": (ecart >= 0) if produit else (ecart <= 0)}

    sortie = [ligne_rapport(l.element, l.compte, l.libelle, sum((l.mois[i] for i in indices), ZERO), reel[l.pk], l.produit)
              for l in lignes]
    hors_budget = [ligne_rapport(e, racine, "Hors budget", ZERO, v, racine.startswith("7"))
                   for (e, racine), v in hors.items() if v]
    elements = OrderedDict()
    for r in sortie + hors_budget:
        g = elements.setdefault(r["element"], {"element": r["element"], "element_nom": r["element_nom"],
                                               "budget_produits": ZERO, "reel_produits": ZERO,
                                               "budget_charges": ZERO, "reel_charges": ZERO})
        sens = "produits" if r["produit"] else "charges"
        g[f"budget_{sens}"] += r["budget"]
        g[f"reel_{sens}"] += r["reel"]
    for g in elements.values():
        g["budget_resultat"] = g["budget_produits"] - g["budget_charges"]
        g["reel_resultat"] = g["reel_produits"] - g["reel_charges"]
        g["ecart_resultat"] = g["reel_resultat"] - g["budget_resultat"]
    total = {k: sum((g[k] for g in elements.values()), ZERO)
             for k in ("budget_produits", "reel_produits", "budget_charges", "reel_charges", "budget_resultat",
                       "reel_resultat", "ecart_resultat")}
    return {"lignes": sortie, "hors_budget": hors_budget, "elements": sorted(elements.values(), key=lambda g: g["element_nom"]),
            "total": total, "mois": [mois_exercice(budget.exercice)[i] for i in indices]}


def preremplir(budget, exercice_reference, hausse_pct=0):
    """Crée les lignes manquantes à partir du réel d'un autre exercice (par élément et racine à 2 chiffres),
    mois par mois, augmenté de hausse_pct %. Ne modifie jamais une ligne existante. Renvoie le nombre de lignes créées."""
    coef = 1 + Decimal(str(hausse_pct or 0)) / 100
    debut, fin = exercice_reference.date_debut, exercice_reference.date_fin
    mois_ref = mois_exercice(exercice_reference)
    cumuls = OrderedDict()
    for f in pa.faits(debut, fin):
        rang = next((i for i, m in reversed(list(enumerate(mois_ref))) if f["date"] >= m), 0)
        for cle, montant in (pa.parts(f, budget.axe) if budget.axe else [(None, f["montant"])]):
            if budget.axe and cle is None:
                continue
            cle_l = (_cle(cle) if budget.axe else "", f["compte"][:2])
            cumuls.setdefault(cle_l, [ZERO] * 12)
            cumuls[cle_l][rang] += montant if f["produit"] else -montant
    existantes = {(l.element, l.compte) for l in budget.lignes.all()}
    creees = 0
    for (element, racine), valeurs in cumuls.items():
        if (element, racine) in existantes or any(e == element and (c.startswith(racine) or racine.startswith(c))
                                                  for e, c in existantes):
            continue
        l = LigneBudget(budget=budget, element=element, compte=racine, libelle="Réel " + exercice_reference.code)
        for i, v in enumerate(valeurs):
            setattr(l, LigneBudget.MOIS[i], (v * coef).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        l.save()
        creees += 1
    return creees


def elements_proposes(axe, exercice):
    """Éléments du plan à proposer à la saisie : ceux mouvementés sur l'exercice et le précédent."""
    if not axe:
        return []
    debut = exercice.date_debut.replace(year=exercice.date_debut.year - 1)
    cles = {c for f in pa.faits(debut, exercice.date_fin) for c, _ in pa.parts(f, axe) if c is not None}
    noms = pa.libelles(axe, list(cles))
    return sorted(((_cle(c), noms.get(c, str(c))) for c in cles), key=lambda x: x[1])
