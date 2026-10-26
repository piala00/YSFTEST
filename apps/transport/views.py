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
    lignes = [{"objet": o, "valeurs": [getattr(o, f"get_{c}_display", lambda c=c, o=o: getattr(o, c))() for c in colonnes],
               "url": reverse("transport:vehicule_fiche" if genre == "vehicules" else "transport:fiche_update",
                              args=[o.pk] if genre == "vehicules" else [genre, o.pk])}
              for o in objets]
    entetes = [modele._meta.get_field(c).verbose_name for c in colonnes]
    nouvelle = reverse("transport:vehicule_create") if genre == "vehicules" else reverse("transport:fiche_create", args=[genre])
    return render(request, "transport/fiches.html", {"titre": titre, "genre": genre, "entetes": entetes, "lignes": lignes,
                                                     "nouvelle": nouvelle})


@login_required
def fiche_form(request, genre, pk=None):
    modele, formulaire, titre, _ = FICHES[genre]
    instance = get_object_or_404(modele, pk=pk) if pk else None
    form = formulaire(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        objet = form.save()
        messages.success(request, "Fiche enregistrée.")
        if genre == "vehicules":
            return redirect("transport:vehicule_fiche", objet.pk)
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
    from apps.comptabilite.models import Journal

    from .models_exploitation import JustificatifMission

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
            elif action == "cloturer":
                depart.cloturer(request.POST.get("km_arrivee") or None, request.POST.get("observations", ""), request.user)
                messages.success(request, "Voyage clôturé.")
            elif action == "avance":
                from apps.comptabilite.models import Journal

                from .models_exploitation import AvanceMission

                AvanceMission(depart=depart, beneficiaire=request.POST.get("beneficiaire", "").strip() or str(depart.chauffeur or ""),
                              montant=Decimal(request.POST.get("montant") or 0),
                              caisse=get_object_or_404(Journal, pk=request.POST.get("caisse"))).remettre(request.user)
                messages.success(request, "Avance de mission remise : à justifier au retour.")
            elif action == "justificatif":
                from .models_exploitation import AvanceMission, JustificatifMission

                avance = get_object_or_404(AvanceMission, pk=request.POST.get("avance"), depart=depart, statut=AvanceMission.REMISE)
                JustificatifMission.objects.create(avance=avance, nature=request.POST.get("nature", JustificatifMission.PEAGE),
                                                   libelle=request.POST.get("libelle", ""), montant=Decimal(request.POST.get("montant") or 0))
            elif action == "justifier":
                from .models_exploitation import AvanceMission

                get_object_or_404(AvanceMission, pk=request.POST.get("avance"), depart=depart).justifier(
                    Decimal(request.POST.get("restitue") or 0), utilisateur=request.user)
                messages.success(request, "Avance justifiée.")
            elif action == "embarquement":
                depart.pointer_embarquement(request.POST.getlist("embarques"), request.user)
                messages.success(request, "Liste d'embarquement enregistrée.")
            elif action == "affecter":
                from .models import Troncon

                troncon = get_object_or_404(Troncon, pk=request.POST.get("troncon"))
                troncon.affecter(depart, int(request.POST["siege"]) if request.POST.get("siege") else None)
                messages.success(request, f"{troncon.billet.voyageur} placé sur ce départ (correspondance).")
        except (ValidationError, ArithmeticError, ValueError) as exc:
            _erreur(request, exc)
        return redirect("transport:depart_detail", depart.pk)
    billets = depart.troncons.select_related("billet__gare_arrivee", "billet__vendu_par", "gare_depart", "gare_arrivee").order_by(
        "siege", "billet__numero")
    occupes = depart.sieges_occupes()
    a_charger = Colis.objects.filter(statut=Colis.ENREGISTRE, gare_depart=depart.ligne.gare_depart,
                                     gare_arrivee=depart.ligne.gare_arrivee) if depart.statut == Depart.PROGRAMME else []
    return render(request, "transport/depart_detail.html", {
        "depart": depart, "billets": billets, "colis": depart.colis.all(), "a_charger": a_charger,
        "absents": depart.absents.select_related("billet", "gare_depart", "gare_arrivee", "depart"),
        "correspondances": depart.correspondances_a_affecter() if depart.statut == Depart.PROGRAMME else [],
        "sieges": [(n, n in occupes) for n in range(1, depart.places + 1)],
        "recette_billets": depart.recette_billets(), "recette_colis": depart.recette_colis(), "depenses": depart.depenses(),
        "depenses_liste": depart.depenses_vehicule.all(),
        "avances": depart.avances_mission.prefetch_related("justificatifs"), "natures_justificatif": JustificatifMission.NATURES,
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)})


