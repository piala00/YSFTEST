import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.commercial.models import Tiers
from apps.core.models import Exercice, Sequence

from . import etats, services
from .forms import CompteForm, EcritureForm, JournalForm, LigneEcritureFormSet, PeriodeForm
from .models import CLASSES_SYSCOHADA, Compte, Ecriture, Journal, LigneEcriture


# ---------------------------------------------------------------- Paramétrage
class CompteListView(LoginRequiredMixin, ListView):
    model = Compte
    template_name = "comptabilite/compte_list.html"

    def get_queryset(self):
        qs = Compte.objects.all()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(numero__startswith=q) | Q(intitule__icontains=q))
        classe = self.request.GET.get("classe")
        if classe:
            qs = qs.filter(numero__startswith=classe)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = CLASSES_SYSCOHADA.items()
        return ctx


class CompteCreateView(LoginRequiredMixin, CreateView):
    model = Compte
    form_class = CompteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:comptes")
    extra_context = {"titre": "Nouveau compte"}


class CompteUpdateView(LoginRequiredMixin, UpdateView):
    model = Compte
    form_class = CompteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:comptes")
    extra_context = {"titre": "Modifier le compte"}


class JournalListView(LoginRequiredMixin, ListView):
    model = Journal
    template_name = "comptabilite/journal_list.html"


