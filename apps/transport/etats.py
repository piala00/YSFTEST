"""États du transport : recette journalière par gare, rentabilité par ligne, véhicule ou départ."""
from collections import OrderedDict
from decimal import Decimal

from .models import Billet, Colis, Depart, DepenseVehicule, Gare

ZERO = Decimal("0")


def recette_journaliere(jour):
    gares = OrderedDict((g.pk, {"gare": g, "billets": ZERO, "nb_billets": 0, "annulations": ZERO, "colis": ZERO, "nb_colis": 0,
                                "livraisons": ZERO, "contre_remb_encaisses": ZERO, "contre_remb_reverses": ZERO,
                                "billets_en_compte": ZERO})
                        for g in Gare.objects.all())
    for b in Billet.objects.filter(date_vente=jour).select_related("gare"):
        ligne = gares[b.gare_id]
        if b.paiement == Billet.COMPTE:
            ligne["billets_en_compte"] += b.prix
        else:
            ligne["billets"] += b.prix
        ligne["nb_billets"] += 1
    for b in Billet.objects.filter(statut=Billet.ANNULE, annule_le__date=jour).exclude(paiement=Billet.COMPTE):
        gares[b.gare_id]["annulations"] += b.rembourse
    for c in Colis.objects.filter(date=jour, port=Colis.PAYE, client__isnull=True).exclude(statut=Colis.ANNULE):
        gares[c.gare_depart_id]["colis"] += c.prix
        gares[c.gare_depart_id]["nb_colis"] += 1
    for c in Colis.objects.filter(livre_le__date=jour):
        g = gares[c.gare_arrivee_id]
        g["livraisons"] += c.prix if c.port == Colis.DU else ZERO
        g["contre_remb_encaisses"] += c.contre_remboursement
    for c in Colis.objects.filter(cr_reverse_le__date=jour):
        gares[c.gare_depart_id]["contre_remb_reverses"] += c.contre_remboursement
    resultat = []
    for g in gares.values():
        g["net"] = (g["billets"] - g["annulations"] + g["colis"] + g["livraisons"] + g["contre_remb_encaisses"]
                    - g["contre_remb_reverses"])
        if any(v for k, v in g.items() if k != "gare"):
            resultat.append(g)
    return resultat


def rentabilite(debut, fin, axe="ligne"):
    """Recettes (billets non annulés + retenues, colis chargés) et dépenses de véhicules, regroupées par axe."""
    groupes = OrderedDict()

    def groupe(cle, libelle):
        return groupes.setdefault(cle, {"libelle": libelle, "departs": 0, "voyageurs": 0, "places": 0, "billets": ZERO,
                                        "colis": ZERO, "depenses": ZERO})

    departs = Depart.objects.filter(date__range=(debut, fin)).exclude(statut=Depart.ANNULE).select_related("ligne", "vehicule")
    for d in departs:
        if axe == "vehicule":
            g = groupe(d.vehicule_id, str(d.vehicule) if d.vehicule else "Sans véhicule")
        elif axe == "depart":
            g = groupe(d.pk, str(d))
        else:
            g = groupe(d.ligne_id, str(d.ligne))
        g["departs"] += 1
        g["voyageurs"] += d.places_vendues
        g["places"] += d.places
        g["billets"] += d.recette_billets() + sum((b.retenue for b in d.billets.filter(statut=Billet.ANNULE)), ZERO)
        g["colis"] += d.recette_colis()
        if axe == "depart":
            g["depenses"] += d.depenses()
    if axe == "vehicule":
        for dv in DepenseVehicule.objects.filter(date__range=(debut, fin)).select_related("vehicule"):
            groupe(dv.vehicule_id, str(dv.vehicule))["depenses"] += dv.montant
    elif axe == "ligne":
        for dv in DepenseVehicule.objects.filter(date__range=(debut, fin), depart__isnull=False).select_related("depart__ligne"):
            groupe(dv.depart.ligne_id, str(dv.depart.ligne))["depenses"] += dv.montant
    for g in groupes.values():
        g["recettes"] = g["billets"] + g["colis"]
        g["marge"] = g["recettes"] - g["depenses"]
        g["remplissage"] = round(100 * g["voyageurs"] / g["places"]) if g["places"] else None
    return list(groupes.values())


# ---------------------------------------------------------------- Comptes des véhicules (comptabilité)
def _lignes_vehicules(debut, fin):
    from apps.comptabilite.models import Ecriture, LigneEcriture

    return (LigneEcriture.objects.filter(vehicule__isnull=False, ecriture__statut=Ecriture.STATUT_VALIDEE,
                                         ecriture__date__range=(debut, fin))
            .select_related("ecriture__journal", "compte", "vehicule"))


def balance_vehicules(debut, fin):
    """Par véhicule, sur toutes les écritures (au siège : toutes les agences) : recettes (classe 7), dépenses
    (classe 6), résultat, et détail des recettes voyageurs / colis et des principales dépenses."""
    from .models import ParametresTransport, Vehicule

    p = ParametresTransport.get()
    lignes = OrderedDict((v.pk, {"vehicule": v, "voyageurs": ZERO, "colis": ZERO, "autres_recettes": ZERO, "recettes": ZERO,
                                 "carburant": ZERO, "entretien": ZERO, "autres_depenses": ZERO, "depenses": ZERO})
                         for v in Vehicule.objects.all())
    for l in _lignes_vehicules(debut, fin):
        g, numero, net = lignes[l.vehicule_id], l.compte.numero, l.credit - l.debit
        if numero.startswith("7"):
            cle = ("voyageurs" if numero == p.compte_billets.numero else
                   "colis" if numero in (p.compte_colis.numero, p.compte_fret.numero) else "autres_recettes")
            g[cle] += net
            g["recettes"] += net
        elif numero.startswith("6"):
            cle = "carburant" if numero.startswith("605") else "entretien" if numero.startswith("624") else "autres_depenses"
            g[cle] -= net
            g["depenses"] -= net
    resultat = []
    for g in lignes.values():
        g["resultat"] = g["recettes"] - g["depenses"]
        if g["recettes"] or g["depenses"] or g["vehicule"].actif:
            resultat.append(g)
    return resultat


def grand_livre_vehicule(vehicule, debut, fin):
    """Mouvements du véhicule, avec le résultat cumulé (recettes − dépenses)."""
    lignes, cumul = [], ZERO
    for l in _lignes_vehicules(debut, fin).filter(vehicule=vehicule).order_by("ecriture__date", "ecriture__numero", "pk"):
        cumul += l.credit - l.debit
        lignes.append({"ligne": l, "cumul": cumul})
    return lignes
