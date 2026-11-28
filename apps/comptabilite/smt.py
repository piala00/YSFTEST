"""États financiers du système minimal de trésorerie (SMT), tirés des mêmes écritures que le système normal.

Structure : modèles DSF SMT de la DGI (2021), lignes « MOD BILAN » et compte de résultat (recettes, dépenses,
variations des stocks, des créances et des dettes, dotations) ; Acte uniforme, art. 28 (le SMT tient compte des
variations significatives de stocks, créances et dettes). Les rattachements des comptes ci-dessous ne sont pas
publiés par la DGI : ils sont PROPOSÉS et doivent être validés par l'expert-comptable.

Le compte de résultat part de la trésorerie : pour chaque écriture qui touche une caisse ou une banque, on classe ses
contreparties (ventes, achats, loyers, salaires…). Les mouvements entre caisses et banques, les fonds en transit,
les liaisons entre agences, les emprunts, apports et immobilisations ne sont ni recettes ni dépenses.
"""
import datetime
from collections import OrderedDict
from decimal import Decimal
from functools import reduce
from operator import or_

from django.db.models import Q

from .services import lignes_validees, soldes_par_compte

ZERO = Decimal("0")
TRESORERIE = ("52", "53", "55", "56", "57")
HORS_RESULTAT = ("1", "2", "58")                       # financement, patrimoine, virements internes

RECETTES = [("ventes", "Recettes sur ventes ou prestations de services"), ("autres_recettes", "Autres recettes sur activités")]
DEPENSES = [("achats", "Dépenses sur achats"), ("loyers", "Dépenses sur loyers"), ("salaires", "Dépenses sur salaires"),
            ("impots", "Dépenses sur impôts et taxes"), ("interets", "Charge d'intérêts"),
            ("autres_depenses", "Autres dépenses sur activités")]


def _rubrique(numero):
    """Rubrique SMT de la contrepartie d'un mouvement de trésorerie (proposition à valider)."""
    if numero.startswith(("70", "41")):
        return "ventes", "autres_depenses"            # clients, avances des voyageurs ; remboursements = autres dépenses
    if numero.startswith("7"):
        return "autres_recettes", "autres_depenses"
    if numero.startswith(("60", "40")):
        return "autres_recettes", "achats"
    if numero.startswith("622"):
        return "autres_recettes", "loyers"
    if numero.startswith(("66", "42", "43")):
        return "autres_recettes", "salaires"
    if numero.startswith(("64", "44")):
        return "autres_recettes", "impots"
    if numero.startswith("67"):
        return "autres_recettes", "interets"
    return "autres_recettes", "autres_depenses"


def compte_de_resultat(date_debut, date_fin):
    lignes = lignes_validees(date_debut, date_fin).select_related("compte")
    ecritures = set(lignes.filter(reduce(or_, (Q(compte__numero__startswith=c) for c in ("52", "53", "55", "56", "57")))).values_list("ecriture_id", flat=True))
    montants = OrderedDict((cle, ZERO) for cle, _ in RECETTES + DEPENSES)
    for l in lignes.filter(ecriture_id__in=ecritures):
        n = l.compte.numero
        if n.startswith(TRESORERIE) or n.startswith(HORS_RESULTAT) or n.startswith("18"):
            continue
        net = l.credit - l.debit                         # > 0 : argent reçu pour cette contrepartie
        cle_recette, cle_depense = _rubrique(n)
        if net > 0:
            montants[cle_recette] += net
        else:
            montants[cle_depense] -= net
    recettes = sum((montants[c] for c, _ in RECETTES), ZERO)
    depenses = sum((montants[c] for c, _ in DEPENSES), ZERO)
    veille = date_debut - datetime.timedelta(days=1)
    avant, apres = soldes_par_compte(veille), soldes_par_compte(date_fin)

    def total(soldes, prefixes, signe):
        return sum((s for n, s in soldes.items() if n.startswith(prefixes) and (s > 0 if signe > 0 else s < 0)), ZERO)

    var_stocks = total(apres, ("3",), 1) - total(avant, ("3",), 1)
    var_creances = total(apres, ("4",), 1) - total(avant, ("4",), 1)
    var_dettes = -(total(apres, ("4",), -1) - total(avant, ("4",), -1))
    dotations = sum((l.debit - l.credit for l in lignes.filter(compte__numero__startswith="68")), ZERO)
    solde = recettes - depenses
    resultat = solde + var_stocks + var_creances - var_dettes - dotations
    comptable = -sum((s for n, s in soldes_par_compte(date_fin, date_debut=date_debut).items() if n[:1] in "678"), ZERO)
    return {"montants": montants, "recettes": recettes, "depenses": depenses, "solde": solde,
            "var_stocks": var_stocks, "var_creances": var_creances, "var_dettes": var_dettes, "dotations": dotations,
            "resultat": resultat, "resultat_comptable": comptable, "ecart": resultat - comptable,
            "lignes_recettes": [(libelle, montants[cle]) for cle, libelle in RECETTES],
            "lignes_depenses": [(libelle, montants[cle]) for cle, libelle in DEPENSES]}


def bilan(date_fin):
    soldes = soldes_par_compte(date_fin)
    actif = OrderedDict((cle, ZERO) for cle in ("immobilisations", "stocks", "clients", "caisse", "banque"))
    passif = OrderedDict((cle, ZERO) for cle in ("exploitant", "resultat", "emprunt", "fournisseurs"))
    for n, s in soldes.items():
        if not s or n.startswith("9"):
            continue
        if n[:1] in "678":
            passif["resultat"] -= s
        elif n.startswith("2"):
            actif["immobilisations"] += s
        elif n.startswith("3"):
            actif["stocks"] += s
        elif n.startswith("57"):
            actif["caisse"] += s
        elif n.startswith("5"):
            actif["banque"] += s                          # banques, monnaie électronique, fonds en transit
        elif n.startswith(("16", "17")):
            passif["emprunt"] -= s
        elif n.startswith("1") and not n.startswith("18"):
            passif["exploitant"] -= s
        elif s > 0:                                       # comptes de tiers et liaisons : selon leur sens
            actif["clients"] += s
        else:
            passif["fournisseurs"] -= s
    total_actif, total_passif = sum(actif.values(), ZERO), sum(passif.values(), ZERO)
    return {"actif": actif, "passif": passif, "total_actif": total_actif, "total_passif": total_passif,
            "equilibre": total_actif == total_passif}