class JournalCreateView(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:journaux")
    extra_context = {"titre": "Nouveau journal"}


class JournalUpdateView(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = JournalForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:journaux")
    extra_context = {"titre": "Modifier le journal"}


# ---------------------------------------------------------------- Écritures
class EcritureListView(LoginRequiredMixin, ListView):
    model = Ecriture
    template_name = "comptabilite/ecriture_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = Ecriture.objects.select_related("journal").annotate(total=Sum("lignes__debit")).order_by("-date", "-numero")
        g = self.request.GET
        if g.get("journal"):
            qs = qs.filter(journal__code=g["journal"])
        if g.get("statut"):
            qs = qs.filter(statut=g["statut"])
        if g.get("du"):
            qs = qs.filter(date__gte=g["du"])
        if g.get("au"):
            qs = qs.filter(date__lte=g["au"])
        if g.get("q"):
            qs = qs.filter(Q(numero__icontains=g["q"]) | Q(libelle__icontains=g["q"]) | Q(reference__icontains=g["q"]))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["journaux"] = Journal.objects.all()
        return ctx


class EcritureDetailView(LoginRequiredMixin, DetailView):
    model = Ecriture
    template_name = "comptabilite/ecriture_detail.html"


def _ecriture_form(request, ecriture):
    if request.method == "POST":
        form = EcritureForm(request.POST, instance=ecriture)
        formset = LigneEcritureFormSet(request.POST, instance=ecriture)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    ecr = form.save(commit=False)
                    ecr.exercice = Exercice.pour_date(ecr.date)
                    if not ecr.numero:
                        ecr.numero = Sequence.suivant(ecr.journal.code, ecr.date.year, largeur=6)
                    ecr.save()
                    formset.instance = ecr
                    formset.save()
                    if "valider" in request.POST:
                        ecr.valider()
                        messages.success(request, f"Écriture {ecr.numero} validée.")
                    else:
                        messages.success(request, f"Écriture {ecr.numero} enregistrée au brouillard.")
                return redirect("comptabilite:ecriture_detail", pk=ecr.pk)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
    else:
        form = EcritureForm(instance=ecriture)
        formset = LigneEcritureFormSet(instance=ecriture)
    return render(request, "comptabilite/ecriture_form.html", {"form": form, "formset": formset, "ecriture": ecriture})


@login_required
def ecriture_create(request):
    return _ecriture_form(request, Ecriture())


@login_required
def ecriture_update(request, pk):
    ecriture = get_object_or_404(Ecriture, pk=pk)
    if ecriture.statut == Ecriture.STATUT_VALIDEE:
        messages.warning(request, "Une écriture validée n'est plus modifiable (passez une écriture d'extourne).")
        return redirect("comptabilite:ecriture_detail", pk=pk)
    return _ecriture_form(request, ecriture)


@login_required
@require_POST
def ecriture_valider(request, pk):
    ecriture = get_object_or_404(Ecriture, pk=pk)
    try:
        ecriture.valider()
        messages.success(request, "Écriture validée.")
    except ValidationError as exc:
        for msg in exc.messages:
            messages.error(request, msg)
    return redirect("comptabilite:ecriture_detail", pk=pk)


@login_required
@require_POST
def ecriture_supprimer(request, pk):
    ecriture = get_object_or_404(Ecriture, pk=pk)
    if ecriture.statut == Ecriture.STATUT_VALIDEE:
        messages.error(request, "Une écriture validée ne peut pas être supprimée.")
        return redirect("comptabilite:ecriture_detail", pk=pk)
    ecriture.delete()
    messages.success(request, "Écriture supprimée.")
    return redirect("comptabilite:ecritures")


# ---------------------------------------------------------------- États
def _export_csv(nom, entetes, lignes):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nom}.csv"'
    response.write("﻿")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(entetes)
    writer.writerows(lignes)
    return response


@login_required
def balance_view(request):
    form, p = PeriodeForm.depuis_requete(request)
    lignes, totaux = services.balance(p["date_debut"], p["date_fin"], p.get("compte_debut"), p.get("compte_fin"))
    if request.GET.get("export") == "csv":
        return _export_csv("balance", ["Compte", "Intitulé", "AN débit", "AN crédit", "Mvt débit", "Mvt crédit",
                                       "Solde débiteur", "Solde créditeur"],
                           [[l["compte"].numero, l["compte"].intitule, l["an_d"], l["an_c"], l["mvt_d"], l["mvt_c"],
                             l["solde_d"], l["solde_c"]] for l in lignes])
    return render(request, "comptabilite/balance.html", {"form": form, "lignes": lignes, "totaux": totaux, "p": p})


@login_required
def grand_livre_view(request):
    form, p = PeriodeForm.depuis_requete(request)
    tiers = None
    if request.GET.get("tiers"):
        tiers = get_object_or_404(Tiers, pk=request.GET["tiers"])
    blocs = services.grand_livre(p["date_debut"], p["date_fin"], p.get("compte_debut"), p.get("compte_fin"), tiers=tiers)
    if request.GET.get("export") == "csv":
        rows = []
        for b in blocs:
            for item in b["lignes"]:
                l = item["ligne"]
                rows.append([b["compte"].numero, l.ecriture.date, l.ecriture.journal.code, l.ecriture.numero,
                             l.libelle, l.debit, l.credit, item["solde"], l.lettrage])
        return _export_csv("grand_livre", ["Compte", "Date", "Journal", "Pièce", "Libellé", "Débit", "Crédit",
                                           "Solde", "Lettrage"], rows)
    return render(request, "comptabilite/grand_livre.html", {"form": form, "blocs": blocs, "p": p, "tiers": tiers})


@login_required
def journal_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    journal = Journal.objects.filter(code=request.GET.get("journal")).first()
    lignes = services.lignes_validees(p["date_debut"], p["date_fin"]).select_related("compte", "ecriture__journal", "tiers")
    if journal:
        lignes = lignes.filter(ecriture__journal=journal)
    lignes = lignes.order_by("ecriture__journal__code", "ecriture__date", "ecriture__numero", "id")
    totaux = lignes.aggregate(d=Sum("debit"), c=Sum("credit"))
    return render(request, "comptabilite/journal_view.html", {
        "form": form, "lignes": lignes, "journal": journal, "journaux": Journal.objects.all(), "totaux": totaux,
    })


@login_required
def bilan_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    return render(request, "comptabilite/bilan.html", {"form": form, "bilan": etats.bilan(p["date_fin"]), "p": p})


@login_required
def compte_resultat_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    cr = etats.compte_de_resultat(p["date_debut"], p["date_fin"])
    return render(request, "comptabilite/compte_resultat.html", {"form": form, "cr": cr, "p": p})


@login_required
def tva_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    return render(request, "comptabilite/tva.html", {"form": form, "tva": services.declaration_tva(p["date_debut"], p["date_fin"]), "p": p})


@login_required
def lettrage_view(request):
    comptes = Compte.objects.filter(lettrable=True)
    compte = comptes.filter(pk=request.GET.get("compte") or request.POST.get("compte")).first()
    tiers = Tiers.objects.filter(pk=request.GET.get("tiers")).first() if request.GET.get("tiers") else None
    if request.method == "POST" and compte:
        ids = request.POST.getlist("lignes")
        try:
            code = services.lettrer(LigneEcriture.objects.filter(pk__in=ids, compte=compte))
            messages.success(request, f"{len(ids)} ligne(s) lettrée(s) avec le code {code}.")
        except ValidationError as exc:
            for msg in exc.messages:
                messages.error(request, msg)
        url = reverse("comptabilite:lettrage") + f"?compte={compte.pk}"
        if tiers:
            url += f"&tiers={tiers.pk}"
        return redirect(url)
    lignes = services.lignes_non_lettrees(compte, tiers) if compte else []
    return render(request, "comptabilite/lettrage.html", {
        "comptes": comptes, "compte": compte, "lignes": lignes,
        "tiers_list": Tiers.objects.filter(actif=True), "tiers": tiers,
    })
