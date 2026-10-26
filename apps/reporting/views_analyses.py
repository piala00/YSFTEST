"""Écrans du reporting construits sur les états généraux et analytiques (même période en un clic, impression, CSV)."""
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse

from apps.comptabilite import plan_analytique as pa
from apps.comptabilite.views_analytique import _contexte_periode, _csv

from . import analyses


def _axe(request, defaut="vehicules"):
    codes = [c for c, _, _ in pa.axes()]
    axe = request.GET.get("axe") or (defaut if defaut in codes else (codes[0] if codes else ""))
    if axe not in codes:
        raise Http404("Axe analytique inconnu")
    return axe, [(c, t) for c, t, _ in pa.axes()]


def _contexte(request, defaut_periode="mois"):
    """Période commune ; par défaut le mois (ou l'année pour les tableaux mensuels)."""
    params = request.GET.copy()
    if not any(params.get(k) for k in ("du", "au", "periode", "mois")):
        params["periode"] = defaut_periode
    request.GET = params
    p = _contexte_periode(request)
    p["export_url"] = request.path + "?" + urlencode({**{k: v for k, v in request.GET.items() if k != "export"},
                                                      "du": p["du"].isoformat(), "au": p["au"].isoformat(), "export": "csv"})
    return p


@login_required
def catalogue(request):
    p = _contexte(request)
    familles = []
    for famille, etats in analyses.catalogue():
        liens = []
        for titre, nom, args, query, description in etats:
            try:
                url = reverse(nom, args=args)
            except NoReverseMatch:
                continue
            liens.append({"titre": titre, "url": url + "?" + urlencode({**query, "du": p["du"].isoformat(),
                                                                         "au": p["au"].isoformat(),
                                                                         "date_debut": p["du"].isoformat(),
                                                                         "date_fin": p["au"].isoformat()}),
                          "description": description})
        familles.append((famille, liens))
    return render(request, "reporting/catalogue.html", {**p, "familles": familles, "export_url": ""})


@login_required
def evolution(request):
    p = _contexte(request, "annee")
    r = analyses.evolution_societe(p["du"], p["au"])
    if request.GET.get("export") == "csv":
        return _csv(f"evolution-{p['du']}-{p['au']}", ["Mois", "Produits", "Charges", "Résultat", "Trésorerie", "Clients",
                                                       "Fournisseurs", "Propriétaires"],
                    [[f"{l['mois']:%m/%Y}", l["produits"], l["charges"], l["resultat"], l["tresorerie"], l["clients"],
                      l["fournisseurs"], l["proprietaires"]] for l in r["lignes"]])
    return render(request, "reporting/evolution.html", {**p, **r})


@login_required
def comparaison(request):
    p = _contexte(request)
    axe, axes = _axe(request)
    mode = request.GET.get("comparer", "precedente")
    if mode == "n1":
        b = pa.annee_precedente(p["du"], p["au"])
    elif mode == "libre":
        lu = pa.lire_periode({"du": request.GET.get("du_b", ""), "au": request.GET.get("au_b", "")})
        b = (lu["du"], lu["au"])
    else:
        b = pa.periode_precedente(p["du"], p["au"])
    r = analyses.comparaison_axe(axe, (p["du"], p["au"]), b)
    if request.GET.get("export") == "csv":
        return _csv(f"comparaison-{axe}-{p['du']}-{p['au']}",
                    ["Élément", "Produits A", "Charges A", "Résultat A", "Produits B", "Charges B", "Résultat B", "Écart", "Variation %"],
                    [[g["libelle"], g["a"]["produits"], g["a"]["charges"], g["a"]["resultat"], g["b"]["produits"],
                      g["b"]["charges"], g["b"]["resultat"], g["ecart"], g["variation"]] for g in r["lignes"]])
    return render(request, "reporting/comparaison.html", {**p, **r, "axe": axe, "axes": axes, "titre_axe": dict(axes)[axe],
                                                         "comparer": mode, "periode_b": b})


@login_required
def matrice(request):
    p = _contexte(request, "annee")
    axe, axes = _axe(request)
    indicateur = request.GET.get("indicateur", "resultat")
    if indicateur not in dict(analyses.INDICATEURS):
        indicateur = "resultat"
    r = analyses.matrice_axe(axe, p["du"], p["au"], indicateur)
    if request.GET.get("export") == "csv":
        return _csv(f"mensuel-{axe}-{indicateur}-{p['du']}-{p['au']}", ["Élément"] + [f"{m:%m/%Y}" for m in r["mois"]] + ["Total"],
                    [[l["libelle"], *l["valeurs"], l["total"]] for l in r["lignes"]] + [["Total", *r["totaux"], r["total"]]])
    return render(request, "reporting/matrice.html", {**p, **r, "axe": axe, "axes": axes, "titre_axe": dict(axes)[axe],
                                                     "indicateur": indicateur, "indicateurs": analyses.INDICATEURS})


@login_required
def classement(request):
    p = _contexte(request)
    axe, axes = _axe(request)
    critere = request.GET.get("critere", "resultat")
    if critere not in dict(analyses.CRITERES):
        critere = "resultat"
    try:
        nombre = max(1, min(int(request.GET.get("nombre", 10)), 100))
    except ValueError:
        nombre = 10
    r = analyses.classement(axe, p["du"], p["au"], critere, nombre)
    if request.GET.get("export") == "csv":
        return _csv(f"classement-{axe}-{critere}-{p['du']}-{p['au']}", ["Rang", "Élément", "Produits", "Charges", "Résultat", "Marge %"],
                    [[i, e["libelle"], e["produits"], e["charges"], e["resultat"], e["marge"]] for i, e in enumerate(r["meilleurs"], 1)])
    return render(request, "reporting/classement.html", {**p, **r, "axe": axe, "axes": axes, "titre_axe": dict(axes)[axe],
                                                        "critere": critere, "criteres": analyses.CRITERES, "nombre": nombre})
