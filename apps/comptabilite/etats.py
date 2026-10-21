"""États financiers SYSCOHADA révisé : Bilan et Compte de résultat (système normal).

Les rubriques reprennent les références officielles (AD, AI, ... TA, RA, XA ...).
Chaque compte du plan est rattaché à la rubrique dont le préfixe est le plus long.
"""
from decimal import Decimal

from .services import soldes_par_compte

ZERO = Decimal("0")


def _commence(numero, prefixes):
    return any(numero.startswith(p) for p in prefixes)


def _plus_long_prefixe(numero, prefixes):
    candidats = [p for p in prefixes if numero.startswith(p)]
    return max((len(p) for p in candidats), default=-1)


# ---------------------------------------------------------------------------
# Compte de résultat
# ---------------------------------------------------------------------------
# (ref, libellé, sens, préfixes) — sens "P" = produit (crédit - débit), "C" = charge (débit - crédit)
POSTES_RESULTAT = [
    ("TA", "Ventes de marchandises", "P", ["701"]),
    ("RA", "Achats de marchandises", "C", ["601"]),
    ("RB", "Variation de stocks de marchandises", "C", ["6031"]),
    ("TB", "Ventes de produits fabriqués", "P", ["702", "703", "704"]),
    ("TC", "Travaux, services vendus", "P", ["705", "706"]),
    ("TD", "Produits accessoires", "P", ["707"]),
    ("TE", "Production stockée (ou déstockage)", "P", ["73"]),
    ("TF", "Production immobilisée", "P", ["72"]),
    ("TG", "Subventions d'exploitation", "P", ["71"]),
    ("TH", "Autres produits", "P", ["75"]),
    ("TI", "Transferts de charges d'exploitation", "P", ["781"]),
    ("RC", "Achats de matières premières et fournitures liées", "C", ["602"]),
    ("RD", "Variation de stocks de matières premières", "C", ["6032"]),
    ("RE", "Autres achats", "C", ["604", "605", "608"]),
    ("RF", "Variation de stocks d'autres approvisionnements", "C", ["6033"]),
    ("RG", "Transports", "C", ["61"]),
    ("RH", "Services extérieurs", "C", ["62", "63"]),
    ("RI", "Impôts et taxes", "C", ["64"]),
    ("RJ", "Autres charges", "C", ["65"]),
    ("RK", "Charges de personnel", "C", ["66"]),
    ("TJ", "Reprises d'amortissements, provisions et dépréciations", "P", ["791", "798", "799"]),
    ("RL", "Dotations aux amortissements, provisions et dépréciations", "C", ["68", "691"]),
    ("TK", "Revenus financiers et assimilés", "P", ["77"]),
    ("TL", "Reprises de provisions et dépréciations financières", "P", ["797"]),
    ("TM", "Transferts de charges financières", "P", ["787"]),
    ("RM", "Frais financiers et charges assimilées", "C", ["67"]),
    ("RN", "Dotations aux provisions et dépréciations financières", "C", ["697"]),
    ("TN", "Produits des cessions d'immobilisations", "P", ["82"]),
    ("TO", "Autres produits HAO", "P", ["84", "86", "88"]),
    ("RO", "Valeurs comptables des cessions d'immobilisations", "C", ["81"]),
    ("RP", "Autres charges HAO", "C", ["83", "85"]),
    ("RQ", "Participation des travailleurs", "C", ["87"]),
    ("RS", "Impôts sur le résultat", "C", ["89"]),
]

# Soldes intermédiaires : (ref, libellé, formule [(signe, ref)], position après la ref)
SOLDES_RESULTAT = [
    ("XA", "MARGE COMMERCIALE", [("+", "TA"), ("-", "RA"), ("-", "RB")], "RB"),
    ("XB", "CHIFFRE D'AFFAIRES", [("+", "TA"), ("+", "TB"), ("+", "TC"), ("+", "TD")], "TD"),
    ("XC", "VALEUR AJOUTÉE", [("+", "XB"), ("-", "RA"), ("-", "RB"), ("+", "TE"), ("+", "TF"), ("+", "TG"),
                               ("+", "TH"), ("+", "TI"), ("-", "RC"), ("-", "RD"), ("-", "RE"), ("-", "RF"),
                               ("-", "RG"), ("-", "RH"), ("-", "RI"), ("-", "RJ")], "RJ"),
    ("XD", "EXCÉDENT BRUT D'EXPLOITATION", [("+", "XC"), ("-", "RK")], "RK"),
    ("XE", "RÉSULTAT D'EXPLOITATION", [("+", "XD"), ("+", "TJ"), ("-", "RL")], "RL"),
    ("XF", "RÉSULTAT FINANCIER", [("+", "TK"), ("+", "TL"), ("+", "TM"), ("-", "RM"), ("-", "RN")], "RN"),
    ("XG", "RÉSULTAT DES ACTIVITÉS ORDINAIRES", [("+", "XE"), ("+", "XF")], "XF"),
    ("XH", "RÉSULTAT HORS ACTIVITÉS ORDINAIRES", [("+", "TN"), ("+", "TO"), ("-", "RO"), ("-", "RP")], "RP"),
    ("XI", "RÉSULTAT NET", [("+", "XG"), ("+", "XH"), ("-", "RQ"), ("-", "RS")], "RS"),
]


