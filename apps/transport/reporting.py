"""Reporting comparatif du transport (skill reporting analytique) : deux périodes comparées par agence, flotte
Classique / VIP, ligne, véhicule ou propriétaire.

Montants : lignes d'écritures générales validées (source unique), jamais recalculées depuis les billets.
Voyages, voyageurs et remplissage : données d'exploitation des départs, affichées à part.
Base de date : date comptable des écritures ; date du départ pour les données d'exploitation.
"""
from decimal import Decimal

ZERO = Decimal("0")
AXES = [("agence", "Par agence"), ("gamme", "Classique / VIP"), ("ligne", "Par ligne"), ("vehicule", "Par véhicule"),
        ("proprietaire", "Par propriétaire")]


def _vide():
    return {"produits": ZERO, "charges": ZERO, "voyages": 0, "voyageurs": 0, "places": 0}


def _periode(axe, debut, fin, gamme=""):
    from apps.commercial.models import Tiers
    from apps.echanges.publication import site_local

    from .analytique import _contrat_le, _contrats_par_vehicule
    from .models import GAMMES, Depart, Ligne, Vehicule

    local = site_local()
    ici = local.code if local else "Ce dossier"
    contrats = _contrats_par_vehicule(debut, fin)
    departs = list(Depart.objects.filter(date__range=(debut, fin)).exclude(statut__in=[Depart.ANNULE, Depart.PROGRAMME])
                   .select_related("ligne", "vehicule"))
    groupes = {}
    contrats_noms = dict(Tiers.objects.filter(contrats_partenaire__isnull=False).values_list("pk", "nom").distinct())

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
    # Montants : le moteur du plan analytique (mêmes lignes validées, même attribution que les états analytiques)
    from apps.comptabilite import plan_analytique as pa

    noms = {"vehicule": {v.pk: v.immatriculation for v in Vehicule.objects.all()},
            "ligne": dict(Ligne.objects.values_list("pk", "code")), "gamme": dict(GAMMES)}
    for f in pa.faits(debut, fin):
        if (axe != "agence" or gamme) and f.get("vehicules") is None:
            continue                                              # hors agence : seuls les montants des véhicules
        if gamme and f.get("gammes") != gamme:
            continue
        if axe == "agence":
            cle = f["site"] or ici
        elif axe == "gamme":
            cle = noms["gamme"].get(f["gammes"], f["gammes"])
        elif axe == "ligne":
            cle = noms["ligne"].get(f["lignes"], "Hors voyage")
        elif axe == "vehicule":
            cle = noms["vehicule"][f["vehicules"]]
        else:
            p = f["proprietaires"]
            cle = "Véhicules de la société" if p == "societe" else contrats_noms.get(p) or str(p)
        g = groupes.setdefault(cle, _vide())
        if f["produit"]:
            g["produits"] += f["montant"]                         # crédit − débit
        else:
            g["charges"] -= f["montant"]                          # débit − crédit
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
