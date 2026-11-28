from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from . import droits as d
from .navigation import module_pour_chemin, structure_module


def chemin_titres(onglets, code):
    """« Traitement › Documents des ventes › Facture » pour un code d'entrée de menu."""
    def chercher(noeuds, chemin):
        for n in noeuds:
            if n.get("separateur"):
                continue
            if n["code"] == code:
                return chemin + [n["titre"]]
            trouve = chercher(n["enfants"], chemin + [n["titre"]])
            if trouve:
                return trouve
        return None
    for o in onglets:
        if o["code"] == code:
            return [o["titre"]]
        trouve = chercher(o["elements"], [o["titre"]])
        if trouve:
            return trouve
    return [code]



class ArchiveLectureSeuleMiddleware:
    """Interdit les mutations HTTP dans un exercice clôturé, tout en gardant la consultation.

    L'authentification, la déconnexion et le changement de dossier restent possibles :
    l'administrateur peut consulter l'archive puis revenir à l'exercice courant.
    """

    ACTIONS_AUTORISEES = {"login", "logout", "choix_societe"}
    METHODES_SANS_MUTATION = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in self.METHODES_SANS_MUTATION:
            return None
        nom = getattr(getattr(request, "resolver_match", None), "url_name", None)
        if nom in self.ACTIONS_AUTORISEES:
            return None
        from .catalogue_societes import base_courante_cloturee

        try:
            archivee = base_courante_cloturee()
        except (OSError, ValueError) as exc:
            return HttpResponse(
                "Catalogue des exercices indisponible : saisie refusée ; écriture refusée par sécurité. "
                f"Vérifiez le catalogue avant de reprendre les saisies ({exc}).",
                status=503,
            )
        if not archivee:
            return None
        return HttpResponseForbidden(
            "Exercice clôturé : cette base historique est en consultation seule. "
            "Ouvrez un exercice non clôturé pour effectuer une saisie."
        )


class AutorisationsMiddleware:
    """Applique Fichier › Autorisations d'accès à chaque page des logiciels."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.controler(request) or self.get_response(request)

    def controler(self, request):
        if not request.user.is_authenticated:
            return None
        module = module_pour_chemin(request.path)
        if module is None:
            return None
        droits = request.droits = d.Droits(request.user, module)
        if droits.acces == d.AUCUN:
            return render(request, "core/acces_refuse.html", {
                "chemin": module.titre, "operation": "ouvrir ce logiciel", "niveau": "Aucun accès",
                "profil": droits.profil or "sans profil"}, status=403)
        if droits.libre:
            return None
        onglets, actif = structure_module(module, request.path, request.GET)
        request.navigation = (module, onglets, actif)
        code = d.element_de_la_page(request, module, actif)
        if code is None:
            return None
        operation = d.operation_demandee(request)
        if droits.permet(code, operation):
            return None
        return render(request, "core/acces_refuse.html", {
            "chemin": " › ".join(chemin_titres(onglets, code)), "operation": operation,
            "niveau": d.LIBELLES[droits.niveau(code)], "profil": droits.profil,
        }, status=403)


class PremiereConfigurationMiddleware:
    """Programme compilé seulement (ERP_ASSISTANT) : tant qu'il n'y a pas d'administrateur, toute page mène à sa
    création ; ensuite l'administrateur passe par l'assistant (société, rôle du serveur) jusqu'à ce qu'il soit terminé."""
    LIBRES = ("/static/", "/demarrage/", "/restaurer-societe/", "/installation/", "/deconnexion/", "/relais/", "/api/")

    def __init__(self, get_response):
        self.get_response = get_response
        self.termine = False

    def __call__(self, request):
        from django.conf import settings

        if settings.ERP_ASSISTANT and not self.termine and not request.path.startswith(self.LIBRES):
            reponse = self.controler(request)
            if reponse is not None:
                return reponse
        return self.get_response(request)

    def controler(self, request):
        from django.contrib.auth import get_user_model
        from django.shortcuts import redirect

        from .models import Societe

        if not get_user_model().objects.filter(is_superuser=True).exists():
            return redirect("core:demarrage")                     # logiciel vide : créer ou restaurer une société
        if Societe.get().assistant_termine:
            self.termine = True                                   # plus aucune requête à la base ensuite
            return None
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect("core:installation")
        return None

