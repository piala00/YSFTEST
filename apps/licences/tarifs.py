"""Barème des licences en FCFA (XAF).

Valeurs de départ validées le 2026-11-04, **modifiables** par le propriétaire (ce sont les
défauts de la grille). Deux formules au choix : **abonnement** récurrent, ou **licence
définitive + maintenance annuelle**. Base de calcul : par agence/société + par poste + par
module optionnel.

Règle AGENTS.md : **aucune taxe n'est inventée**. La TVA/les taxes ne sont pas incluses ; le
propriétaire les fixe selon la réglementation. Ce module ne calcule que le prix hors taxes.
"""
from decimal import Decimal

DEVISE = "FCFA"

# --- Abonnement (récurrent) : prix unitaires mensuel / annuel ------------------
# L'annuel offre ~2 mois (10 × le mensuel).
ABONNEMENT = {
    "base_agence": {"mensuel": 35000, "annuel": 350000},
    "poste_supplementaire": {"mensuel": 12000, "annuel": 120000},
    "module_optionnel": {"mensuel": 6000, "annuel": 60000},
}

# --- Licence définitive (paiement unique) + maintenance ------------------------
DEFINITIVE = {
    "base_agence": 700000,
    "poste": 150000,
    "module": 120000,
    "maintenance_taux": Decimal("0.18"),   # 18 % du total de la licence, par an
}

PERIODES = ("mensuel", "annuel")


def _entier(valeur, minimum=0):
    """Convertit en entier positif, borne au minimum (ne lève jamais : saisie client tolérée)."""
    try:
        n = int(valeur)
    except (TypeError, ValueError):
        n = minimum
    return max(minimum, n)


def _ligne(libelle, quantite, prix_unitaire):
    return {"libelle": libelle, "quantite": quantite, "prix_unitaire": int(prix_unitaire),
            "total": int(quantite) * int(prix_unitaire)}


def devis_abonnement(agences=1, postes=1, modules=0, periode="mensuel"):
    """Devis d'abonnement. Un poste est inclus par agence ; les postes au-delà sont facturés.

    Renvoie ``{"formule", "periode", "lignes": [...], "total", "devise"}``.
    """
    if periode not in PERIODES:
        periode = "mensuel"
    agences = _entier(agences, 1)
    postes = _entier(postes, agences)          # au moins un poste par agence
    modules = _entier(modules, 0)
    postes_sup = max(0, postes - agences)
    p = ABONNEMENT
    lignes = [_ligne("Abonnement de base par agence/société", agences,
                     p["base_agence"][periode])]
    if postes_sup:
        lignes.append(_ligne("Poste supplémentaire", postes_sup,
                             p["poste_supplementaire"][periode]))
    if modules:
        lignes.append(_ligne("Module optionnel", modules, p["module_optionnel"][periode]))
    total = sum(x["total"] for x in lignes)
    return {"formule": "abonnement", "periode": periode, "lignes": lignes,
            "total": total, "devise": DEVISE}


def abonnement_compare(agences=1, postes=1, modules=0):
    """Abonnement mensuel et annuel sur les mêmes lignes (pour un tableau à deux colonnes).

    Renvoie ``{"lignes": [{"libelle","quantite","mensuel","annuel"}], "total_mensuel",
    "total_annuel", "devise"}``.
    """
    mensuel = devis_abonnement(agences, postes, modules, "mensuel")
    annuel = devis_abonnement(agences, postes, modules, "annuel")
    lignes = []
    for lm, la in zip(mensuel["lignes"], annuel["lignes"]):
        lignes.append({"libelle": lm["libelle"], "quantite": lm["quantite"],
                       "mensuel": lm["total"], "annuel": la["total"]})
    return {"lignes": lignes, "total_mensuel": mensuel["total"],
            "total_annuel": annuel["total"], "devise": DEVISE}


def devis_definitive(agences=1, postes=1, modules=0):
    """Devis de licence définitive + maintenance annuelle (18 % du total de la licence).

    Renvoie ``{"formule", "lignes", "licence", "maintenance_annuelle", "total_premiere_annee",
    "devise"}``.
    """
    agences = _entier(agences, 1)
    postes = _entier(postes, agences)
    modules = _entier(modules, 0)
    d = DEFINITIVE
    lignes = [_ligne("Licence définitive — base par agence/société", agences, d["base_agence"]),
              _ligne("Licence définitive — par poste", postes, d["poste"])]
    if modules:
        lignes.append(_ligne("Licence définitive — par module", modules, d["module"]))
    licence = sum(x["total"] for x in lignes)
    maintenance = int((Decimal(licence) * d["maintenance_taux"]).to_integral_value())
    return {"formule": "definitive", "lignes": lignes, "licence": licence,
            "maintenance_taux_pourcent": int(d["maintenance_taux"] * 100),
            "maintenance_annuelle": maintenance,
            "total_premiere_annee": licence + maintenance, "devise": DEVISE}


def grille(agences=1, postes=1, modules=0):
    """Les deux formules côte à côte pour l'affichage (essai) et le devis (outil éditeur)."""
    return {
        "devise": DEVISE,
        "parametres": {"agences": _entier(agences, 1),
                       "postes": _entier(postes, _entier(agences, 1)),
                       "modules": _entier(modules, 0)},
        "abonnement": abonnement_compare(agences, postes, modules),
        "definitive": devis_definitive(agences, postes, modules),
    }
