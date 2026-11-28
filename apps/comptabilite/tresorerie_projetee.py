"""Trésorerie projetée : solde de trésorerie d'aujourd'hui, puis mois par mois ce qui doit entrer et sortir.

Sources, toujours montrées séparément (rien n'est inventé) :
  - solde de départ : comptes de trésorerie (52, 53, 55, 57, moins les découverts 56), écritures validées ;
  - factures clients et fournisseurs non soldées, à leur échéance (celles déjà échues comptent dans le 1er mois) ;
  - prévisions saisies (emprunt, impôt, loyer…), uniques ou mensuelles ;
  - en option, un budget validé de la société : ses produits et charges des mois à venir. Le budget peut recouper
    des factures déjà émises : c'est une hypothèse de travail, indiquée comme telle.
"""
import calendar
import datetime
from decimal import Decimal

from .budget import mois_exercice

ZERO = Decimal("0")


def _mois(depart, nombre):
    mois, d = [], depart.replace(day=1)
    for _ in range(nombre):
        fin = d.replace(day=calendar.monthrange(d.year, d.month)[1])
        mois.append((d, fin))
        d = fin + datetime.timedelta(days=1)
    return mois


def projection(aujourdhui=None, nombre_mois=6, budget=None):
    from apps.commercial.models import Document
    from apps.reporting.services import tresorerie

    from .models import PrevisionTresorerie

    j = aujourdhui or datetime.date.today()
    periodes = _mois(j, max(1, min(int(nombre_mois or 6), 24)))
    fin_horizon = periodes[-1][1]
    lignes = [{"debut": d, "fin": f, "clients": ZERO, "fournisseurs": ZERO, "prevues_entrees": ZERO,
               "prevues_sorties": ZERO, "budget_entrees": ZERO, "budget_sorties": ZERO} for d, f in periodes]

    def rang(date):
        if date <= periodes[0][1]:
            return 0                                                     # échu ou dans le mois en cours
        return next((i for i, (d, f) in enumerate(periodes) if d <= date <= f), None)

    detail = []
    for type_document, cle in ((Document.FACTURE, "clients"), (Document.ACHAT_FACTURE, "fournisseurs")):
        for d in Document.objects.filter(type_document=type_document, statut=Document.VALIDE).select_related("tiers"):
            reste = d.reste_a_payer
            echeance = d.date_echeance or d.date
            i = rang(echeance) if reste > 0 else None
            if i is None:
                continue
            lignes[i][cle] += reste
            detail.append({"date": echeance, "libelle": f"{d.numero} — {d.tiers.nom if d.tiers_id else ''}",
                           "origine": "Facture client" if cle == "clients" else "Facture fournisseur",
                           "entree": reste if cle == "clients" else ZERO, "sortie": reste if cle == "fournisseurs" else ZERO,
                           "en_retard": echeance < j})
    for p in PrevisionTresorerie.objects.all():
        for date in p.occurrences(periodes[0][0], fin_horizon):
            i = rang(date)
            if i is None or date < j:
                continue
            entree = p.sens == PrevisionTresorerie.ENCAISSEMENT
            lignes[i]["prevues_entrees" if entree else "prevues_sorties"] += p.montant
            detail.append({"date": date, "libelle": p.libelle, "origine": "Prévision saisie",
                           "entree": p.montant if entree else ZERO, "sortie": ZERO if entree else p.montant,
                           "en_retard": False})
    if budget is not None and not budget.axe:
        rangs_budget = {m: k for k, m in enumerate(mois_exercice(budget.exercice))}
        for l in budget.lignes.all():
            for i, (d, _) in enumerate(periodes):
                k = rangs_budget.get(d)
                if k is None or i == 0:                                  # mois en cours : déjà dans le réel
                    continue
                lignes[i]["budget_entrees" if l.produit else "budget_sorties"] += l.mois[k]
    solde = tresorerie(j)
    depart = solde
    for l in lignes:
        l["entrees"] = l["clients"] + l["prevues_entrees"] + l["budget_entrees"]
        l["sorties"] = l["fournisseurs"] + l["prevues_sorties"] + l["budget_sorties"]
        l["solde_debut"] = solde
        solde += l["entrees"] - l["sorties"]
        l["solde_fin"] = solde
    detail.sort(key=lambda x: x["date"])
    return {"aujourdhui": j, "depart": depart, "lignes": lignes, "detail": detail, "fin": solde,
            "plus_bas": min(lignes, key=lambda l: l["solde_fin"]), "budget": budget}
