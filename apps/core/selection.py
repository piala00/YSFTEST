"""Fenêtre de sélection des états, comme dans Sage 100.

Quand on ouvre un état depuis les menus, une fenêtre « Sélection » s'affiche d'abord : on y choisit la période,
le tiers, le dépôt, l'article, les comptes… puis « OK » affiche l'état. Le résultat porte alors un bandeau qui
rappelle la sélection, avec « Modifier la sélection », « Imprimer » et « Exporter ».

Chaque état déclare ses critères dans ETATS (nom d'URL → critères). Les paramètres déjà présents dans le lien
du menu (type de tiers, comptes 4 à 4, vue…) préremplissent la fenêtre.
"""
import datetime
from urllib.parse import urlencode

from django.http import QueryDict
from django.shortcuts import render

# Critère → champs de la requête qu'il occupe
CHAMPS = {
    "periode": ("date_debut", "date_fin"),
    "date": ("date",),
    "comptes": ("compte_debut", "compte_fin"),
    "journal": ("journal",),
    "type_tiers": ("type",),
    "tiers": ("tiers",),
    "depot": ("depot",),
    "famille": ("famille",),
    "article": ("article",),
    "anciennete": ("d_apres", "delai1", "delai2", "delai3"),   # balance âgée (Sage P008)
}

TIERS = ["type_tiers", "tiers"]
# nom d'URL → (critères, paramètre d'export ou None)
ETATS = {
    # Comptabilité
    "comptabilite:balance": (["periode", "comptes"], "csv"),
    "comptabilite:grand_livre": (["periode", "comptes", "tiers"], "csv"),
    "comptabilite:journal": (["periode", "journal"], None),
    "comptabilite:balance_agee": (["date"] + TIERS + ["anciennete"], None),
    "comptabilite:justificatif_solde": (["date"] + TIERS, None),
    "comptabilite:statistiques_tiers": (["periode"] + TIERS, "csv"),
    "comptabilite:bilan": (["periode"], None),
    "comptabilite:compte_resultat": (["periode"], None),
    "comptabilite:tva": (["periode"], None),
    "comptabilite:balance_analytique": (["periode"], None),
    "comptabilite:controle_liaison": (["periode"], None),
    # Gestion commerciale
    "commercial:mouvements": (["periode", "depot", "famille", "article"], None),
    "commercial:etat_inventaire": (["date", "depot"], None),
    "commercial:statistique": (["periode", "tiers", "depot", "famille", "article"], "csv"),
    "commercial:etat_ventes": (["periode"], None),
    "commercial:etat_achats": (["periode"], "csv"),
    "commercial:etat_balance_agee": (["date"] + TIERS + ["anciennete"], None),
    # Reporting
    "reporting:ventes": (["periode"], None),
    "reporting:balance_agee": (["date"] + TIERS + ["anciennete"], None),
    "reporting:bilan": (["periode"], None),
    "reporting:compte_resultat": (["periode"], None),
}


def _nom(request):
    match = getattr(request, "resolver_match", None)
    return match.view_name if match else ""


def criteres_de(request):
    """(critères, export) de l'état demandé, ou None si la page n'est pas un état."""
    nom = _nom(request)
    if nom not in ETATS:
        return None
    criteres, export = ETATS[nom]
    if nom == "commercial:statistique":
        from apps.reporting import statistiques

        code = request.resolver_match.kwargs.get("code")
        if code not in statistiques.ETATS:
            return None
        if not statistiques.ETATS[code][1]:                     # état sans période (listes, relevés à date)
            criteres = [c for c in criteres if c != "periode"]
    return criteres, export


def _valeurs_par_defaut():
    from .models import Exercice

    exercice = Exercice.courant()
    aujourdhui = datetime.date.today()
    return {
        "date_debut": (exercice.date_debut if exercice else aujourdhui.replace(month=1, day=1)).isoformat(),
        "date_fin": (exercice.date_fin if exercice else aujourdhui).isoformat(),
        "date": aujourdhui.isoformat(),
        # Balance âgée : date d'écriture, délais 30 / 45 / 60 jours (manuel Sage historique 8.50, non confirmé en V12)
        "d_apres": "ECRITURE", "delai1": "30", "delai2": "45", "delai3": "60",
    }


