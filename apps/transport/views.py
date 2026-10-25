"""Écrans du logiciel Transport de voyageurs."""
import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (BilletForm, ChauffeurForm, ColisForm, DepartForm, DepenseVehiculeForm, GareForm, LigneForm,
                    ParametresTransportForm, VehiculeForm)
from .models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, ParametresTransport, Vehicule

ZERO = Decimal("0")


def _erreur(request, exc):
    messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))


def _jour(request, cle="date"):
    try:
        return datetime.date.fromisoformat(request.GET.get(cle) or "")
    except ValueError:
        return timezone.localdate()


# ---------------------------------------------------------------- Structure : gares, lignes, véhicules, chauffeurs
FICHES = {
    "gares": (Gare, GareForm, "Gares", ["code", "nom", "ville", "caisse"]),
    "lignes": (Ligne, LigneForm, "Lignes et tarifs", ["code", "gare_depart", "gare_arrivee", "distance_km", "duree", "prix_billet",
                                                     "colis_forfait", "colis_prix_kg"]),
    "vehicules": (Vehicule, VehiculeForm, "Véhicules", ["immatriculation", "designation", "type_vehicule", "nombre_places"]),
    "chauffeurs": (Chauffeur, ChauffeurForm, "Chauffeurs", ["nom", "telephone", "permis"]),
}


@login_required
def fiches(request, genre):
    modele, _, titre, colonnes = FICHES[genre]
    objets = modele.objects.all()
    if request.GET.get("q"):
        q = request.GET["q"]
        champs = [c for c in colonnes if c in ("code", "nom", "ville", "immatriculation", "designation")]
        filtre = Q()
        for c in champs:
            filtre |= Q(**{f"{c}__icontains": q})
        objets = objets.filter(filtre)
    lignes = [{"objet": o, "valeurs": [getattr(o, f"get_{c}_display", lambda c=c, o=o: getattr(o, c))() for c in colonnes]}
              for o in objets]
    entetes = [modele._meta.get_field(c).verbose_name for c in colonnes]
    return render(request, "transport/fiches.html", {"titre": titre, "genre": genre, "entetes": entetes, "lignes": lignes})


