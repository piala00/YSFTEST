"""Reporting comparatif du transport (skill reporting analytique) : deux périodes comparées par agence, flotte
Classique / VIP, ligne, véhicule ou propriétaire.

Montants : lignes d'écritures générales validées (source unique), jamais recalculées depuis les billets.
Voyages, voyageurs et remplissage : données d'exploitation des départs, affichées à part.
Base de date : date comptable des écritures ; date du départ pour les données d'exploitation.
"""
from collections import OrderedDict
from decimal import Decimal

ZERO = Decimal("0")
AXES = [("agence", "Par agence"), ("gamme", "Classique / VIP"), ("ligne", "Par ligne"), ("vehicule", "Par véhicule"),
        ("proprietaire", "Par propriétaire")]


def _vide():
    return {"produits": ZERO, "charges": ZERO, "voyages": 0, "voyageurs": 0, "places": 0}


def _periode(axe, debut, fin, gamme=""):
    from django.db.models import Q

    from apps.comptabilite.models import Ecriture, LigneEcriture
    from apps.echanges.publication import site_local

    from .analytique import _contrat_le, _contrats_par_vehicule, _Gammes
    from .etats import _depart_des_pieces
    from .models import Depart

    local = site_local()
    ici = local.code if local else "Ce dossier"
    gammes, contrats = _Gammes(), _contrats_par_vehicule(debut, fin)
    departs = list(Depart.objects.filter(date__range=(debut, fin)).exclude(statut__in=[Depart.ANNULE, Depart.PROGRAMME])
                   .select_related("ligne", "vehicule"))
    par_pk, pieces = {d.pk: d for d in departs}, _depart_des_pieces(departs)
    groupes = {}

    def cle_depart(d):
        if axe == "agence":
            return d.site_origine or ici
        if axe == "gamme":
            return d.ligne.get_gamme_display()
        if axe == "ligne":
            return d.ligne.code
        if axe == "vehicule":
            return d.vehicule.immatriculation if d.vehicule else "Sans véhicule"
        c = _contrat_le(contrats, d.vehicule_id, d.date)
        return c.partenaire.nom if c else "Véhicules de la société"

    for d in departs:
        if gamme and d.ligne.gamme != gamme:
            continue
        g = groupes.setdefault(cle_depart(d), _vide())
        g["voyages"] += 1
        g["voyageurs"] += d.places_vendues
        g["places"] += d.places
    lignes = (LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE, ecriture__date__range=(debut, fin))
              .filter(Q(compte__numero__startswith="6") | Q(compte__numero__startswith="7"))
              .select_related("compte", "ecriture", "vehicule"))
    if axe != "agence" or gamme:
        lignes = lignes.filter(vehicule__isnull=False)            # hors agence : seuls les montants des véhicules
    for l in lignes:
        if gamme and (l.vehicule is None or gammes(l.vehicule, l.ecriture.date) != gamme):
            continue
        if axe == "agence":
            cle = l.ecriture.site_origine or ici
        elif axe == "gamme":
            cle = dict([("CLASSIQUE", "Classique"), ("VIP", "VIP")])[gammes(l.vehicule, l.ecriture.date)]
        elif axe == "ligne":
            d = par_pk.get(pieces.get(l.ecriture.reference) or pieces.get(l.ecriture.origine))
            cle = d.ligne.code if d else "Hors voyage"
        elif axe == "vehicule":
            cle = l.vehicule.immatriculation
        else:
            c = _contrat_le(contrats, l.vehicule_id, l.ecriture.date)
            cle = c.partenaire.nom if c else "Véhicules de la société"
        g = groupes.setdefault(cle, _vide())
        if l.compte.numero.startswith("7"):
            g["produits"] += l.credit - l.debit
        else:
            g["charges"] += l.debit - l.credit
    for g in groupes.values():
        g["resultat"] = g["produits"] - g["charges"]
        g["remplissage"] = round(100 * g["voyageurs"] / g["places"]) if g["places"] else None
    return groupes


def _variation(a, b):
    if not b:
        return None
    return round(100 * (a - b) / abs(b))


def comparer(axe, periode_a, periode_b, gamme=""):
    """Lignes : libellé, période A, période B, écart et variation (%) du résultat et des produits."""
    a, b = _periode(axe, *periode_a, gamme), _periode(axe, *periode_b, gamme)
    resultat = []
    for cle in sorted(set(a) | set(b), key=str):
        ga, gb = a.get(cle, {**_vide(), "resultat": ZERO, "remplissage": None}), b.get(cle, {**_vide(), "resultat": ZERO,
                                                                                               "remplissage": None})
        resultat.append({"libelle": cle, "a": ga, "b": gb, "ecart": ga["resultat"] - gb["resultat"],
                         "variation_produits": _variation(ga["produits"], gb["produits"]),
                         "variation_resultat": _variation(ga["resultat"], gb["resultat"])})
    total = {}
    for cle in ("a", "b"):
        total[cle] = {k: sum((r[cle][k] for r in resultat), ZERO if k in ("produits", "charges", "resultat") else 0)
                      for k in ("produits", "charges", "resultat", "voyages", "voyageurs", "places")}
        total[cle]["remplissage"] = round(100 * total[cle]["voyageurs"] / total[cle]["places"]) if total[cle]["places"] else None
    total["ecart"] = total["a"]["resultat"] - total["b"]["resultat"]
    total["variation_produits"] = _variation(total["a"]["produits"], total["b"]["produits"])
    total["variation_resultat"] = _variation(total["a"]["resultat"], total["b"]["resultat"])
    return {"lignes": resultat, "total": total}
