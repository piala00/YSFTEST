"""Écran de consultation du catalogue multi-sociétés.

La sélection effective sera branchée sur le redémarrage du serveur local.
Ne jamais modifier la connexion Django à chaud.
"""
import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect

from . import poste
from .catalogue_societes import verifier_base_sqlite
from django.shortcuts import render

from .catalogue_societes import lire_catalogue, regrouper


@login_required
@require_http_methods(["GET", "POST"])
def choix_societe(request):
    """Liste les bases connues sans exposer les identifiants SQL ou les chemins de fichiers."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Sélection des bases réservée à l'administrateur.")
    fichier = os.environ.get("ERP_CATALOGUE_SOCIETES", "").strip()
    erreur = ""
    bases = []
    if fichier:
        try:
            bases = lire_catalogue(fichier)
        except (OSError, ValueError) as exc:
            erreur = f"Catalogue indisponible : {exc}"
    else:
        erreur = "Catalogue non configuré (ERP_CATALOGUE_SOCIETES)."
    if request.method == "POST":
        # La sélection est une opération sur le poste, jamais une bascule Django à chaud.
        if not poste.local(request) or not poste.disponible():
            return HttpResponseForbidden("Ouverture réservée au poste serveur compilé.")
        if request.POST.get("confirmation") != "OUVRIR":
            return HttpResponseForbidden("Confirmation OUVRIR requise.")
        identifiant = request.POST.get("base_id", "")
        cible = next((b for b in bases if b["id"] == identifiant), None)
        if cible is None:
            return HttpResponseForbidden("Base inconnue du catalogue.")
        if cible["moteur"] != "sqlite":
            return HttpResponseForbidden("Ouverture SQL Server non encore disponible.")
        try:
            fichier_valide = verifier_base_sqlite(cible["base"])
            # Déconnecter toutes les sessions de l'ancienne société au redémarrage :
            # les comptes et sessions proviennent de la nouvelle base isolée.
            connection.close()
            poste.appeler("configurer", {
                "DB_ENGINE": "sqlite", "SQLITE_FICHIER": fichier_valide,
                "DB_HOST": None, "DB_NAME": None, "DB_USER": None,
                "DB_PASSWORD": None, "DB_PORT": None,
                "MIROIR_DB_ENGINE": None,
            })
            logout(request)
            poste.appeler("redemarrer")
            return render(request, "core/redemarrage.html", {"titre": "Ouverture de la société"})
        except (OSError, ValueError, RuntimeError) as exc:
            erreur = f"Ouverture refusée : {exc}"
    return render(request, "core/choix_societe.html", {
        "groupes": regrouper(bases, request.GET.get("q", ""), request.GET.get("clotures") == "1"),
        "recherche": request.GET.get("q", ""),
        "afficher_clotures": request.GET.get("clotures") == "1",
        "erreur": erreur,
    })
