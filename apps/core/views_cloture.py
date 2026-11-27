"""Écran « Clôturer l'exercice et ouvrir le suivant ».

Déclenche le moteur de clôture annuelle N→N+1 : crée la base de l'année suivante
(configuration reprise + reports à nouveau des écritures validées), puis marque N
clôturé et lie N+1 à N dans le catalogue.
"""
import json
import os

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponseForbidden
from django.shortcuts import render

from . import poste
from .catalogue_societes import lire_catalogue


def _meme_fichier_sqlite(premier, second):
    """Compare deux chemins SQLite selon l'identité physique puis le chemin Windows normalisé."""
    if not premier or not second:
        return False
    try:
        if os.path.samefile(str(premier), str(second)):
            return True
    except (OSError, TypeError, ValueError):
        pass
    try:
        normaliser = lambda valeur: os.path.normcase(os.path.realpath(
            os.path.abspath(os.path.expanduser(str(valeur)))
        ))
        return normaliser(premier) == normaliser(second)
    except (OSError, TypeError, ValueError):
        return False


def _chemin_base_sqlite_active():
    """Retourne le fichier réellement ouvert par Django, pas seulement le réglage initial."""
    if connection.vendor != "sqlite":
        return None
    try:
        with connection.cursor() as curseur:
            curseur.execute("PRAGMA database_list")
            lignes = curseur.fetchall()
        chemin = next((ligne[2] for ligne in lignes
                       if len(ligne) >= 3 and ligne[1] == "main" and ligne[2]), None)
    except Exception:
        chemin = None
    return chemin or connection.settings_dict.get("NAME")


def _entree_courante(bases):
    """Entrée du catalogue correspondant au fichier SQLite réellement utilisé (ou None)."""
    chemin = _chemin_base_sqlite_active()
    if not chemin:
        return None
    for base in bases:
        if base.get("moteur") == "sqlite" and _meme_fichier_sqlite(base.get("base"), chemin):
            return base
    return None


def _diagnostic_recette_native(bases, courante, request):
    """Trace les chemins effectifs uniquement dans la recette Windows dédiée."""
    if os.environ.get("ERP_TEST_CLOTURE_NATIVE") != "1":
        return
    try:
        payload = {
            "engine": connection.vendor,
            "database_config": str(connection.settings_dict.get("NAME", "")),
            "database_open": str(_chemin_base_sqlite_active() or ""),
            "catalogue": os.environ.get("ERP_CATALOGUE_SOCIETES", ""),
            "catalogue_entries": len(bases),
            "current_id": courante.get("id") if courante else None,
            "current_year": courante.get("exercice") if courante else None,
            "is_superuser": bool(request.user.is_superuser),
            "compiled_post": poste.disponible(),
        }
        print("[CLOTURE-NATIVE-DIAG] " + json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception as exc:
        print(f"[CLOTURE-NATIVE-DIAG] diagnostic indisponible: {type(exc).__name__}: {exc}", flush=True)


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
    _diagnostic_recette_native(bases, courante, request)
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
        except Exception as exc:
            contexte["erreur"] = f"Clôture impossible, aucun changement : {exc}"
            return render(request, "core/cloture_annuelle.html", contexte)
        contexte["succes"] = (f"Exercice {annee} créé et lié à l'exercice précédent (désormais clôturé). "
                              "Ouvrez-le avec « Ouvrir une société ».")
        contexte["annee_suivante"] = None
    return render(request, "core/cloture_annuelle.html", contexte)
