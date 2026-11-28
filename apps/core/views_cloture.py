"""Écran « Clôturer l'exercice et ouvrir le suivant ».

Déclenche le moteur de clôture annuelle N→N+1 (déjà testé) : crée la base de l'année suivante
(configuration reprise + reports à nouveau des écritures validées), puis marque N clôturé et lie
N+1 à N dans le catalogue. La base N+1 s'ouvre ensuite par « Ouvrir une société ».

Comme pour « Choix de la société », la création effective est une opération du **poste serveur
compilé** (elle crée un nouveau fichier de base et fait migrer Django). Hors poste compilé, l'écran
explique la marche à suivre sans rien modifier.
"""
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from . import poste
from .catalogue_societes import lire_catalogue


def _entree_courante(bases):
    """Entrée du catalogue correspondant à la base SQLite en cours d'utilisation (ou None)."""
    from django.conf import settings

    actuel = settings.DATABASES.get("default", {})
    if not str(actuel.get("ENGINE", "")).endswith("sqlite3"):
        return None
    try:
        chemin = Path(str(actuel.get("NAME", ""))).resolve()
    except OSError:
        return None
    for base in bases:
        if base["moteur"] != "sqlite":
            continue
        try:
            if Path(base["base"]).resolve() == chemin:
                return base
        except OSError:
            continue
    return None


@login_required
def cloture_exercice_annuel(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Clôture réservée à l'administrateur.")
    contexte = {"titre": "Clôturer l'exercice et ouvrir le suivant", "onglet_poste": "base",
                "compile": poste.disponible()}
    fichier = os.environ.get("ERP_CATALOGUE_SOCIETES", "").strip()
    if not fichier:
        contexte["erreur"] = ("Catalogue multi-sociétés non configuré (ERP_CATALOGUE_SOCIETES). "
                              "La clôture annuelle « une base par année » nécessite ce catalogue.")
        return render(request, "core/cloture_annuelle.html", contexte)
    try:
        bases = lire_catalogue(fichier)
    except (OSError, ValueError) as exc:
        contexte["erreur"] = f"Catalogue indisponible : {exc}"
        return render(request, "core/cloture_annuelle.html", contexte)
    courante = _entree_courante(bases)
    contexte["courante"] = courante
    if courante and not courante["cloture"]:
        contexte["annee_suivante"] = int(courante["exercice"]) + 1

    if request.method == "POST":
        if not poste.local(request) or not poste.disponible():
            return HttpResponseForbidden("Clôture réservée au poste serveur compilé.")
        if request.POST.get("confirmation") != "CLOTURER":
            contexte["erreur"] = "Tapez CLOTURER pour confirmer la clôture."
            return render(request, "core/cloture_annuelle.html", contexte)
        if courante is None or courante["cloture"]:
            contexte["erreur"] = "Exercice courant introuvable dans le catalogue, ou déjà clôturé."
            return render(request, "core/cloture_annuelle.html", contexte)
        from .management.commands.cloturer_exercice import derive_parametres
        from .adaptateur_cloture_transport_sqlite import preparer_dossier_transport_sqlite

        try:
            destination, nouvel_identifiant, annee = derive_parametres(fichier, courante["id"])
            preparer_dossier_transport_sqlite(fichier, courante["id"], destination, nouvel_identifiant, annee)
        except Exception as exc:                       # moteur : échec = aucun changement (N+1 supprimée)
            contexte["erreur"] = f"Clôture impossible, aucun changement : {exc}"
            return render(request, "core/cloture_annuelle.html", contexte)
        contexte["succes"] = (f"Exercice {annee} créé et lié à l'exercice précédent (désormais clôturé). "
                              "Ouvrez-le avec « Ouvrir une société ».")
        contexte["annee_suivante"] = None
    return render(request, "core/cloture_annuelle.html", contexte)
