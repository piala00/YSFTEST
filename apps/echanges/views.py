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
def echanges(request, module):
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
    return render(request, "echanges/echanges.html", {
        "titre": "Échanges entre agences", "local": local, "sites": sites,
        "a_envoyer": Evenement.objects.filter(sequence__gt=_dernier_envoye()).count() if local else 0,
        "lots_recus": LotRecu.objects.select_related("source")[:15], "lots_emis": LotEmis.objects.select_related("destination")[:15],
        "problemes": EvenementRecu.objects.exclude(statut__in=[EvenementRecu.INTEGRE, EvenementRecu.IGNORE])
                                          .select_related("site_origine")[:50]})


def _dernier_envoye():
    from django.db.models import Max

    return LotEmis.objects.aggregate(m=Max("sequence_a"))["m"] or 0
