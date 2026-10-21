from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.commercial.models import Tiers
from apps.comptabilite.forms import PeriodeForm
from apps.comptabilite.views import _export_csv

from . import services


@login_required
def dashboard(request):
    data = services.tableau_de_bord()
    graph = {
        "labels": [m["mois"] for m in data["ca_mensuel"]],
        "ventes": [float(m["montant"]) for m in data["ca_mensuel"]],
        "achats": [float(m["montant"]) for m in data["achats_mensuels"]],
        "clients": [c["tiers__nom"] for c in data["top_clients"]],
        "clients_ca": [float(c["total"]) for c in data["top_clients"]],
    }
    return render(request, "reporting/dashboard.html", {"d": data, "graph_json": graph})


@login_required
def ventes(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    par_client = services.ventes_par_client(p["date_debut"], p["date_fin"])
    par_article = services.ventes_par_article(p["date_debut"], p["date_fin"])
    export = request.GET.get("export")
    if export == "clients":
        return _export_csv("ventes_clients", ["Code", "Client", "Nb factures", "CA HT", "TTC", "Encours"],
                           [[l["tiers"].code, l["tiers"].nom, l["nb"], l["ca_ht"], l["ttc"], l["encours"]] for l in par_client])
    if export == "articles":
        return _export_csv("ventes_articles", ["Référence", "Désignation", "Quantité", "CA HT", "Marge", "Taux marge %"],
                           [[a["article__reference"], a["article__designation"], a["quantite"], a["total"],
                             a["marge"], round(a["taux_marge"], 2)] for a in par_article])
    return render(request, "reporting/ventes.html", {
        "form": form, "par_client": par_client, "par_article": par_article, "p": p,
        "total_ca": sum(l["ca_ht"] for l in par_client),
        "serie_json": [{"mois": m["mois"], "montant": float(m["montant"])}
                                  for m in services.ca_mensuel(p["date_debut"], p["date_fin"])],
    })


@login_required
def balance_agee(request):
    import datetime

    from django.utils.dateparse import parse_date

    type_tiers = request.GET.get("type", Tiers.CLIENT)
    date = parse_date(request.GET.get("date") or "") or datetime.date.today()
    data = services.balance_agee(type_tiers, date, tiers=request.GET.get("tiers") or None)
    return render(request, "reporting/balance_agee.html", {"data": data, "type_tiers": type_tiers, "date": date})


@login_required
def achats(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    lignes = services.achats_par_fournisseur(p["date_debut"], p["date_fin"])
    if request.GET.get("export") == "csv":
        return _export_csv("achats_fournisseurs", ["Code", "Fournisseur", "Nb factures", "Achats HT", "TTC", "Reste à payer"],
                           [[l["tiers"].code, l["tiers"].nom, l["nb"], l["ca_ht"], l["ttc"], l["encours"]] for l in lignes])
    return render(request, "reporting/achats.html", {"form": form, "lignes": lignes, "p": p,
                                                     "total": sum(l["ca_ht"] for l in lignes)})


@login_required
def statistique(request, code):
    """Etat de la Gestion commerciale (Etat › Analyse, Statistiques, Relevés, Listes)."""
    from django.http import Http404

    from . import statistiques

    if code not in statistiques.ETATS:
        raise Http404
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    etat = statistiques.calculer(code, p["date_debut"], p["date_fin"],
                                 **{k: request.GET.get(k) for k in ("tiers", "depot", "famille", "article")})
    if request.GET.get("export") == "csv":
        cles = [c for c in etat["colonnes"]]
        from apps.core.templatetags.erp import cellule
        return _export_csv(code, [c[1] for c in cles], [[cellule(l, c) for c in cles] for l in etat["lignes"]])
    return render(request, "reporting/statistique.html", {"form": form, "p": p, "etat": etat, "code": code})
