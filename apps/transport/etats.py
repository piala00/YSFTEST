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
            ligne["billets_en_compte"] += b.total
        else:
            ligne["billets"] += b.total
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


def _depart_des_pieces(departs):
    """Pièce comptable (référence) → départ : recettes du départ, colis transportés, dépenses, pleins et avances de
    mission rattachés au voyage."""
    from apps.garage.models import PleinCarburant

    from .models_exploitation import AvanceMission

    ids = [d.pk for d in departs]
    pieces = {d.numero: d.pk for d in departs}
    from .models_incidents import Incident

    for modele in (Colis, DepenseVehicule, PleinCarburant, AvanceMission, Incident):
        pieces.update(dict(modele.objects.filter(depart_id__in=ids).values_list("numero", "depart_id")))
    return pieces


def rentabilite(debut, fin, axe="ligne"):
    """Rentabilité par ligne, véhicule ou départ. Montants : écritures générales validées portant le véhicule (source
    unique), rattachées au départ par leur pièce ; voyageurs, places et remplissage : données d'exploitation."""
    from apps.comptabilite.models import Ecriture, LigneEcriture

    groupes = OrderedDict()

    def groupe(cle, libelle):
        return groupes.setdefault(cle, {"libelle": libelle, "departs": 0, "voyageurs": 0, "places": 0, "billets": ZERO,
                                        "colis": ZERO, "autres": ZERO, "depenses": ZERO})

    def cle_depart(d):
        if axe == "vehicule":
            return d.vehicule_id, str(d.vehicule) if d.vehicule else "Sans véhicule"
        if axe == "depart":
            return d.pk, str(d)
        return ("ligne", d.ligne_id), str(d.ligne)

    departs = list(Depart.objects.filter(date__range=(debut, fin)).exclude(statut=Depart.ANNULE).select_related("ligne", "vehicule"))
    for d in departs:
        g = groupe(*cle_depart(d))
        g["departs"] += 1
        g["voyageurs"] += d.places_vendues
        g["places"] += d.places
    par_pk = {d.pk: d for d in departs}
    pieces = _depart_des_pieces(departs)
    from .models import ParametresTransport

    p = ParametresTransport.get()
    for l in (LigneEcriture.objects.filter(vehicule__isnull=False, ecriture__statut=Ecriture.STATUT_VALIDEE,
                                           ecriture__date__range=(debut, fin))
              .filter(compte__numero__regex=r"^[67]").select_related("compte", "ecriture", "vehicule")):
        d = par_pk.get(pieces.get(l.ecriture.reference) or pieces.get(l.ecriture.origine))
        if d is not None:
            g = groupe(*cle_depart(d))
        elif axe == "vehicule":
            g = groupe(l.vehicule_id, str(l.vehicule))
        else:
            g = groupe("hors", "Hors voyage (véhicule sans départ rattaché)")
        numero = l.compte.numero
        if numero.startswith("7"):
            cle = ("billets" if numero == p.compte_billets.numero else
                   "colis" if numero in (p.compte_colis.numero, p.compte_fret.numero) else "autres")
            g[cle] += l.credit - l.debit
        else:
            g["depenses"] += l.debit - l.credit
    for g in groupes.values():
        g["recettes"] = g["billets"] + g["colis"] + g["autres"]
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
        a[{"ESPECES": "especes", "MOBILE_MONEY": "mobile", "COMPTE": "compte"}[b.paiement]] += b.total
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


