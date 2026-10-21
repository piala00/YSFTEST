import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count as models_Count, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.commercial.models import Tiers
from apps.core.models import Exercice, Sequence

from . import etats, services
from .forms import (BanqueForm, CompteForm, EcritureForm, JournalForm, LigneEcritureFormSet, PeriodeForm,
                    SectionAnalytiqueForm, TaxeForm)
from .models import CLASSES_SYSCOHADA, Banque, Compte, Ecriture, Journal, LigneEcriture, SectionAnalytique, Taxe


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


# ------------------------------------------------- Structure : taxes, banques, analytique
STRUCTURES = {
    "taxes": (Taxe, TaxeForm, "Taux de taxes", [("code", "Code"), ("intitule", "Intitulé"), ("get_sens_display", "Sens"),
                                                 ("taux", "Taux (%)"), ("compte", "Compte")]),
    "banques": (Banque, BanqueForm, "Banques", [("code", "Code"), ("intitule", "Intitulé"), ("domiciliation", "Domiciliation"),
                                                ("rib", "RIB"), ("journal", "Journal"), ("compte", "Compte")]),
    "sections": (SectionAnalytique, SectionAnalytiqueForm, "Plan analytique",
                 [("plan", "Plan"), ("code", "Code"), ("intitule", "Intitulé"), ("actif", "Actif")]),
}


def _attribut(objet, nom):
    v = getattr(objet, nom)
    v = v() if callable(v) else v
    if v is True:
        return "Oui"
    if v is False:
        return "Non"
    return "" if v is None else v


@login_required
def structure_liste(request, structure):
    if structure not in STRUCTURES:
        raise Http404
    modele, _, titre, colonnes = STRUCTURES[structure]
    lignes = [(o.pk, [_attribut(o, c) for c, _ in colonnes]) for o in modele.objects.all()]
    return render(request, "comptabilite/structure_list.html", {
        "titre": titre, "structure": structure, "entetes": [l for _, l in colonnes], "lignes": lignes})