@login_required
def fiche_form(request, genre, pk=None):
    modele, formulaire, titre, _ = FICHES[genre]
    instance = get_object_or_404(modele, pk=pk) if pk else None
    form = formulaire(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fiche enregistrée.")
        return redirect("transport:fiches", genre)
    return render(request, "core/form.html", {"form": form, "titre": f"{titre} — {'modifier' if instance else 'nouvelle fiche'}"})


@login_required
def parametres(request):
    form = ParametresTransportForm(request.POST or None, instance=ParametresTransport.get())
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paramètres enregistrés.")
        return redirect("transport:parametres")
    return render(request, "core/form.html", {"form": form, "titre": "Paramètres transport (comptes et taxes)"})


# ---------------------------------------------------------------- Départs
@login_required
def departs(request):
    jour = _jour(request)
    qs = Depart.objects.filter(date=jour).select_related("ligne__gare_depart", "ligne__gare_arrivee", "vehicule", "chauffeur")
    if request.GET.get("gare"):
        qs = qs.filter(ligne__gare_depart_id=request.GET["gare"])
    return render(request, "transport/departs.html", {
        "departs": qs.order_by("heure"), "jour": jour, "gares": Gare.objects.filter(actif=True),
        "gare": request.GET.get("gare", ""), "veille": jour - datetime.timedelta(days=1),
        "lendemain": jour + datetime.timedelta(days=1)})


@login_required
def depart_form(request, pk=None):
    instance = get_object_or_404(Depart, pk=pk) if pk else None
    initial = {"date": _jour(request)} if not instance else {}
    form = DepartForm(request.POST or None, instance=instance, initial=initial)
    if request.method == "POST" and form.is_valid():
        depart = form.save(commit=False)
        depart.cree_par = depart.cree_par or request.user
        depart.save()
        messages.success(request, f"Départ {depart.numero} enregistré.")
        return redirect("transport:depart_detail", depart.pk)
    return render(request, "core/form.html", {"form": form, "titre": "Programmer un départ" if not instance else f"Départ {instance.numero}"})


@login_required
def depart_detail(request, pk):
    depart = get_object_or_404(Depart.objects.select_related("ligne__gare_depart", "ligne__gare_arrivee", "vehicule", "chauffeur"), pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "partir":
                depart.partir()
                messages.success(request, "Départ enregistré : voyageurs embarqués, colis en route.")
            elif action == "arriver":
                depart.arriver()
                messages.success(request, "Arrivée enregistrée : les colis sont disponibles en gare d'arrivée.")
            elif action == "annuler":
                depart.annuler()
                messages.success(request, "Départ annulé.")
            elif action == "charger":
                colis = get_object_or_404(Colis, pk=request.POST.get("colis"))
                colis.charger(depart)
                messages.success(request, f"Colis {colis.numero} chargé.")
        except ValidationError as exc:
            _erreur(request, exc)
        return redirect("transport:depart_detail", depart.pk)
    billets = depart.billets.select_related("vendu_par").order_by("siege", "numero")
    occupes = depart.sieges_occupes()
    a_charger = Colis.objects.filter(statut=Colis.ENREGISTRE, gare_depart=depart.ligne.gare_depart,
                                     gare_arrivee=depart.ligne.gare_arrivee) if depart.statut == Depart.PROGRAMME else []
    return render(request, "transport/depart_detail.html", {
        "depart": depart, "billets": billets, "colis": depart.colis.all(), "a_charger": a_charger,
        "sieges": [(n, n in occupes) for n in range(1, depart.places + 1)],
        "recette_billets": depart.recette_billets(), "recette_colis": depart.recette_colis(), "depenses": depart.depenses(),
        "depenses_liste": depart.depenses_vehicule.all()})


@login_required
def manifeste(request, pk):
    depart = get_object_or_404(Depart, pk=pk)
    return render(request, "transport/manifeste.html", {
        "depart": depart, "billets": depart.billets_actifs.order_by("siege", "numero"),
        "colis": depart.colis.exclude(statut=Colis.ANNULE)})


# ---------------------------------------------------------------- Billetterie
@login_required
def billets(request):
    jour = _jour(request)
    qs = Billet.objects.filter(date_vente=jour).select_related("depart__ligne", "gare", "vendu_par")
    if request.GET.get("q"):
        q = request.GET["q"]
        qs = Billet.objects.filter(Q(numero__icontains=q) | Q(voyageur__icontains=q) | Q(telephone__icontains=q)).select_related(
            "depart__ligne", "gare", "vendu_par")
    return render(request, "transport/billets.html", {"billets": qs, "jour": jour, "q": request.GET.get("q", ""),
                                                      "total": sum((b.prix for b in qs if b.statut != Billet.ANNULE), ZERO)})


@login_required
def billet_vente(request):
    initial = {}
    if request.GET.get("depart"):
        depart = Depart.objects.filter(pk=request.GET["depart"]).first()
        if depart:
            initial = {"depart": depart, "prix": depart.ligne.prix_billet, "siege": request.GET.get("siege")}
    form = BilletForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        billet = form.save(commit=False)
        try:
            billet.vendre(request.user)
            messages.success(request, f"Billet {billet.numero} vendu ({billet.prix:,.0f} FCFA).".replace(",", " "))
            if request.POST.get("suivant"):
                return redirect(f"{reverse('transport:billet_vente')}?depart={billet.depart_id}")
            return redirect("transport:billet_detail", billet.pk)
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "transport/billet_form.html", {"form": form, "titre": "Vendre un billet"})


@login_required
def billet_detail(request, pk):
    billet = get_object_or_404(Billet.objects.select_related("depart__ligne", "gare", "client"), pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "annuler":
                retenue = request.POST.get("retenue")
                billet.annuler(retenue=Decimal(retenue) if retenue not in (None, "") else None, utilisateur=request.user)
                messages.success(request, f"Billet annulé : {billet.rembourse:,.0f} FCFA remboursés.".replace(",", " "))
            elif action == "reporter":
                billet.reporter(get_object_or_404(Depart, pk=request.POST.get("depart")),
                                siege=int(request.POST["siege"]) if request.POST.get("siege") else None)
                messages.success(request, f"Billet reporté sur le départ {billet.depart.numero}.")
        except (ValidationError, ArithmeticError, ValueError) as exc:
            _erreur(request, exc)
        return redirect("transport:billet_detail", billet.pk)
    autres = Depart.objects.filter(ligne=billet.depart.ligne, statut=Depart.PROGRAMME).exclude(pk=billet.depart_id).order_by("date", "heure")
    return render(request, "transport/billet_detail.html", {
        "billet": billet, "autres_departs": autres, "retenue_conseillee": ParametresTransport.get().retenue_annulation})


@login_required
def billet_imprimer(request, pk):
    return render(request, "transport/billet_print.html", {"billet": get_object_or_404(Billet, pk=pk)})


# ---------------------------------------------------------------- Colis et courrier
@login_required
def colis_liste(request):
    qs = Colis.objects.select_related("gare_depart", "gare_arrivee", "depart")
    statut, gare = request.GET.get("statut", ""), request.GET.get("gare", "")
    if request.GET.get("q"):
        q = request.GET["q"]
        qs = qs.filter(Q(numero__icontains=q) | Q(expediteur__icontains=q) | Q(destinataire__icontains=q)
                       | Q(tel_destinataire__icontains=q) | Q(tel_expediteur__icontains=q))
    elif statut:
        qs = qs.filter(statut=statut)
    else:
        qs = qs.filter(date=_jour(request))
    if gare:
        qs = qs.filter(Q(gare_depart_id=gare) | Q(gare_arrivee_id=gare))
    return render(request, "transport/colis_liste.html", {
        "colis": qs[:500], "statuts": Colis.STATUTS, "statut": statut, "gares": Gare.objects.filter(actif=True), "gare": gare,
        "jour": _jour(request), "q": request.GET.get("q", "")})


@login_required
def colis_form(request):
    form = ColisForm(request.POST or None, initial={"nature": request.GET.get("nature", Colis.COLIS)})
    if request.method == "POST" and form.is_valid():
        colis = form.save(commit=False)
        try:
            colis.enregistrer(request.user)
            messages.success(request, f"{colis.get_nature_display()} {colis.numero} enregistré — code de retrait {colis.code_retrait}.")
            return redirect("transport:colis_detail", colis.pk)
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Enregistrer un colis, un courrier ou du fret"})


@login_required
def colis_detail(request, pk):
    colis = get_object_or_404(Colis.objects.select_related("gare_depart", "gare_arrivee", "depart", "client"), pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "livrer":
                colis.livrer(request.POST.get("code"), request.POST.get("retire_par"), utilisateur=request.user)
                messages.success(request, "Envoi remis au destinataire" + (
                    f" : {colis.a_encaisser:,.0f} FCFA encaissés.".replace(",", " ") if colis.a_encaisser else "."))
            elif action == "reverser":
                colis.reverser_contre_remboursement(request.user)
                messages.success(request, "Contre-remboursement reversé à l'expéditeur.")
            elif action == "annuler":
                colis.annuler(request.user)
                messages.success(request, "Envoi annulé.")
            elif action == "charger":
                colis.charger(get_object_or_404(Depart, pk=request.POST.get("depart")))
                messages.success(request, "Envoi chargé.")
        except ValidationError as exc:
            _erreur(request, exc)
        return redirect("transport:colis_detail", colis.pk)
    departs = Depart.objects.filter(statut=Depart.PROGRAMME, ligne__gare_depart=colis.gare_depart,
                                    ligne__gare_arrivee=colis.gare_arrivee).order_by("date", "heure")
    return render(request, "transport/colis_detail.html", {"colis": colis, "departs": departs})


@login_required
def colis_imprimer(request, pk):
    return render(request, "transport/colis_print.html", {"colis": get_object_or_404(Colis, pk=pk)})


# ---------------------------------------------------------------- Flotte
@login_required
def depenses(request):
    qs = DepenseVehicule.objects.select_related("vehicule", "depart", "compte", "ecriture")
    debut, fin = _jour(request, "du").replace(day=1) if not request.GET.get("du") else _jour(request, "du"), _jour(request, "au")
    qs = qs.filter(date__range=(debut, fin))
    if request.GET.get("vehicule"):
        qs = qs.filter(vehicule_id=request.GET["vehicule"])
    return render(request, "transport/depenses.html", {
        "depenses": qs, "du": debut, "au": fin, "vehicules": Vehicule.objects.all(), "vehicule": request.GET.get("vehicule", ""),
        "total": sum((d.montant for d in qs), ZERO)})


@login_required
def depense_form(request):
    from apps.comptabilite.models import Journal

    initial = {"caisse": Journal.objects.filter(code="CA").first(), "depart": request.GET.get("depart"),
               "vehicule": request.GET.get("vehicule")}
    form = DepenseVehiculeForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        depense = form.save(commit=False)
        try:
            depense.enregistrer(request.user)
            messages.success(request, f"Dépense {depense.numero} enregistrée et comptabilisée.")
            return redirect("transport:depenses")
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Saisir une dépense de véhicule"})


# ---------------------------------------------------------------- États
@login_required
def recette_journaliere(request):
    """Caisse du jour par gare : billets, annulations, colis au départ, encaissements à la livraison, dépenses."""
    from . import etats

    jour = _jour(request)
    return render(request, "transport/recette.html", {"jour": jour, "gares": etats.recette_journaliere(jour)})


@login_required
def rentabilite(request):
    from . import etats

    fin = _jour(request, "au")
    debut = _jour(request, "du") if request.GET.get("du") else fin.replace(day=1)
    axe = request.GET.get("axe", "ligne")
    return render(request, "transport/rentabilite.html", {
        "du": debut, "au": fin, "axe": axe, "lignes": etats.rentabilite(debut, fin, axe),
        "axes": [("ligne", "Par ligne"), ("vehicule", "Par véhicule"), ("depart", "Par départ")]})
