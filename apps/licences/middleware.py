"""Programme compilé seulement (ERP_LICENCE) : lecture seule après expiration, nombre de postes."""
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import render

# Toujours permis, même en lecture seule : se connecter, déposer une licence, sauvegarder ou restaurer, administrer
# le poste, et les échanges (une agence continue d'envoyer ses données à la direction).
LIBRES = ("/connexion/", "/deconnexion/", "/installation/", "/poste/", "/licence/", "/relais/", "/static/")
LIBRES_DANS = ("/sauvegarde/", "/echanges/")
SURES = ("GET", "HEAD", "OPTIONS")


class LicenceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ERP_LICENCE and not request.path.startswith(LIBRES):
            reponse = self.controler(request)
            if reponse is not None:
                return reponse
        return self.get_response(request)

    def controler(self, request):
        from . import licence

        etat = licence.etat()
        if etat.lecture_seule and request.method not in SURES and not any(p in request.path for p in LIBRES_DANS):
            return render(request, "licences/lecture_seule.html", {"etat": etat}, status=403)
        if (request.user.is_authenticated and not request.user.is_superuser
                and licence.comptes_actifs() > etat.postes):
            logout(request)
            return render(request, "licences/trop_de_comptes.html", {"etat": etat, "actifs": licence.comptes_actifs()},
                          status=403)
        return None