@login_required
def voyages_a_cloturer(request):
    """Départs arrivés à clôturer, et avances de mission encore à justifier."""
    from .models_exploitation import AvanceMission

    return render(request, "transport/voyages_a_cloturer.html", {
        "departs": Depart.objects.filter(statut__in=[Depart.PARTI, Depart.ARRIVE], site_origine="")
                                 .select_related("ligne", "vehicule", "chauffeur").order_by("date", "heure"),
        "avances": AvanceMission.objects.filter(statut=AvanceMission.REMISE).select_related("depart__vehicule")})


@login_required
def manifeste(request, pk):
    depart = get_object_or_404(Depart, pk=pk)
    return render(request, "transport/manifeste.html", {
        "depart": depart, "billets": depart.voyageurs.select_related("billet__gare_arrivee", "gare_depart", "gare_arrivee").order_by("siege", "billet__numero"),
        "colis": depart.colis.exclude(statut=Colis.ANNULE)})


# ---------------------------------------------------------------- Billetterie
@login_required
def billets(request):
    jour = _jour(request)
    qs = Billet.objects.filter(date_vente=jour).select_related("depart__ligne", "gare", "vendu_par")
    if request.GET.get("remboursement"):
        qs = Billet.objects.filter(remboursement=request.GET["remboursement"]).select_related("depart__ligne", "gare", "vendu_par")
    if request.GET.get("q"):
        q = request.GET["q"]
        qs = Billet.objects.filter(Q(numero__icontains=q) | Q(voyageur__icontains=q) | Q(telephone__icontains=q)).select_related(
            "depart__ligne", "gare", "vendu_par")
    return render(request, "transport/billets.html", {"billets": qs, "jour": jour, "q": request.GET.get("q", ""),
                                                      "total": sum((b.total for b in qs if b.statut != Billet.ANNULE), ZERO)})


@login_required
def billet_vente(request):
    initial = {}
    if request.GET.get("depart"):
        depart = Depart.objects.filter(pk=request.GET["depart"]).first()
        if depart:
            initial = {"depart": depart, "siege": request.GET.get("siege")}         # prix : tarif du trajet choisi
    form = BilletForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        billet = form.save(commit=False)
        try:
            billet.vendre(request.user, depart_correspondance=form.cleaned_data.get("depart_correspondance"),
                          siege_correspondance=form.cleaned_data.get("siege_correspondance"))
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
                maintenant = request.POST.get("rembourser") != "plus_tard"
                billet.annuler(retenue=Decimal(retenue) if retenue not in (None, "") else None, utilisateur=request.user,
                               rembourser=maintenant)
                if billet.remboursement == Billet.AUTORISE:
                    messages.success(request, f"Billet annulé : remboursement de {billet.rembourse:,.0f} FCFA autorisé, "
                                              f"à payer en caisse.".replace(",", " "))
                else:
                    messages.success(request, f"Billet annulé : {billet.rembourse:,.0f} FCFA remboursés.".replace(",", " "))
            elif action == "rembourser":
                billet.rembourser(utilisateur=request.user)
                messages.success(request, f"Remboursement de {billet.rembourse:,.0f} FCFA payé.".replace(",", " "))
            elif action == "reporter":
                billet.reporter(get_object_or_404(Depart, pk=request.POST.get("depart")),
                                siege=int(request.POST["siege"]) if request.POST.get("siege") else None)
                messages.success(request, f"Billet reporté sur le départ {billet.depart.numero}.")
        except (ValidationError, ArithmeticError, ValueError) as exc:
            _erreur(request, exc)
        return redirect("transport:billet_detail", billet.pk)
    from .models import Troncon

    a_faire = billet.troncons.filter(statut=Troncon.A_VOYAGER).first()
    autres = ([d for d in Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").exclude(pk=a_faire.depart_id)
               .select_related("ligne").order_by("date", "heure")[:200] if d.ligne.dessert(a_faire.gare_depart, a_faire.gare_arrivee)]
              if a_faire else [])
    return render(request, "transport/billet_detail.html", {
        "billet": billet, "troncons": billet.troncons.select_related("gare_depart", "gare_arrivee", "depart", "vehicule",
                                                                     "depart_manque"),
        "historique": billet.historique.select_related("utilisateur"),
        "autres_departs": autres, "retenue_conseillee": ParametresTransport.get().retenue_annulation})


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
def recette_journaliere(request, service=""):
    """Caisse du jour par gare : billets, annulations, colis au départ, encaissements à la livraison."""
    from . import etats

    jour = _jour(request)
    return render(request, "transport/recette.html", {"jour": jour, "gares": etats.recette_journaliere(jour), "service": service})


