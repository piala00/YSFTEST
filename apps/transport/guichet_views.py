"""Parcours explicites : réutilisation des tronçons et incidents existants."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core import droits
from .forms import TransitDepartForm, TransitPlacementForm, TransvasementForm
from .models import Depart, Troncon
from .models_incidents import Incident


def _mode_suite(mode):
    return "&mode=" + mode if mode in ("transit", "correspondance") else ""


def _droit_operation(request, code):
    module = droits.module_de(reverse("transport:billets_transit"))
    acces = droits.Droits(request.user, module)
    if not acces.permet(code, droits.ECRIRE) or not acces.permet("billetterie.departs", droits.ECRIRE):
        raise PermissionDenied


@login_required
def billets_transit(request):
    choix = TransitDepartForm(request.GET or None)
    depart = choix.cleaned_data["depart"] if choix.is_valid() else None
    placement = TransitPlacementForm(request.POST if request.method == "POST" else None)
    erreur = ""
    if request.method == "POST":
        _droit_operation(request, "billetterie.transit")
        if depart is None:
            erreur = "Choisissez un départ local encore programmé."
        elif placement.is_valid():
            try:
                identifiant = int(request.POST.get("troncon", ""))
                with transaction.atomic():
                    depart = Depart.objects.select_for_update().get(pk=depart.pk)
                    depart.ouvert_a_la_vente()
                    t = get_object_or_404(Troncon.objects.select_for_update(), pk=identifiant)
                    siege = placement.cleaned_data["siege"]
                    if t.depart_id == depart.pk and t.siege == siege and t.statut == Troncon.A_VOYAGER:
                        if t.billet.statut == t.billet.ANNULE:
                            raise ValidationError("Ce billet est annulé.")
                    else:
                        if t.depart_id is not None or not depart.correspondances_a_affecter().filter(pk=t.pk).exists():
                            raise ValidationError("Ce billet n'est plus en attente pour ce trajet. Actualisez la liste.")
                        t.affecter(depart, siege)
                messages.success(request, f"Billet {t.billet.numero} placé : aucun nouvel encaissement.")
                if request.POST.get("imprimer"):
                    return redirect(reverse("transport:billet_imprimer", args=[t.billet_id]) + f"?transit={depart.pk}")
                return redirect(reverse("transport:billets_transit") + f"?depart={depart.pk}")
            except (ValidationError, ValueError, TypeError) as exc:
                erreur = " ".join(exc.messages) if isinstance(exc, ValidationError) else "Billet non reconnu."
    attentes = depart.correspondances_a_affecter().order_by("billet__numero", "ordre") if depart else Troncon.objects.none()
    recherche = request.GET.get("q", "").strip()
    if recherche:
        attentes = attentes.filter(billet__numero__icontains=recherche)
    return render(request, "transport/transit.html", {
        "choix": choix, "depart": depart, "attentes": attentes[:100], "placement": placement,
        "erreur": erreur, "recherche": recherche})


@login_required
def transvasement(request):
    _droit_operation(request, "billetterie.transvasement")
    initial = {}
    if request.GET.get("depart", "").isdecimal():
        initial["depart"] = request.GET["depart"]
    form = TransvasementForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            incident = Incident.transborder(d["depart"], d["part_restante"], d["vehicule_secours"], d["lieu"],
                                           d["description"], request.user)
            messages.success(request, f"Transvasement {incident.numero} enregistré, sans nouvelle vente de billets.")
            return redirect("transport:depart_detail", incident.depart_id)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, "transport/transvasement.html", {"form": form})
