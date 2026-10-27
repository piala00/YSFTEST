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


# ---------------------------------------------------------------- États du reporting du Transport
def activite_billetterie(debut, fin):
    """Par point de vente : billets vendus et annulés, recettes des billets et des bagages, par mode de paiement.
    Données de billetterie (date de vente) ; les montants comptables sont dans les états analytiques."""
    from .models import Billet

    modes = {Billet.ESPECES: "especes", Billet.MOBILE_MONEY: "mobile", Billet.COMPTE: "compte"}
    groupes = {}
    for b in Billet.objects.filter(date_vente__range=(debut, fin)).select_related("gare"):
        cle = b.gare.nom if b.gare_id else "Sans point de vente"
        g = groupes.setdefault(cle, {"agence": cle, "billets": 0, "annules": 0, "bagages_nombre": 0, "billets_montant": ZERO,
                                     "bagages_montant": ZERO, "especes": ZERO, "mobile": ZERO, "compte": ZERO})
        if b.statut == Billet.ANNULE:
            g["annules"] += 1
            continue
        montant, bagages = b.prix or ZERO, b.prix_bagages or ZERO
        g["billets"] += 1
        g["bagages_nombre"] += b.bagages_nombre
        g["billets_montant"] += montant
        g["bagages_montant"] += bagages
        g[modes.get(b.paiement, "especes")] += montant + bagages
    lignes = sorted(groupes.values(), key=lambda g: -(g["billets_montant"] + g["bagages_montant"]))
    for l in lignes:
        l["total"] = l["billets_montant"] + l["bagages_montant"]
    total = {k: sum((l[k] for l in lignes), ZERO if k not in ("billets", "annules", "bagages_nombre") else 0)
             for k in ("billets", "annules", "bagages_nombre", "billets_montant", "bagages_montant", "especes", "mobile",
                       "compte", "total")}
    return {"lignes": lignes, "total": total}


def activite_colis(debut, fin, axe="depart"):
    """Colis, courrier et fret par agence de départ, d'arrivée ou par liaison : envois, pièces, poids, recettes,
    port dû, contre-remboursements, livrés et en attente (date d'enregistrement)."""
    from .models import Colis

    groupes = {}
    for c in Colis.objects.filter(date__range=(debut, fin)).select_related("gare_depart", "gare_arrivee"):
        if axe == "arrivee":
            cle = c.gare_arrivee.nom
        elif axe == "liaison":
            cle = f"{c.gare_depart.nom} → {c.gare_arrivee.nom}"
        else:
            cle = c.gare_depart.nom
        g = groupes.setdefault(cle, {"cle": cle, "envois": 0, "annules": 0, "pieces": 0, "poids": ZERO, "recette": ZERO,
                                     "port_du": ZERO, "remboursements": ZERO, "livres": 0, "attente": 0})
        if c.statut == Colis.ANNULE:
            g["annules"] += 1
            continue
        g["envois"] += 1
        g["pieces"] += c.nombre
        g["poids"] += c.poids or ZERO
        g["recette"] += c.prix or ZERO
        if c.port == Colis.DU:
            g["port_du"] += c.prix or ZERO
        g["remboursements"] += c.contre_remboursement or ZERO
        if c.statut == Colis.LIVRE:
            g["livres"] += 1
        else:
            g["attente"] += 1
    lignes = sorted(groupes.values(), key=lambda g: -g["recette"])
    total = {k: sum((l[k] for l in lignes), ZERO if k in ("poids", "recette", "port_du", "remboursements") else 0)
             for k in ("envois", "annules", "pieces", "poids", "recette", "port_du", "remboursements", "livres", "attente")}
    return {"lignes": lignes, "total": total}


def tableau_de_bord(debut, fin):
    """Indicateurs du transport sur la période, comparés à la période précédente de même durée."""
    import datetime

    from .models import Billet, Colis

    def resume(d, f):
        agences = _periode("agence", d, f)
        t = {k: sum((g[k] for g in agences.values()), ZERO if k in ("produits", "charges") else 0)
             for k in ("produits", "charges", "voyages", "voyageurs", "places")}
        t["resultat"] = t["produits"] - t["charges"]
        t["remplissage"] = round(100 * t["voyageurs"] / t["places"]) if t["places"] else None
        t["billets"] = Billet.objects.filter(date_vente__range=(d, f)).exclude(statut=Billet.ANNULE).count()
        colis = Colis.objects.filter(date__range=(d, f)).exclude(statut=Colis.ANNULE)
        t["colis"] = colis.count()
        t["colis_recette"] = sum((c.prix or ZERO for c in colis), ZERO)
        return t

    duree = fin - debut
    precedent_fin = debut - datetime.timedelta(days=1)
    actuel, precedent = resume(debut, fin), resume(precedent_fin - duree, precedent_fin)
    indicateurs = []
    for cle, libelle, genre in (("produits", "Produits", "montant"), ("charges", "Charges", "montant"),
                                ("resultat", "Résultat", "montant"), ("voyages", "Voyages effectués", "nombre"),
                                ("voyageurs", "Voyageurs", "nombre"), ("remplissage", "Remplissage", "pourcent"),
                                ("billets", "Billets vendus", "nombre"), ("colis", "Colis et fret", "nombre"),
                                ("colis_recette", "Recette colis et fret", "montant")):
        a, b = actuel[cle], precedent[cle]
        indicateurs.append({"cle": cle, "libelle": libelle, "genre": genre, "valeur": a, "precedent": b,
                            "variation": _variation(a, b) if a is not None and b is not None else None})
    vehicules = sorted(({"libelle": k, **v} for k, v in _periode("vehicule", debut, fin).items()), key=lambda v: -v["resultat"])
    lignes = sorted(({"libelle": k, **v} for k, v in _periode("ligne", debut, fin).items()), key=lambda v: -v["resultat"])
    agences = sorted(({"libelle": k, **v} for k, v in _periode("agence", debut, fin).items()), key=lambda v: -v["resultat"])
    return {"indicateurs": indicateurs, "meilleurs": vehicules[:5], "moins_bons": vehicules[-5:][::-1] if len(vehicules) > 5 else [],
            "lignes": lignes, "agences": agences, "precedent_du": precedent_fin - duree, "precedent_au": precedent_fin}
