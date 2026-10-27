"""API du relais (activée seulement si RELAIS_ACTIF=1) :
    POST   /relais/v1/boites/<code>/        déposer un lot pour <code> (en-tête X-Nom-Lot)
    GET    /relais/v1/boites/<code>/        lister les lots de sa propre boîte
    GET    /relais/v1/boites/<code>/<nom>   lire un lot de sa boîte
    DELETE /relais/v1/boites/<code>/<nom>   le retirer après intégration
Authentification : « Authorization: Bearer <jeton du site> ». Un site ne lit et ne vide que sa propre boîte.
"""
import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import LotDepose, SiteRelais, empreinte

NOM_VALIDE = re.compile(r"^ERP-LOT-[A-Za-z0-9_-]+\.erpx\.chiffre$")
TAILLE_MAX = 60 * 1024 * 1024


def _dossier():
    return Path(getattr(settings, "RELAIS_DOSSIER", settings.BASE_DIR / "relais-stockage"))


def _site(request):
    entete = request.headers.get("Authorization", "")
    if not entete.startswith("Bearer "):
        return None
    site = SiteRelais.objects.filter(empreinte_jeton=empreinte(entete[7:].strip()), actif=True).first()
    if site is not None:
        SiteRelais.objects.filter(pk=site.pk).update(dernier_contact=timezone.now())
    return site


def _erreur(message, statut):
    return JsonResponse({"erreur": message}, status=statut)


@csrf_exempt
def boite(request, code):
    if not getattr(settings, "RELAIS_ACTIF", False):
        raise Http404
    site = _site(request)
    if site is None:
        return _erreur("jeton absent ou inconnu", 401)
    destination = SiteRelais.objects.filter(code=code, actif=True).first()
    if destination is None:
        return _erreur("site destinataire inconnu du relais", 404)
    if request.method == "POST":
        nom = request.headers.get("X-Nom-Lot", "")
        if not NOM_VALIDE.match(nom) or f"-vers-{code}-" not in nom or not nom.startswith(f"ERP-LOT-{site.code}-vers-"):
            return _erreur("nom de lot refusé", 400)
        corps = request.body
        if not corps or len(corps) > TAILLE_MAX:
            return _erreur("lot vide ou trop volumineux", 413)
        dossier = _dossier() / code
        dossier.mkdir(parents=True, exist_ok=True)
        provisoire = dossier / f".{nom}.part"
        provisoire.write_bytes(corps)
        provisoire.replace(dossier / nom)
        LotDepose.objects.update_or_create(destination=destination, nom=nom, defaults={
            "expediteur": site, "taille": len(corps), "empreinte": hashlib.sha256(corps).hexdigest()})
        return JsonResponse({"depose": nom}, status=201)
    if site.pk != destination.pk:
        return _erreur("un site ne lit que sa propre boîte", 403)
    if request.method == "GET":
        return JsonResponse({"lots": list(destination.boite.values_list("nom", flat=True))})
    return _erreur("méthode non prise en charge", 405)


@csrf_exempt
def lot(request, code, nom):
    if not getattr(settings, "RELAIS_ACTIF", False):
        raise Http404
    site = _site(request)
    if site is None:
        return _erreur("jeton absent ou inconnu", 401)
    if site.code != code:
        return _erreur("un site ne lit que sa propre boîte", 403)
    depose = LotDepose.objects.filter(destination=site, nom=nom).first()
    if depose is None or not NOM_VALIDE.match(nom):
        return _erreur("lot introuvable", 404)
    chemin = _dossier() / code / nom
    if request.method == "GET":
        if not chemin.exists():
            return _erreur("lot introuvable", 404)
        return FileResponse(open(chemin, "rb"), content_type="application/octet-stream")
    if request.method == "DELETE":
        chemin.unlink(missing_ok=True)
        depose.delete()
        return JsonResponse({"retire": nom})
    return _erreur("méthode non prise en charge", 405)
