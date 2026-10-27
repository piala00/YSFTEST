"""API du relais (activée seulement si RELAIS_ACTIF=1) :
    POST   /relais/v1/boites/<code>/        déposer un lot pour <code> (en-tête X-Nom-Lot)
    GET    /relais/v1/boites/<code>/        lister les lots de sa propre boîte
    GET    /relais/v1/boites/<code>/<nom>   lire un lot de sa boîte
    DELETE /relais/v1/boites/<code>/<nom>   le retirer après intégration
Authentification : « Authorization: Bearer <jeton du site> ». Un site ne lit et ne vide que sa propre boîte.
"""
import hashlib
import re
import secrets
from pathlib import Path

from django.conf import settings
from django.db import transaction
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
        try:
            annonce = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            annonce = 0
        if not 0 < annonce <= TAILLE_MAX:                         # refusé avant de lire quoi que ce soit
            return _erreur("lot vide, de taille non annoncée ou trop volumineux", 413)
        dossier = _dossier() / code
        dossier.mkdir(parents=True, exist_ok=True)
        provisoire = dossier / f".{nom}.{secrets.token_hex(4)}.part"
        empreinte_lot, taille = hashlib.sha256(), 0
        try:
            with open(provisoire, "wb") as f:                     # lecture en flux, bornée
                while bloc := request.read(1024 * 1024):
                    taille += len(bloc)
                    if taille > TAILLE_MAX:
                        return _erreur("lot trop volumineux", 413)
                    empreinte_lot.update(bloc)
                    f.write(bloc)
            if taille != annonce:
                return _erreur("lot incomplet", 400)
            final, signature = dossier / nom, empreinte_lot.hexdigest()
            with transaction.atomic():
                deja = LotDepose.objects.select_for_update().filter(destination=destination, nom=nom).first()
                if deja is not None and final.exists():
                    if deja.empreinte == signature:
                        return JsonResponse({"depose": nom, "deja": True}, status=201)   # même dépôt rejoué
                    return _erreur("un autre lot porte déjà ce nom : jamais écrasé", 409)
                provisoire.replace(final)
                LotDepose.objects.update_or_create(destination=destination, nom=nom, defaults={
                    "expediteur": site, "taille": taille, "empreinte": signature})
        finally:
            provisoire.unlink(missing_ok=True)
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
        depose.delete()
        chemin.unlink(missing_ok=True)
        return JsonResponse({"retire": nom})
    return _erreur("méthode non prise en charge", 405)
