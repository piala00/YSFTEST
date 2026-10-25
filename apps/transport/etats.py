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
        g["net_billetterie"] = g["billets"] - g["annulations"]
        g["net_colis"] = g["colis"] + g["livraisons"] + g["contre_remb_encaisses"] - g["contre_remb_reverses"]
        g["net"] = g["net_billetterie"] + g["net_colis"]
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


# ---------------------------------------------------------------- Rapport journalier de l'agence
def rapport_journalier(jour):
    """Toute l'activité de la journée, service par service, puis véhicule par véhicule et caisse par caisse.
    Chaque service saisit dans son logiciel ; ce rapport regroupe automatiquement."""
    from collections import defaultdict

    from apps.comptabilite.models import Ecriture, Journal, LigneEcriture
    from apps.garage.models import OrdreReparation, PleinCarburant
    from apps.personnel.models import Avance

    from .models import Troncon, Vehicule

    # Billetterie, par guichetier
    agents = defaultdict(lambda: {"nb": 0, "especes": ZERO, "mobile": ZERO, "compte": ZERO, "rembourse": ZERO})
    for b in Billet.objects.filter(date_vente=jour).select_related("vendu_par"):
        a = agents[str(b.vendu_par or "—")]
        a["nb"] += 1
        a[{"ESPECES": "especes", "MOBILE_MONEY": "mobile", "COMPTE": "compte"}[b.paiement]] += b.prix
    for b in Billet.objects.filter(statut=Billet.ANNULE, annule_le__date=jour).select_related("annule_par"):
        agents[str(b.annule_par or b.vendu_par or "—")]["rembourse"] += b.rembourse
    for a in agents.values():
        a["encaisse"] = a["especes"] + a["mobile"] - a["rembourse"]
    # Colis
    envois = Colis.objects.filter(date=jour).exclude(statut=Colis.ANNULE)
    remis = Colis.objects.filter(livre_le__date=jour)
    colis = {"enregistres": envois.count(), "port_paye": sum((c.prix for c in envois if c.port == Colis.PAYE and not c.client_id), ZERO),
             "en_compte": sum((c.prix for c in envois if c.client_id), ZERO), "remis": remis.count(),
             "port_du": sum((c.prix for c in remis if c.port == Colis.DU), ZERO),
             "cr_encaisses": sum((c.contre_remboursement for c in remis), ZERO),
             "cr_reverses": sum((c.contre_remboursement for c in Colis.objects.filter(cr_reverse_le__date=jour)), ZERO),
             "a_remettre": Colis.objects.filter(statut=Colis.ARRIVE).count()}
    # Véhicules : activité du jour et résultat comptable du jour
    vehicules = {}

    def ligne_vehicule(v):
        return vehicules.setdefault(v.pk, {"vehicule": v, "departs": [], "voyageurs": 0, "colis": 0, "litres": ZERO,
                                           "recettes": ZERO, "carburant": ZERO, "reparations": ZERO, "personnel": ZERO,
                                           "autres": ZERO})
    for d in Depart.objects.filter(date=jour, vehicule__isnull=False).exclude(statut=Depart.ANNULE).select_related("vehicule", "ligne"):
        g = ligne_vehicule(d.vehicule)
        g["departs"].append(d)
        g["voyageurs"] += d.troncons.exclude(statut=Troncon.ANNULE).count()
        g["colis"] += d.colis.exclude(statut=Colis.ANNULE).count()
    for p in PleinCarburant.objects.filter(date=jour).select_related("vehicule"):
        ligne_vehicule(p.vehicule)["litres"] += p.litres
    from .models import ParametresTransport

    parametres = ParametresTransport.get()
    for l in LigneEcriture.objects.filter(ecriture__date=jour, ecriture__statut=Ecriture.STATUT_VALIDEE,
                                          vehicule__isnull=False).select_related("compte", "vehicule"):
        g, numero = ligne_vehicule(l.vehicule), l.compte.numero
        if numero.startswith("7"):
            g["recettes"] += l.credit - l.debit
        elif numero.startswith("6"):
            cle = ("carburant" if numero == getattr(parametres.compte_carburant, "numero", "") else
                   "reparations" if numero in (getattr(parametres.compte_pieces, "numero", ""),
                                               getattr(parametres.compte_main_oeuvre, "numero", "")) else
                   "personnel" if numero.startswith("66") else "autres")
            g[cle] += l.debit - l.credit
    for g in vehicules.values():
        g["depenses"] = g["carburant"] + g["reparations"] + g["personnel"] + g["autres"]
        g["resultat"] = g["recettes"] - g["depenses"]
    # Garage
    pleins = PleinCarburant.objects.filter(date=jour)
    garage = {"pleins": pleins.count(), "litres": sum((p.litres for p in pleins), ZERO), "carburant": sum((p.montant for p in pleins), ZERO),
              "reparations_terminees": OrdreReparation.objects.filter(date_sortie=jour, statut=OrdreReparation.CLOTURE).count(),
              "au_garage": OrdreReparation.objects.filter(statut=OrdreReparation.OUVERT).select_related("vehicule")}
    # Caisses et banques : entrées et sorties de la journée
    caisses = []
    for j in Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False):
        lignes = LigneEcriture.objects.filter(compte=j.compte_tresorerie, ecriture__date=jour,
                                              ecriture__statut=Ecriture.STATUT_VALIDEE, ecriture__site_origine="")
        entrees, sorties = sum((l.debit for l in lignes), ZERO), sum((l.credit for l in lignes), ZERO)
        if entrees or sorties:
            caisses.append({"journal": j, "entrees": entrees, "sorties": sorties, "solde": entrees - sorties})
    return {"agents": dict(agents), "colis": colis, "vehicules": sorted(vehicules.values(), key=lambda g: g["vehicule"].immatriculation),
            "garage": garage, "caisses": caisses,
            "avances": sum((a.montant for a in Avance.objects.filter(date=jour, ecriture__isnull=False)), ZERO),
            "total_vehicules": {k: sum((g[k] for g in vehicules.values()), ZERO) for k in ("recettes", "depenses", "resultat")}}