@login_required
def rapport_journalier(request):
    from . import etats

    from .models_caisse import ClotureJournee, SessionCaisse, anomalies_du_jour

    jour = _jour(request)
    bloquants, signales = anomalies_du_jour(jour)
    return render(request, "transport/rapport_journalier.html", {
        "jour": jour, **etats.rapport_journalier(jour), "bloquants": bloquants, "signales": signales,
        "cloture": ClotureJournee.objects.filter(date=jour, perimetre=ClotureJournee.AGENCE).first(),
        "sessions": SessionCaisse.objects.filter(ouverte_le__date=jour).select_related("agent")})


@login_required
def rapport_journalier_imprimer(request):
    """Rapport journalier de l'agence en tableaux simples, mis en page pour une feuille A4 portrait."""
    from django.utils import timezone

    from apps.core.models import Agence
    from apps.echanges.models import Evenement, LotEmis
    from apps.echanges.publication import site_local

    from . import etats
    from .models_caisse import ClotureJournee

    jour = _jour(request)
    local = site_local()
    siege = local is None or local.role == local.SIEGE
    agences = Agence.objects.filter(locale=False).order_by("rang", "code") if siege else Agence.objects.none()
    agence = agences.filter(code=request.GET.get("agence", "")).first()   # au siège seulement : données reçues
    site = agence.code if agence else ""
    code = site or (local.code if local else "AG")
    contexte = {"jour": jour, "agences": agences, "agence": agence, "local": local, "genere_le": timezone.now(),
                "numero": f"RJ-{code}-{jour:%Y%m%d}", **etats.rapport_agence_a4(jour, site)}
    if agence:
        contexte["etat"] = "Données reçues de l'agence par les échanges"
        contexte["synchro"] = (f"dernière réception le {timezone.localtime(agence.derniere_reception):%d/%m/%Y %H:%M}"
                               if agence.derniere_reception else "aucun fichier reçu de cette agence")
    else:
        cloture = ClotureJournee.objects.filter(date=jour, perimetre=ClotureJournee.AGENCE).select_related("cloture_par").first()
        contexte["etat"] = (f"CLÔTURÉ le {timezone.localtime(cloture.cloture_le):%d/%m/%Y %H:%M} par {cloture.cloture_par or '—'}"
                            if cloture else "PROVISOIRE — journée non clôturée")
        if local is not None:
            dernier = max(LotEmis.objects.values_list("sequence_a", flat=True), default=0)
            n = Evenement.objects.filter(sequence__gt=dernier).count()
            contexte["synchro"] = f"{n} fait(s) pas encore envoyé(s) au siège" if n else "tout est envoyé au siège"
    return render(request, "transport/rapport_journalier_a4.html", contexte)


@login_required
def rentabilite(request):
    from . import etats

    fin = _jour(request, "au")
    debut = _jour(request, "du") if request.GET.get("du") else fin.replace(day=1)
    axe = request.GET.get("axe", "ligne")
    return render(request, "transport/rentabilite.html", {
        "du": debut, "au": fin, "axe": axe, "lignes": etats.rentabilite(debut, fin, axe),
        "axes": [("ligne", "Par ligne"), ("depart", "Par départ")]})


