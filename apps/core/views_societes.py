"""Écran de consultation du catalogue multi-sociétés.

La sélection effective sera branchée sur le redémarrage du serveur local.
Ne jamais modifier la connexion Django à chaud.
"""
import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .catalogue_societes import lire_catalogue, regrouper


@login_required
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
    return render(request, "core/choix_societe.html", {
        "groupes": regrouper(bases, request.GET.get("q", ""), request.GET.get("clotures") == "1"),
        "recherche": request.GET.get("q", ""),
        "afficher_clotures": request.GET.get("clotures") == "1",
        "erreur": erreur,
    })
