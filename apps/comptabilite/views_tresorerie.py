"""Trésorerie projetée et prévisions de trésorerie."""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Budget, PrevisionTresorerie
from .tresorerie_projetee import projection
from .views_budget import _decimal


@login_required
def tresorerie_projetee(request):
    if request.method == "POST":
        try:
            if request.POST.get("action") == "supprimer":
                PrevisionTresorerie.objects.filter(pk=request.POST.get("prevision")).delete()
            else:
                libelle = request.POST.get("libelle", "").strip()
                montant = _decimal(request.POST.get("montant"))
                if not libelle or montant <= 0:
                    raise ValidationError("Indiquez un libellé et un montant positif.")
                try:
                    date = datetime.date.fromisoformat(request.POST.get("date", ""))
                    fin = request.POST.get("jusqu_au")
                    jusqu_au = datetime.date.fromisoformat(fin) if fin else None
                except ValueError:
                    raise ValidationError("Date incorrecte.")
                PrevisionTresorerie.objects.create(
                    date=date, libelle=libelle[:100], montant=montant, jusqu_au=jusqu_au,
                    sens=PrevisionTresorerie.ENCAISSEMENT if request.POST.get("sens") == "ENCAISSEMENT"
                    else PrevisionTresorerie.DECAISSEMENT,
                    mensuelle=bool(request.POST.get("mensuelle")), cree_par=request.user.get_username())
                messages.success(request, "Prévision enregistrée.")
        except ValidationError as exc:
            for m in exc.messages:
                messages.error(request, m)
        return redirect(request.get_full_path())
    budgets = Budget.objects.filter(axe="", statut=Budget.VALIDE).select_related("exercice")
    budget = budgets.filter(pk=request.GET.get("budget")).first() if request.GET.get("budget") else None
    try:
        nombre = max(1, min(int(request.GET.get("mois") or 6), 24))
    except ValueError:
        nombre = 6
    return render(request, "comptabilite/tresorerie_projetee.html", {
        **projection(nombre_mois=nombre, budget=budget), "nombre_mois": nombre, "budgets": budgets,
        "previsions": PrevisionTresorerie.objects.all(), "sens": PrevisionTresorerie.SENS})


@login_required
def controles_cloture(request):
    """Etat › Analyse et contrôles › Contrôles de clôture : toutes les vérifications avant de clôturer."""
    from .controles import executer
    from .views_analytique import _contexte_periode

    if not request.GET.get("du") and not request.GET.get("periode") and not request.GET.get("mois"):
        params = request.GET.copy()
        params["periode"] = "exercice"
        request.GET = params
    p = _contexte_periode(request)
    return render(request, "comptabilite/controles_cloture.html", {**p, **executer(p["du"], p["au"])})
