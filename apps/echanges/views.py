"""Fichier › Échanges entre agences : préparer le fichier à envoyer, intégrer les fichiers reçus, suivre les manques."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.core.models import Agence

from . import lots
from .models import Evenement, EvenementRecu, LotEmis, LotRecu
from .publication import site_local


def _fichier(nom, octets):
    reponse = HttpResponse(octets, content_type="application/octet-stream")
    reponse["Content-Disposition"] = f'attachment; filename="{nom}"'
    return reponse


@login_required
def echanges(request, module, administration=False):
    local = site_local()
    if request.method == "POST":
        action = request.POST.get("action")
        reservee = action in ("siege", "agence", "installation", "installer")
        if reservee and not request.user.is_superuser:
            messages.error(request, "Réservé à l'administrateur.")
            return redirect(request.path)
        try:
            if action == "siege":
                lots.configurer_siege(request.POST["code"].strip().upper(), request.POST["nom"].strip())
                messages.success(request, "Ce poste est maintenant le siège. Déclarez vos agences.")
            elif action == "agence":
                a = lots.ajouter_agence(request.POST["code"].strip().upper(), request.POST["nom"].strip(),
                                        request.POST.get("ville", "").strip())
                messages.success(request, f"Agence {a.code} déclarée. Téléchargez son fichier d'installation.")
            elif action == "installation":
                return _fichier(*lots.fichier_installation(Agence.objects.get(pk=request.POST["agence"]), request.user))
            elif action == "installer":
                f = request.FILES["fichier"]
                rapport = lots.installer_agence(f.read(), f.name, request.user)
                messages.success(request, f"Agence {site_local().code} installée. {rapport.texte()}")
            elif action == "exporter":
                return _fichier(*lots.exporter(Agence.objects.get(pk=request.POST["destination"]), request.user,
                                               depuis=int(request.POST["depuis"]) if request.POST.get("depuis") else None))
            elif action == "synchroniser":
                from . import synchro

                boite = synchro.boite_configuree()
                if boite is None:
                    raise ValueError("aucune boîte aux lettres n'est configurée sur ce serveur")
                bilan = synchro.synchroniser(boite, request.user)
                (messages.warning if bilan.erreurs else messages.success)(request, f"{boite} : {bilan.texte()}")
            elif action == "importer":
                for f in request.FILES.getlist("fichiers"):
                    try:
                        rapport = lots.importer(f.read(), f.name, request.user)
                        (messages.warning if rapport.attente or rapport.conflits or rapport.rejets or rapport.manques
                         else messages.success)(request, f"{f.name} : {rapport.texte()}")
                    except lots.LotInvalide as exc:
                        messages.error(request, f"{f.name} refusé : {exc}")
        except (lots.LotInvalide, KeyError, ValueError, Agence.DoesNotExist) as exc:
            messages.error(request, f"Opération impossible : {exc}")
        return redirect(request.path)
    sites = []
    if local is not None:
        for a in Agence.objects.filter(uid__isnull=False).exclude(pk=local.pk).select_related("compte_liaison"):
            dernier = LotEmis.objects.filter(destination=a).first()
            sites.append({"agence": a, "dernier_envoi": dernier,
                          "attente": EvenementRecu.objects.filter(site_origine=a, statut=EvenementRecu.ATTENTE).count(),
                          "conflits": EvenementRecu.objects.filter(site_origine=a, statut__in=[EvenementRecu.CONFLIT,
                                                                                                EvenementRecu.REJET]).count()})
    from .synchro import boite_configuree

    boite = boite_configuree()
    return render(request, "echanges/echanges.html", {
        "administration_poste": administration, "onglet_poste": "echanges",
        "titre": "Échanges entre agences", "local": local, "sites": sites, "boite": str(boite) if boite else "",
        "a_envoyer": Evenement.objects.filter(sequence__gt=_dernier_envoye()).count() if local else 0,
        "lots_recus": LotRecu.objects.select_related("source")[:15], "lots_emis": LotEmis.objects.select_related("destination")[:15],
        "problemes": EvenementRecu.objects.exclude(statut__in=[EvenementRecu.INTEGRE, EvenementRecu.IGNORE])
                                          .select_related("site_origine")[:50]})


def _dernier_envoye():
    from django.db.models import Max

    return LotEmis.objects.aggregate(m=Max("sequence_a"))["m"] or 0


# ---------------------------------------------------------------- Demandes de correction (direction → agence)
@login_required
def corrections(request):
    """Direction : toutes les demandes envoyées aux agences. Agence : les demandes reçues de la direction."""
    from .models import DemandeCorrection

    local = site_local()
    demandes = DemandeCorrection.objects.all()
    statut, agence = request.GET.get("statut", "ouvertes"), request.GET.get("agence", "")
    if statut == "ouvertes":
        demandes = demandes.filter(statut__in=DemandeCorrection.OUVERTS)
    elif statut:
        demandes = demandes.filter(statut=statut)
    if agence:
        demandes = demandes.filter(agence=agence)
    toutes = DemandeCorrection.objects.all()
    return render(request, "echanges/corrections.html", {
        "local": local, "demandes": demandes, "statut": statut, "agence": agence, "statuts": DemandeCorrection.STATUTS,
        "agences": sorted(set(toutes.values_list("agence", flat=True))),
        "compteurs": {"ouvertes": toutes.filter(statut__in=DemandeCorrection.OUVERTS).count(),
                      "en_retard": sum(1 for d in toutes.filter(statut__in=DemandeCorrection.OUVERTS) if d.en_retard),
                      "contestees": toutes.filter(statut=DemandeCorrection.CONTESTEE).count()}})


@login_required
def correction_demander(request, pk):
    """Direction : signaler une erreur sur une écriture reçue d'une agence."""
    import datetime

    from django.core.exceptions import ValidationError
    from django.shortcuts import get_object_or_404

    from apps.comptabilite.models import Ecriture

    from . import corrections as service

    ecriture = get_object_or_404(Ecriture, pk=pk)
    echeance = datetime.date.today() + datetime.timedelta(days=7)
    if request.method == "POST":
        try:
            saisie = request.POST.get("echeance") or ""
            d = service.demander(ecriture, request.POST.get("motif", ""), request.POST.get("correction_attendue", ""),
                                 request.user.get_username(), datetime.date.fromisoformat(saisie) if saisie else None)
            messages.success(request, f"Demande {d.numero} enregistrée : elle part à l'agence {d.agence} avec le prochain "
                                      "fichier d'échange.")
            return redirect("comptabilite:correction_detail", pk=d.pk)
        except (ValidationError, ValueError) as exc:
            for m in getattr(exc, "messages", [str(exc)]):
                messages.error(request, m)
    return render(request, "echanges/correction_demander.html", {"ecriture": ecriture, "echeance": echeance,
                                                                  "local": site_local()})