def compte_de_resultat(date_debut, date_fin, exercice=None):
    soldes = soldes_par_compte(date_fin, date_debut=date_debut, exercice=exercice)
    tous_prefixes = [p for _, _, _, prefixes in POSTES_RESULTAT for p in prefixes]
    valeurs = {ref: ZERO for ref, *_ in POSTES_RESULTAT}
    for numero, solde in soldes.items():
        if numero[0] not in "678":
            continue
        meilleur = _plus_long_prefixe(numero, tous_prefixes)
        for ref, _, sens, prefixes in POSTES_RESULTAT:
            if _plus_long_prefixe(numero, prefixes) == meilleur and meilleur >= 0:
                valeurs[ref] += -solde if sens == "P" else solde
                break

    for ref, _, formule, _ in SOLDES_RESULTAT:
        valeurs[ref] = sum((valeurs[r] if s == "+" else -valeurs[r]) for s, r in formule)

    lignes = []
    apres = {pos: (ref, lib) for ref, lib, _, pos in SOLDES_RESULTAT}
    for ref, libelle, sens, _ in POSTES_RESULTAT:
        lignes.append({"ref": ref, "libelle": libelle, "sens": sens, "montant": valeurs[ref], "total": False})
        while ref in apres:
            ref_solde, lib_solde = apres.pop(ref)
            lignes.append({"ref": ref_solde, "libelle": lib_solde, "sens": "", "montant": valeurs[ref_solde], "total": True})
            ref = ref_solde
    return {"lignes": lignes, "valeurs": valeurs, "resultat_net": valeurs["XI"]}


# ---------------------------------------------------------------------------
# Bilan
# ---------------------------------------------------------------------------
# Actif : (ref, libellé, préfixes bruts, préfixes amortissements/dépréciations)
POSTES_ACTIF = [
    ("AD", "Immobilisations incorporelles", ["21"], ["281", "291"]),
    ("AI", "Immobilisations corporelles", ["22", "23", "24"], ["282", "283", "284", "292", "293", "294"]),
    ("AP", "Avances et acomptes versés sur immobilisations", ["25"], ["295"]),
    ("AQ", "Immobilisations financières", ["26", "27"], ["296", "297"]),
    ("AZ", "TOTAL ACTIF IMMOBILISÉ", None, None),
    ("BA", "Actif circulant HAO", ["485", "488"], ["498"]),
    ("BB", "Stocks et encours", ["31", "32", "33", "34", "35", "36", "37", "38"], ["39"]),
    ("BH", "Fournisseurs, avances versées", ["409"], ["490"]),
    ("BI", "Clients", ["41"], ["491"]),
    ("BJ", "Autres créances", ["42", "43", "44", "45", "46", "47"], ["492", "493", "494", "495", "496", "497"]),
    ("BK", "TOTAL ACTIF CIRCULANT", None, None),
    ("BQ", "Titres de placement", ["50"], ["590"]),
    ("BR", "Valeurs à encaisser", ["51"], ["591"]),
    ("BS", "Banques, chèques postaux, caisse et assimilés", ["52", "53", "54", "55", "57", "58"], ["592", "593", "594"]),
    ("BT", "TOTAL TRÉSORERIE-ACTIF", None, None),
    ("BU", "Écart de conversion-Actif", ["478"], []),
]
TOTAUX_ACTIF = {"AZ": ["AD", "AI", "AP", "AQ"], "BK": ["BA", "BB", "BH", "BI", "BJ"], "BT": ["BQ", "BR", "BS"]}

# Passif : (ref, libellé, préfixes)
POSTES_PASSIF = [
    ("CA", "Capital", ["101", "102", "103", "104"]),
    ("CB", "Apporteurs capital non appelé (-)", ["109"]),
    ("CD", "Primes liées au capital social", ["105"]),
    ("CE", "Écarts de réévaluation", ["106"]),
    ("CF", "Réserves indisponibles", ["111", "112", "113"]),
    ("CG", "Réserves libres", ["118"]),
    ("CH", "Report à nouveau (+ ou -)", ["12"]),
    ("CJ", "Résultat net de l'exercice (bénéfice + ou perte -)", ["13"]),
    ("CL", "Subventions d'investissement", ["14"]),
    ("CM", "Provisions réglementées", ["15"]),
    ("CP", "TOTAL CAPITAUX PROPRES ET RESSOURCES ASSIMILÉES", None),
    ("DA", "Emprunts et dettes financières diverses", ["16", "18"]),
    ("DB", "Dettes de location-acquisition", ["17"]),
    ("DC", "Provisions pour risques et charges", ["19"]),
    ("DD", "TOTAL DETTES FINANCIÈRES ET RESSOURCES ASSIMILÉES", None),
    ("DF", "TOTAL RESSOURCES STABLES", None),
    ("DH", "Dettes circulantes HAO", ["481", "482", "484"]),
    ("DI", "Clients, avances reçues", ["419"]),
    ("DJ", "Fournisseurs d'exploitation", ["40"]),
    ("DK", "Dettes fiscales et sociales", ["42", "43", "44"]),
    ("DM", "Autres dettes", ["45", "46", "47"]),
    ("DN", "Provisions pour risques à court terme", ["499"]),
    ("DP", "TOTAL PASSIF CIRCULANT", None),
    ("DQ", "Banques, crédits d'escompte", ["565"]),
    ("DR", "Banques, établissements financiers et crédits de trésorerie", ["52", "53", "56"]),
    ("DT", "TOTAL TRÉSORERIE-PASSIF", None),
    ("DV", "Écart de conversion-Passif", ["479"]),
]
TOTAUX_PASSIF = {
    "CP": ["CA", "CB", "CD", "CE", "CF", "CG", "CH", "CJ", "CL", "CM"],
    "DD": ["DA", "DB", "DC"],
    "DF": ["CP", "DD"],
    "DP": ["DH", "DI", "DJ", "DK", "DM", "DN"],
    "DT": ["DQ", "DR"],
}