# ---------------------------------------------------------------- Véhicules : fiche, grand livre, balance
def _periode(request):
    from apps.core.models import Exercice

    exercice = Exercice.courant()
    fin = _jour(request, "au") if request.GET.get("au") else (exercice.date_fin if exercice else timezone.localdate())
    debut = _jour(request, "du") if request.GET.get("du") else (exercice.date_debut if exercice else fin.replace(month=1, day=1))
    return debut, fin


@login_required
def vehicule_fiche(request, pk):
    from . import etats

    vehicule = get_object_or_404(Vehicule.objects.select_related("proprietaire"), pk=pk)
    debut, fin = _periode(request)
    solde = next((l for l in etats.balance_vehicules(debut, fin) if l["vehicule"].pk == vehicule.pk), None)
    departs = vehicule.departs.filter(date__range=(debut, fin)).exclude(statut=Depart.ANNULE)
    places = sum((d.places for d in departs), 0)
    voyageurs = sum((d.places_vendues for d in departs), 0)
    return render(request, "transport/vehicule_fiche.html", {
        "vehicule": vehicule, "du": debut, "au": fin, "solde": solde, "alertes": vehicule.alertes(),
        "activite": etats.activite_vehicule(vehicule, debut, fin), "chauffeurs": vehicule.employes.filter(actif=True),
        "nb_departs": departs.count(), "voyageurs": voyageurs,
        "remplissage": round(100 * voyageurs / places) if places else None,
        "derniers_departs": departs.select_related("ligne", "chauffeur")[:10],
        "dernieres_depenses": vehicule.depenses.filter(date__range=(debut, fin))[:10]})


@login_required
def balance_vehicules(request):
    from . import etats

    debut, fin = _periode(request)
    lignes = etats.balance_vehicules(debut, fin)
    totaux = {cle: sum((l[cle] for l in lignes), ZERO) for cle in ("voyageurs", "colis", "autres_recettes", "recettes",
                                                                  "carburant", "entretien", "autres_depenses", "depenses",
                                                                  "resultat")}
    return render(request, "transport/balance_vehicules.html", {"du": debut, "au": fin, "lignes": lignes, "totaux": totaux})


@login_required
def grand_livre_vehicules(request):
    from . import etats

    debut, fin = _periode(request)
    choisis = Vehicule.objects.filter(pk=request.GET["vehicule"]) if request.GET.get("vehicule") else Vehicule.objects.all()
    livres = [{"vehicule": v, "lignes": etats.grand_livre_vehicule(v, debut, fin)} for v in choisis]
    return render(request, "transport/grand_livre_vehicules.html", {
        "du": debut, "au": fin, "livres": [l for l in livres if l["lignes"] or request.GET.get("vehicule")],
        "vehicules": Vehicule.objects.all(), "vehicule": request.GET.get("vehicule", "")})


# ---------------------------------------------------------------- Caisses des guichets et clôtures
@login_required
def ma_caisse(request, service):
    """Ouverture, suivi et fermeture de la caisse de l'agent connecté."""
    from apps.comptabilite.models import Journal

    from .models_caisse import SessionCaisse

    session = SessionCaisse.ouverte_de(request.user)
    if request.method == "POST":
        try:
            if request.POST.get("action") == "ouvrir":
                SessionCaisse.ouvrir(request.user, get_object_or_404(Journal, pk=request.POST.get("caisse")), service=service,
                                     gare=Gare.objects.filter(pk=request.POST.get("gare")).first(),
                                     fonds_initial=Decimal(request.POST.get("fonds_initial") or 0))
                messages.success(request, "Caisse ouverte.")
            elif request.POST.get("action") == "fermer" and session:
                session.fermer(Decimal(request.POST.get("montant_compte") or "-1"), request.POST.get("justification", ""),
                               request.POST.get("remis_a", ""))
                messages.success(request, f"Caisse fermée : attendu {session.attendu:,.0f}, compté {session.montant_compte:,.0f}, "
                                          f"écart {session.ecart:,.0f}. Le chef de gare doit l'approuver.".replace(",", " "))
        except (ValidationError, ArithmeticError, ValueError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    return render(request, "transport/ma_caisse.html", {
        "session": session, "detail": session.detail() if session else None, "service": service,
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE), "gares": Gare.objects.filter(actif=True),
        "dernieres": SessionCaisse.objects.filter(agent=request.user).exclude(statut=SessionCaisse.OUVERTE)[:5]})


