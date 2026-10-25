"""Logiciel Garage : carburant, réparations, échéances des véhicules."""
import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.comptabilite.models import Journal
from apps.transport.models import Vehicule

from .forms import LigneReparationForm, OrdreForm, PleinForm
from .models import OrdreReparation, PleinCarburant

ZERO = Decimal("0")


def _date(request, cle, defaut):
    try:
        return datetime.date.fromisoformat(request.GET.get(cle) or "")
    except ValueError:
        return defaut


def _erreur(request, exc):
    messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))


@login_required
def pleins(request):
    fin = _date(request, "au", timezone.localdate())
    debut = _date(request, "du", fin.replace(day=1))
    qs = PleinCarburant.objects.filter(date__range=(debut, fin)).select_related("vehicule", "ecriture")
    if request.GET.get("vehicule"):
        qs = qs.filter(vehicule_id=request.GET["vehicule"])
    return render(request, "garage/pleins.html", {
        "pleins": qs, "du": debut, "au": fin, "vehicules": Vehicule.objects.all(), "vehicule": request.GET.get("vehicule", ""),
        "litres": sum((p.litres for p in qs), ZERO), "total": sum((p.montant for p in qs), ZERO)})


@login_required
def plein_form(request):
    initial = {"caisse": Journal.objects.filter(code="CA").first(), "vehicule": request.GET.get("vehicule"),
               "depart": request.GET.get("depart")}
    form = PleinForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        plein = form.save(commit=False)
        try:
            plein.enregistrer(request.user)
            conso = plein.consommation()
            messages.success(request, f"Plein {plein.numero} enregistré sur {plein.vehicule.immatriculation}"
                                      + (f" : {conso} L/100 km depuis le plein précédent." if conso else "."))
            return redirect("garage:pleins")
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Saisir un plein de carburant"})


@login_required
def reparations(request):
    statut = request.GET.get("statut", OrdreReparation.OUVERT)
    qs = OrdreReparation.objects.select_related("vehicule").prefetch_related("lignes")
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, "garage/reparations.html", {"ordres": qs[:300], "statut": statut, "statuts": OrdreReparation.STATUTS})


@login_required
def reparation_form(request):
    form = OrdreForm(request.POST or None, initial={"vehicule": request.GET.get("vehicule")})
    if request.method == "POST" and form.is_valid():
        ordre = form.save(commit=False)
        ordre.cree_par = request.user
        ordre.save()
        messages.success(request, f"Véhicule entré au garage : ordre {ordre.numero}. Ajoutez les pièces et travaux.")
        return redirect("garage:reparation", ordre.pk)
    return render(request, "core/form.html", {"form": form, "titre": "Entrée d'un véhicule au garage"})


@login_required
def reparation(request, pk):
    ordre = get_object_or_404(OrdreReparation.objects.select_related("vehicule"), pk=pk)
    form = LigneReparationForm(request.POST if request.POST.get("action") == "ligne" else None)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if ordre.statut != OrdreReparation.OUVERT:
                raise ValidationError("Cet ordre n'est plus en cours.")
            if action == "ligne" and form.is_valid():
                ligne = form.save(commit=False)
                ligne.ordre = ordre
                ligne.save()
                return redirect("garage:reparation", ordre.pk)
            if action == "supprimer":
                ordre.lignes.filter(pk=request.POST.get("ligne")).delete()
                return redirect("garage:reparation", ordre.pk)
            if action == "cloturer":
                ordre.cloturer(caisse=Journal.objects.filter(pk=request.POST.get("caisse")).first(),
                               date=datetime.date.fromisoformat(request.POST["date"]) if request.POST.get("date") else None,
                               utilisateur=request.user)
                messages.success(request, f"Réparation terminée : {ordre.cout_comptabilise:,.0f} FCFA sur le véhicule {ordre.vehicule.immatriculation}.".replace(",", " "))
                return redirect("garage:reparation", ordre.pk)
            if action == "annuler":
                if ordre.lignes.exists():
                    raise ValidationError("Retirez d'abord les lignes.")
                ordre.statut = OrdreReparation.ANNULE
                ordre.save(update_fields=["statut"])
                return redirect("garage:reparations")
        except (ValidationError, ValueError) as exc:
            _erreur(request, exc)
    return render(request, "garage/reparation.html", {
        "ordre": ordre, "lignes": ordre.lignes.select_related("fournisseur"), "form": form,
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE), "aujourdhui": timezone.localdate()})


@login_required
def consommation(request):
    """Carburant et consommation de chaque véhicule sur la période (relevés de compteur aux pleins)."""
    from apps.transport.etats import activite_vehicule

    fin = _date(request, "au", timezone.localdate())
    debut = _date(request, "du", fin.replace(day=1))
    lignes = [{"vehicule": v, **activite_vehicule(v, debut, fin)} for v in Vehicule.objects.filter(actif=True)]
    return render(request, "garage/consommation.html", {"du": debut, "au": fin, "lignes": lignes})


@login_required
def echeances(request):
    """Papiers des véhicules : assurance et visite technique expirées ou à renouveler."""
    vehicules = [(v, v.alertes()) for v in Vehicule.objects.filter(actif=True)]
    return render(request, "garage/echeances.html", {"vehicules": vehicules})
