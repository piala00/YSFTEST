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


def _contexte(request, defaut_periode="mois", avec_export=True):
    """Période commune ; par défaut le mois (ou l'année pour les tableaux mensuels)."""
    params = request.GET.copy()
    if not any(params.get(k) for k in ("du", "au", "periode", "mois")):
        params["periode"] = defaut_periode
    request.GET = params
    p = _contexte_periode(request)
    params = request.GET.copy()
    params["du"], params["au"] = p["du"].isoformat(), p["au"].isoformat()
    for format, cle in (("csv", "export_url"), ("xlsx", "excel_url")):
        params["export"] = format
        p[cle] = request.path + "?" + params.urlencode() if avec_export else ""
    return p


def _exporter(request, periode, nom, entetes, lignes, **effectifs):
    if request.GET.get("export") == "csv":
        return _csv(nom, entetes, lignes)
    from .exports import exporter_excel

    params = request.GET.copy()
    params.pop("export", None)
    params["du"], params["au"] = periode["du"].isoformat(), periode["au"].isoformat()
    for cle, valeur in effectifs.items():
        params[cle] = str(valeur)
    criteres = [("Écran", request.path)] + [(cle, valeur) for cle, valeurs in params.lists() for valeur in valeurs]
    return exporter_excel(nom, entetes, lignes, criteres)


@login_required
def catalogue(request):
    p = _contexte(request, avec_export=False)
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
    return render(request, "reporting/catalogue.html", {**p, "familles": familles})


@login_required
def evolution(request):
    p = _contexte(request, "annee")
    r = analyses.evolution_societe(p["du"], p["au"])
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"evolution-{p['du']}-{p['au']}", ["Mois", "Produits", "Charges", "Résultat", "Trésorerie", "Clients",
                                                       "Fournisseurs", "Propriétaires"],
                    [[f"{l['mois']:%m/%Y}", l["produits"], l["charges"], l["resultat"], l["tresorerie"], l["clients"],
                      l["fournisseurs"], l["proprietaires"]] for l in r["lignes"]])
    return render(request, "reporting/evolution.html", {**p, **r})


@login_required
def comparaison(request):
    p = _contexte(request)
    axe, axes = _axe(request)
    mode = request.GET.get("comparer", "precedente")
    if mode not in ("precedente", "n1", "libre"):
        mode = "precedente"
    if mode == "n1":
        b = pa.annee_precedente(p["du"], p["au"])
    elif mode == "libre":
        lu = pa.lire_periode({"du": request.GET.get("du_b", ""), "au": request.GET.get("au_b", "")})
        b = (lu["du"], lu["au"])
    else:
        b = pa.periode_precedente(p["du"], p["au"])
    r = analyses.comparaison_axe(axe, (p["du"], p["au"]), b)
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"comparaison-{axe}-{p['du']}-{p['au']}",
                    ["Élément", "Produits A", "Charges A", "Résultat A", "Produits B", "Charges B", "Résultat B", "Écart", "Variation %"],
                    [[g["libelle"], g["a"]["produits"], g["a"]["charges"], g["a"]["resultat"], g["b"]["produits"],
                      g["b"]["charges"], g["b"]["resultat"], g["ecart"], g["variation"]] for g in r["lignes"]],
                         axe=axe, comparer=mode, du_b=b[0].isoformat(), au_b=b[1].isoformat())
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
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"mensuel-{axe}-{indicateur}-{p['du']}-{p['au']}", ["Élément"] + [f"{m:%m/%Y}" for m in r["mois"]] + ["Total"],
                    [[l["libelle"], *l["valeurs"], l["total"]] for l in r["lignes"]] + [["Total", *r["totaux"], r["total"]]],
                         axe=axe, indicateur=indicateur)
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
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"classement-{axe}-{critere}-{p['du']}-{p['au']}", ["Rang", "Élément", "Produits", "Charges", "Résultat", "Marge %"],
                    [[i, e["libelle"], e["produits"], e["charges"], e["resultat"], e["marge"]] for i, e in enumerate(r["meilleurs"], 1)], axe=axe, critere=critere, nombre=nombre)
    return render(request, "reporting/classement.html", {**p, **r, "axe": axe, "axes": axes, "titre_axe": dict(axes)[axe],
                                                        "critere": critere, "criteres": analyses.CRITERES, "nombre": nombre})


# ---------------------------------------------------------------- Reporting du Transport
@login_required
def transport_tableau_de_bord(request):
    from apps.transport import reporting as tr

    p = _contexte(request, avec_export=False)
    return render(request, "reporting/transport_tableau_de_bord.html", {**p, **tr.tableau_de_bord(p["du"], p["au"])})


@login_required
def transport_billetterie(request):
    from apps.transport import reporting as tr

    p = _contexte(request)
    r = tr.activite_billetterie(p["du"], p["au"])
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"billetterie-{p['du']}-{p['au']}", ["Point de vente", "Billets", "Annulés", "Bagages", "Recette billets",
                                                         "Recette bagages", "Espèces", "Mobile Money", "En compte", "Total"],
                    [[l["agence"], l["billets"], l["annules"], l["bagages_nombre"], l["billets_montant"], l["bagages_montant"],
                      l["especes"], l["mobile"], l["compte"], l["total"]] for l in r["lignes"]])
    return render(request, "reporting/transport_billetterie.html", {**p, **r})


@login_required
def transport_colis_non_livres(request):
    """Colis arrivés ou en route, pas encore livrés (ni annulés) : suivi des colis en souffrance, triés par ancienneté."""
    from apps.transport import reporting as tr

    p = _contexte(request)
    try:
        seuil = int(request.GET.get("seuil") or 7)
    except ValueError:
        seuil = 7
    r = tr.colis_non_livres(p["au"], seuil)
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"colis-non-livres-{p['au']}",
                    ["N° colis", "Enregistré le", "Jours", "Départ", "Arrivée", "Destinataire", "Téléphone", "Statut",
                     "Pièces", "En retard"],
                    [[l["numero"], l["date"], l["jours"], l["depart"], l["arrivee"], l["destinataire"], l["tel"],
                      l["statut"], l["pieces"], "oui" if l["en_retard"] else ""] for l in r["lignes"]], seuil=r["seuil"])
    return render(request, "reporting/transport_colis_non_livres.html", {**p, **r})


@login_required
def transport_colis(request):
    from apps.transport import reporting as tr

    p = _contexte(request)
    axe = request.GET.get("axe") if request.GET.get("axe") in ("depart", "arrivee", "liaison") else "depart"
    r = tr.activite_colis(p["du"], p["au"], axe)
    if request.GET.get("export") in ("csv", "xlsx"):
        return _exporter(request, p, f"colis-{p['du']}-{p['au']}", ["Regroupement", "Envois", "Annulés", "Pièces", "Poids (kg)", "Recette",
                                                   "Port dû", "Contre-remboursements", "Livrés", "En attente"],
                    [[l["cle"], l["envois"], l["annules"], l["pieces"], l["poids"], l["recette"], l["port_du"],
                      l["remboursements"], l["livres"], l["attente"]] for l in r["lignes"]], axe=axe)
    return render(request, "reporting/transport_colis.html", {**p, **r, "axe": axe, "axes_colis": [
        ("depart", "Agence de départ"), ("arrivee", "Agence d'arrivée"), ("liaison", "Liaison")]})