def _choix(critere, valeurs):
    """Listes déroulantes de la fenêtre de sélection."""
    if critere == "journal":
        from apps.comptabilite.models import Journal

        return [(j.code, f"{j.code} - {j.intitule}", "") for j in Journal.objects.all()]
    if critere == "tiers":
        from apps.commercial.models import Tiers

        qs = Tiers.objects.filter(actif=True).order_by("nom")
        return [(str(t.pk), f"{t.code} - {t.nom}", t.type_tiers) for t in qs]
    if critere == "depot":
        from apps.commercial.models import Depot

        return [(str(d.pk), str(d), "") for d in Depot.objects.all()]
    if critere == "famille":
        from apps.commercial.models import FamilleArticle

        return [(str(f.pk), str(f), "") for f in FamilleArticle.objects.all()]
    if critere == "article":
        from apps.commercial.models import Article

        return [(str(a.pk), f"{a.reference} - {a.designation}", "")
                for a in Article.objects.filter(actif=True).order_by("reference")]
    return []


def fenetre(request):
    """Page « Sélection » affichée avant l'état."""
    criteres, _ = criteres_de(request)
    valeurs = {**_valeurs_par_defaut(), **{k: v for k, v in request.GET.items()}}
    occupes = {champ for c in criteres for champ in CHAMPS[c]}
    caches = [(k, v) for k, v in request.GET.items() if k not in occupes and k not in ("ok", "page")]
    champs = [{"critere": c, "choix": _choix(c, valeurs)} for c in criteres]
    delais = [("delai1", "1er délai"), ("delai2", "2ème délai"), ("delai3", "3ème délai")]
    return render(request, "core/selection.html", {"champs": champs, "valeurs": valeurs, "caches": caches, "delais": delais})


def resume(request):
    """Bandeau du résultat : rappel de la sélection, liens Modifier / Exporter."""
    infos = criteres_de(request)
    if infos is None or request.GET.get("ok") != "1":
        return None
    criteres, export = infos
    g = request.GET
    morceaux = []

    def date_fr(v):
        try:
            return datetime.date.fromisoformat(v).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return v

    for c in criteres:
        if c == "periode" and g.get("date_debut"):
            morceaux.append(f"du {date_fr(g['date_debut'])} au {date_fr(g.get('date_fin', ''))}")
        elif c == "date" and g.get("date"):
            morceaux.append(f"au {date_fr(g['date'])}")
        elif c == "comptes" and (g.get("compte_debut") or g.get("compte_fin")):
            morceaux.append(f"comptes {g.get('compte_debut') or '…'} à {g.get('compte_fin') or '…'}")
        elif c == "anciennete" and g.get("delai1"):
            morceaux.append(f"d'après la date d'{'échéance' if g.get('d_apres') == 'ECHEANCE' else 'écriture'}, "
                            f"délais {g.get('delai1')} / {g.get('delai2')} / {g.get('delai3')} j")
        elif c == "type_tiers" and g.get("type"):
            morceaux.append("clients" if g["type"] == "CLIENT" else "fournisseurs")
        elif c in ("journal", "tiers", "depot", "famille", "article"):
            valeur = g.get(c)
            libelle = {v: lib for v, lib, _ in _choix(c, g)}.get(valeur) if valeur else None
            vides = {"journal": "tous les journaux", "tiers": "tous les tiers", "depot": "tous les dépôts",
                     "famille": "toutes les familles", "article": "tous les articles"}
            morceaux.append(libelle or vides[c])
    modifier = g.copy()
    modifier.pop("ok", None)
    modifier.pop("page", None)
    lien_export = None
    if export:
        params = g.copy()
        params["export"] = export
        lien_export = f"{request.path}?{params.urlencode()}"
    return {"texte": " · ".join(morceaux), "modifier": f"{request.path}?{modifier.urlencode()}", "export": lien_export}


class SelectionMiddleware:
    """Ouvre la fenêtre de sélection avant chaque état (sauf si « ok=1 » ou un export est demandé)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != "GET" or not request.user.is_authenticated:
            return None
        if request.GET.get("ok") == "1" or request.GET.get("export") or criteres_de(request) is None:
            return None
        return fenetre(request)


def lien_etat(url, **params):
    """URL d'un état avec sa sélection déjà faite (liens internes : balance → grand-livre…)."""
    return f"{url}?{urlencode({**params, 'ok': 1})}"