def rapport_agence_a4(jour, site=""):
    """Rapport journalier simple de l'agence, en tableaux (skill rapport journalier d'agence), imprimable en A4 portrait.

    site : "" = ce dossier ; au siège, code d'une agence = ses données reçues par les échanges.
    Deux vues distinctes, jamais additionnées :
      - exploitation (date de départ) : départs effectués, voyageurs et part du prix revenant à chaque car ;
      - trésorerie (date de paiement) : ce qui est réellement entré et sorti des caisses, banques et Mobile Money,
        lu sur les comptes de trésorerie (une pièce comptable = un mouvement : pas de double compte).
    """
    from collections import defaultdict

    from apps.comptabilite.models import Ecriture, Journal, LigneEcriture

    from .models import ParametresTransport, Troncon

    p = ParametresTransport.get()

    def num(compte):
        return getattr(compte, "numero", None)

    # A. Billetterie : départs effectués, une ligne par trajet et par prix réellement pratiqué
    billetterie = []
    for d in (Depart.objects.filter(date=jour, site_origine=site, statut__in=[Depart.PARTI, Depart.ARRIVE, Depart.CLOTURE])
              .select_related("vehicule", "ligne").order_by("heure", "numero")):
        groupes = OrderedDict()
        for t in (d.troncons.filter(statut=Troncon.EFFECTUE).select_related("gare_depart", "gare_arrivee")
                  .order_by("gare_depart__ville", "gare_arrivee__ville", "-part")):
            g = groupes.setdefault((t.gare_depart.ville, t.gare_arrivee.ville, t.part), {"places": 0})
            g["places"] += 1
        if not groupes:
            groupes[(d.ligne.gare_depart.ville, d.ligne.gare_arrivee.ville, None)] = {"places": 0}
        for (a, b, prix), g in groupes.items():
            billetterie.append({"depart": d, "vehicule": d.vehicule, "trajet": f"{a} → {b}", "places": g["places"],
                                "prix": prix, "montant": (prix or ZERO) * g["places"]})
    non_partis = Depart.objects.filter(date=jour, site_origine=site, statut=Depart.PROGRAMME).count()
    # Bagages payants des voyageurs partis (part revenant à chaque car)
    bagages = [{"vehicule": t.depart.vehicule, "designation": t.billet.bagages, "billet": t.billet.numero,
                "destination": t.gare_arrivee.ville, "quantite": t.billet.bagages_nombre, "montant": t.part_bagages}
               for t in (Troncon.objects.filter(depart__date=jour, depart__site_origine=site, statut=Troncon.EFFECTUE,
                                                part_bagages__gt=0)
                         .select_related("depart__vehicule", "billet", "gare_arrivee").order_by("depart__heure", "billet__numero"))]

    # B. Trésorerie : lignes des comptes de trésorerie de la journée
    journaux = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False).select_related(
        "compte_tresorerie")
    comptes = OrderedDict()
    for j in journaux.order_by("compte_tresorerie__numero", "code"):
        c = comptes.setdefault(j.compte_tresorerie_id, {"compte": j.compte_tresorerie, "journaux": []})
        c["journaux"].append(j.code)
    colis_comptes = {num(p.compte_colis_a_transporter), num(p.compte_contre_remboursement), num(p.compte_colis), num(p.compte_fret)}

    def especes(compte):
        return compte.numero.startswith("57")

    lignes = (LigneEcriture.objects.filter(compte_id__in=comptes, ecriture__date=jour, ecriture__site_origine=site,
                                           ecriture__statut=Ecriture.STATUT_VALIDEE)
              .select_related("compte", "ecriture", "ecriture__journal").order_by("ecriture__numero", "pk"))
    autres_lignes = defaultdict(list)
    for l in LigneEcriture.objects.filter(ecriture__in={l.ecriture_id for l in lignes}).select_related("compte", "vehicule"):
        autres_lignes[l.ecriture_id].append(l)
    totaux = defaultdict(lambda: {"especes": ZERO, "electronique": ZERO})
    colis, sorties, par_compte = [], [], defaultdict(lambda: defaultdict(lambda: ZERO))
    for l in lignes:
        e, entree = l.ecriture, l.debit - l.credit
        autres = [o for o in autres_lignes[e.pk] if o.compte_id not in comptes]
        numeros = {o.compte.numero for o in autres}
        if e.libelle.startswith("Écart de caisse"):
            nature = "ecart"
        elif any(n.startswith("585") for n in numeros):
            nature = "transfert"
        elif num(p.compte_remboursements) in numeros or (num(p.compte_billets_a_voyager) in numeros and entree < 0):
            nature = "remboursement"
        elif num(p.compte_billets_a_voyager) in numeros:
            nature = "billets"
            if entree > 0:                            # vente : la part des bagages est sur le billet
                from .models import Billet as BilletModele

                b = BilletModele.objects.filter(numero=e.reference).only("prix_bagages").first()
                part = min(b.prix_bagages, entree) if b and b.prix_bagages else ZERO
                if part:
                    totaux["bagages"]["especes" if especes(l.compte) else "electronique"] += part
                    totaux["billets"]["especes" if especes(l.compte) else "electronique"] -= part
        elif numeros & colis_comptes and entree > 0:
            nature = "colis"
        else:
            nature = "autres_entrees" if entree > 0 else "sorties"
        moyen = "especes" if especes(l.compte) else "electronique"
        totaux[nature][moyen] += entree if nature in ("billets", "colis", "autres_entrees") else -entree
        if nature == "transfert":                     # entre caisses, banque, siège : ni recette ni dépense
            par_compte[l.compte_id]["transferts"] += entree
        elif entree > 0:
            par_compte[l.compte_id]["entrees"] += entree
        else:
            par_compte[l.compte_id]["sorties"] -= entree
        if nature == "colis":
            from .models import Colis as ColisModele

            c = ColisModele.objects.filter(numero=e.reference).select_related("gare_arrivee").first()
            colis.append({"piece": e.reference or e.numero, "designation": (f"{c.get_nature_display()} {c.description}".strip()
                                                                           if c else e.libelle),
                          "destination": c.gare_arrivee.ville if c else "—", "moyen": e.journal.code, "montant": entree})
        elif nature == "sorties":
            vehicules = sorted({o.vehicule.immatriculation for o in autres if o.vehicule_id})
            sorties.append({"piece": e.reference or e.numero, "designation": e.libelle,
                            "affectation": ", ".join(vehicules) or "Agence",
                            "moyen": "Espèces" if moyen == "especes" else e.journal.intitule, "montant": -entree})

    def t(nature, moyen=None):
        v = totaux[nature] if nature in totaux else {"especes": ZERO, "electronique": ZERO}
        return v[moyen] if moyen else v["especes"] + v["electronique"]

    encaissements = {m: t("billets", m) + t("bagages", m) + t("colis", m) + t("autres_entrees", m)
                     for m in ("especes", "electronique")}

    # Situation par caisse / banque / Mobile Money
    caisses = []
    for cid, c in comptes.items():
        avant = LigneEcriture.objects.filter(compte_id=cid, ecriture__date__lt=jour, ecriture__site_origine=site,
                                             ecriture__statut=Ecriture.STATUT_VALIDEE)
        ouverture = sum((x.debit - x.credit for x in avant), ZERO)
        m = par_compte.get(cid, {})
        entrees, sorties_c, transferts = m.get("entrees", ZERO), m.get("sorties", ZERO), m.get("transferts", ZERO)
        if not (ouverture or entrees or sorties_c or transferts):
            continue
        caisses.append({"compte": c["compte"], "journaux": ", ".join(c["journaux"]), "especes": especes(c["compte"]),
                        "ouverture": ouverture, "entrees": entrees, "sorties": sorties_c, "transferts": transferts,
                        "solde": ouverture + entrees - sorties_c + transferts})
    total_caisses = {k: sum((c[k] for c in caisses), ZERO) for k in ("ouverture", "entrees", "sorties", "transferts", "solde")}
    especes_caisses = [c for c in caisses if c["especes"]]
    total_sorties = sum((s["montant"] for s in sorties), ZERO)
    return {
        "billetterie": billetterie, "non_partis": non_partis,
        "total_billetterie": {"places": sum(l["places"] for l in billetterie),
                              "montant": sum((l["montant"] for l in billetterie), ZERO)},
        "bagages": bagages, "total_bagages": {"quantite": sum(b["quantite"] for b in bagages),
                                              "montant": sum((b["montant"] for b in bagages), ZERO)},
        "colis": colis, "total_colis": sum((c["montant"] for c in colis), ZERO),
        "sorties": sorties, "total_sorties": total_sorties,
        "caisse": {
            "billets": t("billets"), "bagages": t("bagages"), "colis": t("colis"), "autres": t("autres_entrees"),
            "total": encaissements["especes"] + encaissements["electronique"],
            "especes": encaissements["especes"], "electronique": encaissements["electronique"],
            "remboursements": t("remboursement"), "sorties": total_sorties,
            "nette": encaissements["especes"] + encaissements["electronique"] - t("remboursement") - total_sorties,
            "ouverture_especes": sum((c["ouverture"] for c in especes_caisses), ZERO),
            "remboursements_especes": t("remboursement", "especes"), "sorties_especes": t("sorties", "especes"),
            "decaissements_especes": t("remboursement", "especes") + t("sorties", "especes"),
            "transferts_especes": sum((c["transferts"] for c in especes_caisses), ZERO),
            "ecarts": -t("ecart"),
            "solde_especes": sum((c["solde"] for c in especes_caisses), ZERO),
        },
        "caisses": caisses, "total_caisses": total_caisses,
    }