# Comptes de tiers / trésorerie dont le classement dépend du sens du solde
COMPTES_A_SENS_VARIABLE = ("4", "5")


def _rubrique_actif(numero):
    """Retourne (ref, colonne) avec colonne 'brut' ou 'amort'."""
    meilleur = (None, None, -1)
    for ref, _, bruts, amorts in POSTES_ACTIF:
        if bruts is None:
            continue
        for col, prefixes in (("brut", bruts), ("amort", amorts)):
            longueur = _plus_long_prefixe(numero, prefixes)
            if longueur > meilleur[2]:
                meilleur = (ref, col, longueur)
    return meilleur[0], meilleur[1]


def _rubrique_passif(numero):
    meilleur = (None, -1)
    for ref, _, prefixes in POSTES_PASSIF:
        if prefixes is None:
            continue
        longueur = _plus_long_prefixe(numero, prefixes)
        if longueur > meilleur[1]:
            meilleur = (ref, longueur)
    return meilleur[0]


def bilan(date_fin, exercice=None):
    soldes = soldes_par_compte(date_fin, exercice=exercice)
    actif = {ref: {"brut": ZERO, "amort": ZERO} for ref, *_ in POSTES_ACTIF}
    passif = {ref: ZERO for ref, *_ in POSTES_PASSIF}
    non_classes = []

    resultat_exercice = ZERO
    for numero, solde in soldes.items():
        if not solde:
            continue
        classe = numero[0]
        if classe in "678":
            resultat_exercice -= solde  # produits (créditeurs) - charges (débitrices)
            continue
        if classe == "9":
            continue

        if classe in COMPTES_A_SENS_VARIABLE:
            ref_actif, col = _rubrique_actif(numero)
            if col == "amort":
                actif[ref_actif]["amort"] += -solde
            elif solde > 0:
                # Solde débiteur → actif (créances / disponibilités)
                actif[ref_actif or ("BJ" if classe == "4" else "BS")]["brut"] += solde
            else:
                # Solde créditeur → passif (dettes / trésorerie passive)
                passif[_rubrique_passif(numero) or ("DM" if classe == "4" else "DR")] += -solde
            continue

        ref_actif, col = _rubrique_actif(numero) if classe in "23" else (None, None)
        if ref_actif:
            actif[ref_actif][col] += solde if col == "brut" else -solde
            continue
        ref_passif = _rubrique_passif(numero)
        if ref_passif:
            passif[ref_passif] += -solde
        else:
            non_classes.append((numero, solde))

    passif["CJ"] += resultat_exercice

    for ref, composants in TOTAUX_ACTIF.items():
        actif[ref] = {
            "brut": sum(actif[r]["brut"] for r in composants),
            "amort": sum(actif[r]["amort"] for r in composants),
        }
    for ref, composants in TOTAUX_PASSIF.items():
        passif[ref] = sum(passif[r] for r in composants)

    lignes_actif = []
    for ref, libelle, bruts, _ in POSTES_ACTIF:
        v = actif[ref]
        lignes_actif.append({"ref": ref, "libelle": libelle, "brut": v["brut"], "amort": v["amort"],
                             "net": v["brut"] - v["amort"], "total": bruts is None})
    total_actif = {
        "brut": sum(actif[r]["brut"] for r in ("AZ", "BK", "BT", "BU")),
        "amort": sum(actif[r]["amort"] for r in ("AZ", "BK", "BT", "BU")),
    }
    total_actif["net"] = total_actif["brut"] - total_actif["amort"]

    lignes_passif = [{"ref": ref, "libelle": libelle, "montant": passif[ref], "total": prefixes is None}
                     for ref, libelle, prefixes in POSTES_PASSIF]
    total_passif = passif["DF"] + passif["DP"] + passif["DT"] + passif["DV"]

    return {
        "actif": lignes_actif,
        "passif": lignes_passif,
        "total_actif": total_actif,
        "total_passif": total_passif,
        "resultat": resultat_exercice,
        "equilibre": total_actif["net"] == total_passif,
        "non_classes": non_classes,
    }
