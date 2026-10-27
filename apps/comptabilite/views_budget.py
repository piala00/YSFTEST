"""Budgets (société ou plan analytique) et état budget / réel."""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.models import Exercice

from . import budget as service
from . import plan_analytique as pa
from .models import Budget, LigneBudget
from .views_analytique import _contexte_periode, _csv


def _decimal(valeur):
    try:
        return Decimal(str(valeur or "0").replace(" ", "").replace(" ", "").replace(",", "."))
    except InvalidOperation:
        raise ValidationError(f"Montant incorrect : « {valeur} ».")


@login_required
def budgets(request):
    if request.method == "POST":
        try:
            exercice = get_object_or_404(Exercice, pk=request.POST.get("exercice"))
            axe = request.POST.get("axe", "")
            if axe and pa.titre_axe(axe) is None:
                raise ValidationError("Plan analytique inconnu.")
            nom = request.POST.get("nom", "").strip()
            if not nom:
                raise ValidationError("Donnez un nom au budget.")
            if Budget.objects.filter(exercice=exercice, nom=nom).exists():
                raise ValidationError("Un budget porte déjà ce nom pour cet exercice.")
            b = Budget.objects.create(exercice=exercice, nom=nom, axe=axe, cree_par=request.user.get_username())
            messages.success(request, f"Budget « {b.nom} » créé : ajoutez ses lignes, ou préremplissez-le avec le réel.")
            return redirect("analytique:budget", pk=b.pk)
        except ValidationError as exc:
            for m in exc.messages:
                messages.error(request, m)
    liste = Budget.objects.select_related("exercice")
    return render(request, "analytique/budgets.html", {
        "budgets": [(b, pa.titre_axe(b.axe) if b.axe else "Société entière") for b in liste],
        "exercices": Exercice.objects.all(), "axes": [(c, t) for c, t, _ in pa.axes()]})


@login_required
def budget(request, pk):
    b = get_object_or_404(Budget.objects.select_related("exercice"), pk=pk)
    mois = service.mois_exercice(b.exercice)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action in ("ajouter", "supprimer", "preremplir") and b.statut == Budget.VALIDE:
                raise ValidationError("Budget validé : rouvrez-le pour le modifier.")
            if action == "ajouter":
                element = request.POST.get("element", "") if b.axe else ""
                compte = service.verifier_ligne(b, element, request.POST.get("compte"))
                l = LigneBudget(budget=b, element=element, compte=compte, libelle=request.POST.get("libelle", "")[:100])
                if request.POST.get("repartition") == "mois":
                    valeurs = [_decimal(request.POST.get(m)) for m in LigneBudget.MOIS[:len(mois)]]
                else:
                    valeurs = service.repartir(_decimal(request.POST.get("annuel")), len(mois))
                if any(v < 0 for v in valeurs):
                    raise ValidationError("Saisissez des montants positifs (produits et charges).")
                for nom_mois, v in zip(LigneBudget.MOIS, valeurs):
                    setattr(l, nom_mois, v)
                l.save()
                messages.success(request, f"Ligne {compte} ajoutée.")
            elif action == "supprimer":
                b.lignes.filter(pk=request.POST.get("ligne")).delete()
            elif action == "preremplir":
                reference = get_object_or_404(Exercice, pk=request.POST.get("reference"))
                n = service.preremplir(b, reference, _decimal(request.POST.get("hausse") or 0))
                messages.success(request, f"{n} ligne(s) créée(s) d'après le réel de {reference}.")
            elif action in ("valider", "rouvrir"):
                b.statut = Budget.VALIDE if action == "valider" else Budget.BROUILLON
                b.save(update_fields=["statut"])
            return redirect("analytique:budget", pk=b.pk)
        except ValidationError as exc:
            for m in exc.messages:
                messages.error(request, m)
    lignes = list(b.lignes.all())
    noms = dict(service.elements_proposes(b.axe, b.exercice)) if b.axe else {}
    totaux = {"produits": sum((l.total for l in lignes if l.produit), Decimal("0")),
              "charges": sum((l.total for l in lignes if not l.produit), Decimal("0"))}
    totaux["resultat"] = totaux["produits"] - totaux["charges"]
    return render(request, "analytique/budget.html", {
        "b": b, "mois": mois, "lignes": [(l, noms.get(l.element, l.element)) for l in lignes], "totaux": totaux,
        "elements": list(noms.items()), "titre_axe": pa.titre_axe(b.axe) if b.axe else "Société entière",
        "references": Exercice.objects.exclude(pk=b.exercice_id), "champs_mois": list(zip(LigneBudget.MOIS, mois))})


@login_required
def budget_reel(request, pk):
    b = get_object_or_404(Budget.objects.select_related("exercice"), pk=pk)
    if not request.GET.get("du") and not request.GET.get("periode") and not request.GET.get("mois"):
        params = request.GET.copy()
        params["du"], params["au"] = b.exercice.date_debut.isoformat(), b.exercice.date_fin.isoformat()
        request.GET = params
    p = _contexte_periode(request)
    r = service.rapport(b, p["du"], p["au"])
    vue = request.GET.get("vue", "elements" if b.axe else "comptes")
    if request.GET.get("export") == "csv":
        return _csv(f"budget-reel-{b.pk}", ["Élément", "Compte", "Libellé", "Budget", "Réel", "Écart", "Réalisation %"],
                    [[l["element_nom"], l["compte"], l["libelle"], l["budget"], l["reel"], l["ecart"],
                      "" if l["taux"] is None else l["taux"]] for l in r["lignes"] + r["hors_budget"]])
    return render(request, "analytique/budget_reel.html", {
        **p, **r, "b": b, "vue": vue, "titre_axe": pa.titre_axe(b.axe) if b.axe else "Société entière"})