def activite_vehicule(vehicule, debut, fin):
    """Vue d'ensemble d'un véhicule sur la période : voyages, colis, carburant, réparations."""
    from apps.garage.models import OrdreReparation, PleinCarburant

    pleins = list(PleinCarburant.objects.filter(vehicule=vehicule, date__range=(debut, fin)).order_by("date", "pk"))
    releves = [p for p in pleins if p.kilometrage is not None]
    conso = None
    if len(releves) >= 2 and releves[-1].kilometrage > releves[0].kilometrage:
        litres = sum((p.litres for p in releves[1:]), ZERO)
        conso = (litres * 100 / (releves[-1].kilometrage - releves[0].kilometrage)).quantize(Decimal("0.1"))
    reparations = list(OrdreReparation.objects.filter(vehicule=vehicule, date_entree__lte=fin)
                       .exclude(statut=OrdreReparation.ANNULE).filter(models_q_sortie(debut)))
    return {"litres": sum((p.litres for p in pleins), ZERO), "cout_carburant": sum((p.montant for p in pleins), ZERO),
            "consommation": conso, "km": (releves[-1].kilometrage - releves[0].kilometrage) if len(releves) >= 2 else None,
            "pleins": pleins[-10:][::-1], "reparations": reparations,
            "jours_garage": sum((r.immobilisation_jours for r in reparations), 0),
            "colis": Colis.objects.filter(depart__vehicule=vehicule, depart__date__range=(debut, fin)).exclude(statut=Colis.ANNULE).count()}


def models_q_sortie(debut):
    from django.db.models import Q

    return Q(date_sortie__isnull=True) | Q(date_sortie__gte=debut)