@login_required
def sessions_caisse(request):
    from .models_caisse import SessionCaisse

    jour = _jour(request)
    if request.method == "POST":
        s = get_object_or_404(SessionCaisse, pk=request.POST.get("session"))
        try:
            s.approuver(request.user, request.POST.get("justification", ""), request.POST.get("imputation") or SessionCaisse.CHARGE)
            messages.success(request, f"Caisse {s.numero} approuvée.")
        except ValidationError as exc:
            _erreur(request, exc)
        return redirect(f"{request.path}?date={jour.isoformat()}")
    sessions = SessionCaisse.objects.filter(ouverte_le__date=jour).select_related("agent", "caisse", "gare")
    return render(request, "transport/sessions_caisse.html", {
        "jour": jour, "sessions": [(s, s.detail()) for s in sessions], "imputations": SessionCaisse.IMPUTATIONS})


@login_required
def transferts(request):
    from apps.comptabilite.models import Journal

    from .models_caisse import TransfertFonds

    if request.method == "POST":
        try:
            if request.POST.get("action") == "envoyer":
                TransfertFonds(origine=get_object_or_404(Journal, pk=request.POST["origine"]),
                               destination=get_object_or_404(Journal, pk=request.POST["destination"]),
                               montant=Decimal(request.POST.get("montant") or 0), porteur=request.POST.get("porteur", "")
                               ).envoyer(request.user)
                messages.success(request, "Fonds envoyés : en transit jusqu'à leur réception.")
            elif request.POST.get("action") == "recevoir":
                get_object_or_404(TransfertFonds, pk=request.POST["transfert"]).recevoir(request.user)
                messages.success(request, "Réception enregistrée.")
        except (ValidationError, ArithmeticError, ValueError, KeyError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    return render(request, "transport/transferts.html", {
        "transferts": TransfertFonds.objects.select_related("origine", "destination")[:100],
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)})


@login_required
def cloture_journee(request, perimetre=""):
    from .models_caisse import ClotureJournee, anomalies_du_jour, cloturer_journee

    jour = _jour(request)
    perimetres = [p for p in ClotureJournee.PERIMETRES if not perimetre or p[0] == perimetre]
    if request.method == "POST":
        try:
            cloturer_journee(jour, request.POST["perimetre"], request.user, request.POST.get("commentaire", ""))
            messages.success(request, "Journée clôturée.")
        except (ValidationError, KeyError) as exc:
            _erreur(request, exc)
        return redirect(f"{request.path}?date={jour.isoformat()}")
    etats = []
    for code, libelle in perimetres:
        bloquants, signales = anomalies_du_jour(jour, code)
        etats.append({"code": code, "libelle": libelle, "bloquants": bloquants, "signales": signales,
                      "cloture": ClotureJournee.objects.filter(date=jour, perimetre=code).select_related("cloture_par").first()})
    return render(request, "transport/cloture.html", {"jour": jour, "etats": etats})


# ---------------------------------------------------------------- Comptabilité analytique : Véhicules, Propriétaires
def _filtres_analytiques(request):
    from apps.core.models import Agence
    from apps.echanges.publication import site_local

    from .models import GAMMES

    debut, fin = _periode(request)
    gamme = request.GET.get("gamme", "") if request.GET.get("gamme", "") in dict(GAMMES) else ""
    local = site_local()
    agences = Agence.objects.filter(locale=False).order_by("rang", "code") if local is not None and local.role == local.SIEGE else []
    agence = request.GET.get("agence", "")
    site = None if not agences or agence == "" else ("" if agence == "SIEGE" else agence)
    return {"du": debut, "au": fin, "gamme": gamme, "gammes": GAMMES, "agences": agences, "agence": agence}, site


@login_required
def analytique_vehicules(request):
    from . import analytique

    filtres, site = _filtres_analytiques(request)
    return render(request, "transport/analytique_vehicules.html", {
        **filtres, **analytique.vehicules(filtres["du"], filtres["au"], filtres["gamme"], site),
        "produits": analytique.PRODUITS, "charges": analytique.CHARGES})