@login_required
def structure_fiche(request, structure, pk=None):
    if structure not in STRUCTURES:
        raise Http404
    modele, formulaire, titre, _ = STRUCTURES[structure]
    objet = get_object_or_404(modele, pk=pk) if pk else None
    form = formulaire(request.POST or None, instance=objet)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{titre} : fiche enregistrée.")
        return redirect("comptabilite:structure", structure=structure)
    return render(request, "core/form.html", {"form": form, "titre": f"{titre} — {'modifier' if objet else 'nouvelle fiche'}"})


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
    brouillard = request.GET.get("statut") == Ecriture.STATUT_BROUILLARD
    if brouillard:
        lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_BROUILLARD, ecriture__date__gte=p["date_debut"],
                                              ecriture__date__lte=p["date_fin"]).select_related("compte", "ecriture__journal", "tiers")
    else:
        lignes = services.lignes_validees(p["date_debut"], p["date_fin"]).select_related("compte", "ecriture__journal", "tiers")
    if journal:
        lignes = lignes.filter(ecriture__journal=journal)
    lignes = lignes.order_by("ecriture__journal__code", "ecriture__date", "ecriture__numero", "id")
    totaux = lignes.aggregate(d=Sum("debit"), c=Sum("credit"))
    return render(request, "comptabilite/journal_view.html", {
        "form": form, "lignes": lignes, "journal": journal, "journaux": Journal.objects.all(), "totaux": totaux,
        "brouillard": brouillard,
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
    tout = request.GET.get("tout") == "1"
    if compte and tout:
        lignes = services.lignes_validees().filter(compte=compte).select_related("ecriture", "tiers").order_by("ecriture__date", "id")
        if tiers:
            lignes = lignes.filter(tiers=tiers)
    else:
        lignes = services.lignes_non_lettrees(compte, tiers) if compte else []
    return render(request, "comptabilite/lettrage.html", {
        "comptes": comptes, "compte": compte, "lignes": lignes, "tout": tout,
        "tiers_list": Tiers.objects.filter(actif=True), "tiers": tiers,
    })


@login_required
@require_POST
def delettrage(request):
    compte = get_object_or_404(Compte, pk=request.POST.get("compte"), lettrable=True)
    code = request.POST.get("code", "").strip().upper()
    n = services.delettrer(compte, code) if code else 0
    if n:
        messages.success(request, f"Code {code} supprimé : {n} ligne(s) délettrée(s).")
    else:
        messages.warning(request, f"Aucune ligne lettrée « {code} » sur le compte {compte.numero}.")
    return redirect(reverse("comptabilite:lettrage") + f"?compte={compte.pk}&tout=1")


@login_required
def lettrage_auto_view(request):
    comptes = Compte.objects.filter(lettrable=True)
    if request.method == "POST":
        selection = comptes.filter(pk__in=request.POST.getlist("comptes")) if request.POST.getlist("comptes") else None
        tiers = Tiers.objects.filter(pk=request.POST.get("tiers")).first() if request.POST.get("tiers") else None
        n = services.lettrage_automatique(selection, tiers)
        messages.success(request, f"Lettrage automatique terminé : {n} code(s) de lettrage attribué(s).")
        return redirect("comptabilite:lettrage_auto")
    restant = (services.lignes_validees().filter(compte__lettrable=True, lettrage="").values("compte__numero", "compte__intitule")
               .annotate(n=models_Count("id"), d=Sum("debit"), c=Sum("credit")).order_by("compte__numero"))
    restant = [{**r, "solde": (r["d"] or 0) - (r["c"] or 0)} for r in restant]
    return render(request, "comptabilite/lettrage_auto.html", {
        "comptes": comptes, "restant": restant, "tiers_list": Tiers.objects.filter(actif=True)})


# ---------------------------------------------------------------- Rapprochement bancaire
@login_required
def rapprochement_view(request):
    import datetime
    from decimal import Decimal, InvalidOperation

    banques = Banque.objects.select_related("journal__compte_tresorerie")
    banque = banques.filter(pk=request.GET.get("banque") or request.POST.get("banque")).first() or banques.first()
    date_releve = parse_date(request.GET.get("date") or request.POST.get("date") or "") or datetime.date.today()
    try:
        solde_releve = Decimal((request.GET.get("solde") or request.POST.get("solde") or "").replace(" ", "").replace(",", "."))
    except InvalidOperation:
        solde_releve = None
    if request.method == "POST" and banque:
        ids = request.POST.getlist("lignes")
        n = services.pointer(LigneEcriture.objects.filter(pk__in=ids, compte=banque.compte), date_releve)
        messages.success(request, f"{n} opération(s) pointée(s) sur le relevé du {date_releve:%d/%m/%Y}.")
        url = reverse("comptabilite:rapprochement") + f"?banque={banque.pk}&date={date_releve.isoformat()}"
        if solde_releve is not None:
            url += f"&solde={solde_releve}"
        return redirect(url)
    situation = services.rapprochement(banque.compte, date_releve) if banque and banque.compte else None
    ecart = (situation["solde_banque_theorique"] - solde_releve) if situation and solde_releve is not None else None
    return render(request, "comptabilite/rapprochement.html", {
        "banques": banques, "banque": banque, "date_releve": date_releve, "solde_releve": solde_releve,
        "situation": situation, "ecart": ecart})


# ---------------------------------------------------------------- Fin d'exercice et clôtures
@login_required
def cloture_exercice_view(request):
    if request.method == "POST":
        exercice = get_object_or_404(Exercice, pk=request.POST.get("exercice"))
        try:
            r = services.cloturer_exercice(exercice)
            messages.success(request, f"Exercice {exercice.code} clôturé. Résultat : {r['resultat']:,.0f}".replace(",", " ")
                             + f". À-nouveaux générés dans l'exercice {r['exercice_suivant'].code}"
                             + (f" (pièce {r['ecriture'].numero})." if r["ecriture"] else "."))
        except ValidationError as exc:
            for msg in exc.messages:
                messages.error(request, msg)
        return redirect("comptabilite:cloture_exercice")
    exercices = [(e, services.controles_cloture(e)) for e in Exercice.objects.order_by("date_debut")]
    return render(request, "comptabilite/cloture_exercice.html", {"exercices": exercices})


@login_required
def cloture_journaux_view(request):
    journaux = Journal.objects.all()
    if request.method == "POST":
        for journal in journaux:
            valeur = request.POST.get(f"cloture_{journal.pk}", "")
            date = parse_date(valeur) if valeur else None
            if date != journal.cloture_au:
                journal.cloture_au = date
                journal.save(update_fields=["cloture_au"])
        messages.success(request, "Dates de clôture des journaux enregistrées.")
        return redirect("comptabilite:cloture_journaux")
    return render(request, "comptabilite/cloture_journaux.html", {"journaux": journaux})


# ---------------------------------------------------------------- Analytique
@login_required
def ventilation_view(request):
    """Traitement > Saisie des écritures analytiques : affecter une section aux lignes de charges et produits."""
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    sections = SectionAnalytique.objects.filter(actif=True)
    if request.method == "POST":
        n = 0
        for cle, valeur in request.POST.items():
            if cle.startswith("section_"):
                ligne = LigneEcriture.objects.filter(pk=cle[8:]).first()
                section = sections.filter(pk=valeur).first() if valeur else None
                if ligne and ligne.section != section:
                    ligne.section = section
                    ligne.save(update_fields=["section"])
                    n += 1
        messages.success(request, f"{n} ligne(s) ventilée(s).")
        return redirect(request.get_full_path())
    lignes = (services.lignes_validees(p["date_debut"], p["date_fin"])
              .filter(Q(compte__numero__startswith="6") | Q(compte__numero__startswith="7"))
              .select_related("compte", "ecriture__journal", "section").order_by("ecriture__date", "id"))
    if request.GET.get("tout") != "1":
        lignes = lignes.filter(section__isnull=True)
    return render(request, "comptabilite/ventilation.html", {"form": form, "lignes": lignes[:300], "sections": sections})


@login_required
def balance_analytique_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    lignes = services.balance_analytique(p["date_debut"], p["date_fin"])
    totaux = {k: sum(l[k] for l in lignes) for k in ("charges", "produits", "resultat")}
    return render(request, "comptabilite/balance_analytique.html", {"form": form, "lignes": lignes, "totaux": totaux, "p": p})


# ---------------------------------------------------------------- Etats tiers
@login_required
def justificatif_solde_view(request):
    import datetime

    type_tiers = request.GET.get("type", Tiers.CLIENT)
    date = parse_date(request.GET.get("date") or "") or datetime.date.today()
    blocs = services.justificatif_solde(date, type_tiers)
    return render(request, "comptabilite/justificatif_solde.html", {
        "blocs": blocs, "date": date, "type_tiers": type_tiers, "total": sum((b["solde"] for b in blocs), 0)})


@login_required
def statistiques_tiers_view(request):
    form, p = PeriodeForm.depuis_requete(request, avec_comptes=False)
    type_tiers = request.GET.get("type", Tiers.CLIENT)
    lignes = services.statistiques_tiers(p["date_debut"], p["date_fin"], type_tiers)
    totaux = {k: sum((l[k] for l in lignes), 0) for k in ("report", "facture", "regle", "solde")}
    if request.GET.get("export") == "csv":
        return _export_csv("statistiques_tiers", ["Code", "Tiers", "Report", "Facturé", "Réglé", "Solde", "Nb factures",
                                                  "Nb règlements", "Dernière facture", "Dernier règlement"],
                           [[l["tiers"].code, l["tiers"].nom, l["report"], l["facture"], l["regle"], l["solde"],
                             l["nb_factures"], l["nb_reglements"], l["derniere_facture"], l["dernier_reglement"]]
                            for l in lignes])
    return render(request, "comptabilite/statistiques_tiers.html", {
        "form": form, "p": p, "lignes": lignes, "totaux": totaux, "type_tiers": type_tiers, "export": True})