@login_required
def correction_detail(request, pk):
    """Suivi d'une demande ; à l'agence : corriger (écritures de correction) ou contester ; à la direction : annuler."""
    import datetime

    from django.core.exceptions import ValidationError
    from django.shortcuts import get_object_or_404

    from apps.comptabilite.models import Ecriture

    from . import corrections as service
    from .models import DemandeCorrection

    d = get_object_or_404(DemandeCorrection, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "annuler":
                service.annuler(d, request.user.get_username(), request.POST.get("motif", ""))
                messages.success(request, "Demande annulée ; l'agence en sera informée par le prochain fichier.")
            elif action in ("corriger", "contester"):
                choisies = Ecriture.objects.filter(pk__in=request.POST.getlist("ecritures"))
                service.repondre(d, DemandeCorrection.CORRIGEE if action == "corriger" else DemandeCorrection.CONTESTEE,
                                 request.POST.get("reponse", ""), request.user.get_username(), choisies)
                messages.success(request, "Réponse enregistrée ; elle part à la direction avec le prochain fichier.")
            return redirect("comptabilite:correction_detail", pk=d.pk)
        except ValidationError as exc:
            for m in exc.messages:
                messages.error(request, m)
    origine = Ecriture.objects.filter(uid=d.ecriture_uid).first()
    candidates = []
    if d.site_origine and d.ouverte:                    # à l'agence : ses écritures validées depuis la demande
        depuis = (d.demandee_le.date() if d.demandee_le else datetime.date.today()) - datetime.timedelta(days=3)
        candidates = (Ecriture.objects.filter(site_origine="", statut=Ecriture.STATUT_VALIDEE, cree_le__date__gte=depuis)
                      .exclude(uid=d.ecriture_uid).select_related("journal").order_by("-date", "-id")[:100])
    return render(request, "echanges/correction_detail.html", {
        "d": d, "origine": origine, "candidates": candidates, "local": site_local(),
        "correctives": Ecriture.objects.filter(uid__in=d.ecritures_correction).select_related("journal")})
