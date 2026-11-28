"""Logiciel Personnel et paie."""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.comptabilite.models import Journal

from .forms import AvanceForm, EmployeForm, RubriqueForm
from .models import Avance, Bulletin, Employe, PeriodePaie, RubriquePaie


def _erreur(request, exc):
    messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))


@login_required
def employes(request):
    qs = Employe.objects.select_related("agence", "vehicule")
    if request.GET.get("service"):
        qs = qs.filter(service=request.GET["service"])
    if not request.GET.get("tous"):
        qs = qs.filter(actif=True)
    return render(request, "personnel/employes.html", {
        "employes": qs, "services": Employe.SERVICES, "service": request.GET.get("service", ""),
        "masse": qs.aggregate(t=Sum("salaire_base"))["t"] or 0})


@login_required
def employe_form(request, pk=None):
    instance = get_object_or_404(Employe, pk=pk) if pk else None
    form = EmployeForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fiche enregistrée.")
        return redirect("personnel:employes")
    return render(request, "core/form.html", {"form": form, "titre": f"Employé {instance}" if instance else "Nouvel employé"})


@login_required
def rubriques(request):
    return render(request, "personnel/rubriques.html", {"rubriques": RubriquePaie.objects.select_related("compte", "compte_contrepartie")})


@login_required
def rubrique_form(request, pk=None):
    instance = get_object_or_404(RubriquePaie, pk=pk) if pk else None
    form = RubriqueForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Rubrique enregistrée.")
        return redirect("personnel:rubriques")
    return render(request, "core/form.html", {"form": form, "titre": "Rubrique de paie"})


@login_required
def avances(request):
    return render(request, "personnel/avances.html", {"avances": Avance.objects.select_related("employe", "bulletin__periode")[:300]})


@login_required
def avance_form(request):
    form = AvanceForm(request.POST or None, initial={"caisse": Journal.objects.filter(code="CA").first()})
    if request.method == "POST" and form.is_valid():
        try:
            avance = form.save(commit=False)
            avance.enregistrer()
            messages.success(request, f"Avance de {avance.montant:,.0f} FCFA versée à {avance.employe.nom} ; elle sera reprise sur sa prochaine paie.".replace(",", " "))
            return redirect("personnel:avances")
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Avance sur salaire"})


@login_required
def paies(request):
    if request.method == "POST":
        try:
            mois = datetime.date.fromisoformat(request.POST["mois"] + "-01")
            periode, cree = PeriodePaie.objects.get_or_create(annee=mois.year, mois=mois.month)
            if cree:
                periode.generer()
            return redirect("personnel:paie", periode.pk)
        except (KeyError, ValueError, ValidationError) as exc:
            _erreur(request, exc)
    return render(request, "personnel/paies.html", {"periodes": PeriodePaie.objects.all(),
                                                    "mois": timezone.localdate().strftime("%Y-%m")})


@login_required
def paie(request, pk):
    periode = get_object_or_404(PeriodePaie, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "generer":
                n = periode.generer()
                messages.success(request, f"{n} bulletin(s) préparé(s).")
            elif action == "valider":
                periode.valider()
                messages.success(request, "Paie validée et comptabilisée (salaires des chauffeurs sur leur véhicule).")
            elif action == "payer":
                periode.payer(get_object_or_404(Journal, pk=request.POST.get("caisse")))
                messages.success(request, "Paiement des salaires enregistré.")
        except ValidationError as exc:
            _erreur(request, exc)
        return redirect("personnel:paie", periode.pk)
    bulletins = periode.bulletins.select_related("employe__vehicule")
    totaux = {c: sum((getattr(b, c) for b in bulletins), 0) for c in ("salaire_base", "brut", "retenues", "avances", "net", "patronales")}
    return render(request, "personnel/paie.html", {
        "periode": periode, "bulletins": bulletins, "totaux": totaux,
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)})


@login_required
def bulletin(request, pk):
    b = get_object_or_404(Bulletin.objects.select_related("periode", "employe"), pk=pk)
    if request.method == "POST" and b.periode.statut == PeriodePaie.BROUILLON:
        action = request.POST.get("action")
        try:
            if action == "base":
                b.salaire_base = int(request.POST["salaire_base"])
                b.save(update_fields=["salaire_base"])
            elif action == "ajouter":
                saisi = request.POST.get("montant")
                b.lignes.create(rubrique=get_object_or_404(RubriquePaie, pk=request.POST["rubrique"]),
                                montant_saisi=int(saisi) if saisi else None)
            elif action == "retirer":
                b.lignes.filter(pk=request.POST.get("ligne")).delete()
            b.calculer()
        except (KeyError, ValueError) as exc:
            _erreur(request, exc)
        return redirect("personnel:bulletin", b.pk)
    return render(request, "personnel/bulletin.html", {
        "b": b, "lignes": b.lignes.select_related("rubrique"), "rubriques": RubriquePaie.objects.filter(actif=True),
        "modifiable": b.periode.statut == PeriodePaie.BROUILLON, "imprimer": request.GET.get("imprimer")})