@login_required
def analytique_vehicule(request, pk):
    from . import analytique

    vehicule = get_object_or_404(Vehicule, pk=pk)
    filtres, _ = _filtres_analytiques(request)
    compte = analytique.compte_vehicule(vehicule, filtres["du"], filtres["au"])
    rubriques = [(cle, libelle, compte["totaux"][cle], compte["details"].get(cle, [])) for cle, libelle in
                 analytique.PRODUITS + analytique.CHARGES + [("proprietaire", "Part du propriétaire (contrat)")]]
    return render(request, "transport/analytique_vehicule.html", {
        **filtres, "vehicule": vehicule, "totaux": compte["totaux"], "rubriques": rubriques,
        "voyages": vehicule.departs.filter(date__range=(filtres["du"], filtres["au"]))
        .exclude(statut__in=[Depart.ANNULE, Depart.PROGRAMME]).select_related("ligne").order_by("date", "heure"),
        "historique_gamme": vehicule.changements_gamme.all(),
        "contrats": vehicule.contrats_partenaire.exclude(statut="BROUILLON").select_related("partenaire")})


@login_required
def analytique_proprietaires(request):
    from . import analytique

    filtres, _ = _filtres_analytiques(request)
    return render(request, "transport/analytique_proprietaires.html", {
        **filtres, "portefeuilles": analytique.proprietaires(filtres["du"], filtres["au"], filtres["gamme"])})


# ---------------------------------------------------------------- Dépenses de fonctionnement autorisées par le siège
@login_required
def depenses_fonctionnement(request):
    from apps.comptabilite.models import Journal
    from apps.core.models import Agence

    from .models_depenses import DemandeDepense

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "demander":
                d = DemandeDepense(
                    date=_jour(request, "date") if request.POST.get("date") else timezone.localdate(),
                    agence=request.POST.get("agence", ""), nature=request.POST.get("nature", DemandeDepense.AUTRE),
                    libelle=request.POST.get("libelle", "").strip(), beneficiaire=request.POST.get("beneficiaire", "").strip(),
                    montant=Decimal(request.POST.get("montant") or 0),
                    vehicule=Vehicule.objects.filter(pk=request.POST.get("vehicule") or None).first())
                if not d.libelle:
                    raise ValidationError("Indiquez le libellé de la dépense.")
                d.demander(request.user)
                messages.success(request, f"Demande {d.numero} enregistrée : {d.get_statut_display().lower()}.")
            else:
                d = get_object_or_404(DemandeDepense, pk=request.POST.get("demande"))
                if action in ("autoriser", "refuser"):
                    d.decider(action == "autoriser", request.user, request.POST.get("motif", ""))
                    messages.success(request, f"Demande {d.numero} : {d.get_statut_display().lower()}.")
                elif action == "payer":
                    d.payer(get_object_or_404(Journal, pk=request.POST.get("caisse")), request.user)
                    messages.success(request, f"Dépense {d.numero} payée.")
                elif action == "annuler":
                    d.annuler(request.POST.get("motif", ""), request.user)
                    messages.success(request, f"Demande {d.numero} annulée.")
        except (ValidationError, ArithmeticError, ValueError) as exc:
            _erreur(request, exc)
        return redirect(request.path + (f"?statut={request.GET['statut']}" if request.GET.get("statut") else ""))
    qs = DemandeDepense.objects.select_related("vehicule", "caisse")
    if request.GET.get("statut"):
        qs = qs.filter(statut=request.GET["statut"])
    from apps.echanges.publication import site_local

    local = site_local()
    return render(request, "transport/depenses_fonctionnement.html", {
        "demandes": qs[:300], "natures": DemandeDepense.NATURES, "statuts": DemandeDepense.STATUTS,
        "statut": request.GET.get("statut", ""), "decision_ici": DemandeDepense.autorisation_locale(),
        "local": local, "agences": Agence.objects.exclude(code="").order_by("rang", "code"),
        "vehicules": Vehicule.objects.filter(actif=True),
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False),
        "plafond": ParametresTransport.get().plafond_depense_sans_autorisation})
