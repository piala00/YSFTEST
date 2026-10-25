import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.commercial.models import Tiers
from apps.comptabilite.models import Journal

from .forms import ContratForm
from .models import ContratPartenaire, Decompte, ReglementPartenaire, solde_partenaire


def _erreur(request, exc):
    messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))


def _date(valeur):
    return datetime.date.fromisoformat(valeur)


@login_required
def contrats(request):
    form = ContratForm(request.POST or None)
    if request.method == "POST":
        try:
            action = request.POST.get("action")
            if action == "activer":
                get_object_or_404(ContratPartenaire, pk=request.POST["contrat"]).activer(request.user)
                messages.success(request, "Contrat mis en vigueur.")
            elif action == "avenant":
                ancien = get_object_or_404(ContratPartenaire, pk=request.POST["contrat"])
                changements = {}
                if request.POST.get("taux_commission"):
                    changements["taux_commission"] = Decimal(request.POST["taux_commission"])
                if request.POST.get("montant_location"):
                    changements["montant_location"] = Decimal(request.POST["montant_location"])
                nouveau = ancien.avenant(_date(request.POST["a_partir_du"]), **changements)
                messages.success(request, f"Avenant enregistré : version {nouveau.version} en vigueur.")
            elif form.is_valid():
                contrat = form.save()
                messages.success(request, f"Contrat préparé pour {contrat.vehicule.immatriculation} : mettez-le en vigueur.")
            else:
                return render(request, "partenaires/contrats.html", _contexte(form))
        except (ValidationError, ArithmeticError, ValueError, KeyError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    return render(request, "partenaires/contrats.html", _contexte(form))


def _contexte(form):
    return {"form": form, "contrats": ContratPartenaire.objects.select_related("vehicule", "partenaire")}


@login_required
def decomptes(request):
    if request.method == "POST":
        try:
            action = request.POST.get("action")
            if action == "calculer":
                d = Decompte.calculer(get_object_or_404(ContratPartenaire, pk=request.POST["contrat"]),
                                      _date(request.POST["debut"]), _date(request.POST["fin"]))
                messages.success(request, f"Décompte {d.numero} calculé : {d.montant_du} dû au propriétaire. À approuver.")
            elif action == "approuver":
                d = get_object_or_404(Decompte, pk=request.POST["decompte"])
                d.approuver(request.user)
                messages.success(request, f"Décompte {d.numero} approuvé et comptabilisé.")
            elif action == "supprimer":
                d = get_object_or_404(Decompte, pk=request.POST["decompte"], statut=Decompte.BROUILLON)
                d.delete()
                messages.success(request, "Décompte non approuvé supprimé (il peut être recalculé).")
        except (ValidationError, ArithmeticError, ValueError, KeyError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    aujourd_hui = datetime.date.today()
    premier = aujourd_hui.replace(day=1)
    fin_mois_dernier = premier - datetime.timedelta(days=1)
    return render(request, "partenaires/decomptes.html", {
        "decomptes": Decompte.objects.select_related("contrat__vehicule", "contrat__partenaire")[:200],
        "contrats": ContratPartenaire.objects.exclude(statut=ContratPartenaire.BROUILLON).select_related("vehicule", "partenaire"),
        "debut": fin_mois_dernier.replace(day=1), "fin": fin_mois_dernier})


@login_required
def releve(request, pk=None):
    partenaires = Tiers.objects.filter(contrats_partenaire__isnull=False).distinct().order_by("nom")
    partenaire = get_object_or_404(Tiers, pk=pk) if pk else None
    if partenaire and request.method == "POST":
        try:
            decompte = Decompte.objects.filter(pk=request.POST.get("decompte") or None, contrat__partenaire=partenaire).first()
            r = ReglementPartenaire(partenaire=partenaire, decompte=decompte, montant=Decimal(request.POST.get("montant") or 0),
                                    caisse=get_object_or_404(Journal, pk=request.POST["caisse"]),
                                    date=_date(request.POST.get("date") or datetime.date.today().isoformat()),
                                    reference=request.POST.get("reference", ""))
            r.enregistrer(request.user)
            messages.success(request, f"Règlement {r.numero} enregistré.")
        except (ValidationError, ArithmeticError, ValueError, KeyError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    contexte = {"partenaires": [{"tiers": t, "solde": solde_partenaire(t)} for t in partenaires], "partenaire": partenaire}
    if partenaire:
        mouvements = []
        for d in Decompte.objects.filter(contrat__partenaire=partenaire, statut=Decompte.APPROUVE):
            mouvements.append({"date": d.fin, "piece": d.numero, "libelle": f"Décompte {d.contrat.vehicule.immatriculation} "
                               f"du {d.debut:%d/%m} au {d.fin:%d/%m/%Y}", "du": d.montant_du, "paye": Decimal(0)})
        for r in ReglementPartenaire.objects.filter(partenaire=partenaire):
            mouvements.append({"date": r.date, "piece": r.numero, "libelle": f"Règlement {r.caisse.code} {r.reference}",
                               "du": Decimal(0), "paye": r.montant})
        mouvements.sort(key=lambda m: (m["date"], m["piece"]))
        cumul = Decimal(0)
        for m in mouvements:
            cumul += m["du"] - m["paye"]
            m["reste"] = cumul
        contexte.update({
            "mouvements": mouvements, "reste": cumul, "solde_comptable": solde_partenaire(partenaire),
            "contrats": partenaire.contrats_partenaire.select_related("vehicule"),
            "decomptes": Decompte.objects.filter(contrat__partenaire=partenaire, statut=Decompte.APPROUVE),
            "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False)})
    return render(request, "partenaires/releve.html", contexte)
