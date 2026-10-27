"""Premier démarrage (compte administrateur, identité, rôle du serveur) et Fichier › Administration du poste."""
import re

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from . import poste
from .forms import IdentiteSocieteForm
from .models import Societe


def installation_compte(request):
    """Aucun administrateur : on le crée ici, depuis le serveur lui-même seulement (jamais depuis un autre poste)."""
    U = get_user_model()
    if U.objects.filter(is_superuser=True).exists():
        return redirect("core:installation")
    if not poste.local(request):
        return render(request, "core/installation_compte.html", {"distant": True}, status=403)
    erreurs, identifiant = [], request.POST.get("identifiant", "admin").strip() or "admin"
    if request.method == "POST":
        mot_de_passe = request.POST.get("mot_de_passe", "")
        if mot_de_passe != request.POST.get("confirmation", ""):
            erreurs.append("Les deux mots de passe sont différents.")
        else:
            try:
                validate_password(mot_de_passe, U(username=identifiant))
            except ValidationError as exc:
                erreurs.extend(exc.messages)
        if not erreurs:
            u = U.objects.filter(username=identifiant).first() or U(username=identifiant)
            u.is_superuser = u.is_staff = u.is_active = True
            u.set_password(mot_de_passe)
            u.save()
            login(request, u, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("core:installation")
    return render(request, "core/installation_compte.html", {"erreurs": erreurs, "identifiant": identifiant})


@login_required
def installation(request):
    """Assistant : 1. identité de la société, 2. rôle de ce serveur (un seul site, direction ou agence)."""
    if not request.user.is_superuser:
        return redirect("core:portail")
    from apps.echanges import lots
    from apps.echanges.publication import site_local

    societe = Societe.get()
    etape = request.GET.get("etape") or "identite"
    prevue = poste.appeler("installation_prevue") if "installation_prevue" in poste.ACTIONS else {}
    form = IdentiteSocieteForm(instance=societe)
    if request.method == "POST" and etape == "identite":
        form = IdentiteSocieteForm(request.POST, instance=societe)
        if form.is_valid():
            form.save()
            return redirect(f"{request.path}?etape=role")
    elif request.method == "POST" and etape == "role":
        role = request.POST.get("role")
        try:
            if role == "siege":
                code = request.POST.get("code", "").strip().upper()
                if not re.fullmatch(r"[A-Z0-9_]{2,10}", code):
                    raise lots.LotInvalide("code de 2 à 10 lettres ou chiffres, sans espace (ex. SIEGE)")
                lots.configurer_siege(code, request.POST.get("nom", "").strip() or "Direction")
            elif role == "agence":
                fichier = request.FILES.get("fichier")
                if fichier is not None:
                    lots.installer_agence(fichier.read(), fichier.name, request.user)
                elif request.POST.get("fichier_prevu") and prevue.get("fichier_agence"):
                    chemin = prevue["fichier_agence"]
                    lots.installer_agence(chemin.read_bytes(), chemin.name, request.user)
                else:
                    raise lots.LotInvalide("choisissez le fichier d'installation remis par la direction")
            elif role != "seul":
                raise lots.LotInvalide("choisissez le rôle de ce serveur")
        except lots.LotInvalide as exc:
            messages.error(request, f"Impossible : {exc}")
            return redirect(f"{request.path}?etape=role")
        societe.refresh_from_db()
        societe.assistant_termine = True
        societe.save(update_fields=["assistant_termine"])
        local = site_local()
        messages.success(request, "Configuration terminée." + (f" Ce serveur : {local.code} — {local.get_role_display()}." if local else "")
                         + " Pour des données d'essai : Fichier › Administration du poste › Simulation.")
        return redirect("core:portail")
    return render(request, "core/installation.html", {
        "etape": etape, "form": form, "local": site_local(), "edition": societe.activite,
        "role_prevu": prevue.get("role", ""), "fichier_prevu": prevue.get("fichier_agence")})


@login_required
def administration_poste(request):
    """Fichier › Administration du poste : sauvegardes de la base, restauration, simulation, démarrage avec Windows."""
    from . import droits as d

    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {
            "chemin": "Fichier › Administration du poste", "operation": "administrer le serveur",
            "niveau": "réservé à l'administrateur", "profil": d.profil_de(request.user) or "sans profil"}, status=403)
    if not poste.disponible():
        return render(request, "core/poste.html", {"indisponible": True, "titre": "Administration du poste"})
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "sauvegarder":
                messages.success(request, f"Sauvegarde faite : {poste.appeler('sauvegarder')}")
            elif action == "restaurer":
                if request.POST.get("confirmation") != "RESTAURER":
                    raise ValueError("tapez RESTAURER pour confirmer")
                poste.appeler("restaurer_au_demarrage", request.POST.get("fichier", ""))
                messages.warning(request, "Restauration prévue : fermez la fenêtre noire du logiciel puis relancez-le. "
                                          "La base actuelle sera mise de côté, pas effacée.")
            elif action == "annuler_restauration":
                poste.appeler("restaurer_au_demarrage", None)
                messages.success(request, "Restauration annulée.")
            elif action == "simulation_creer":
                debut = request.POST.get("debut", "")
                if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", debut):
                    raise ValueError("mois de départ attendu au format AAAA-MM")
                duree = request.POST.get("duree", "")
                if duree != "aujourdhui" and not (duree.isdigit() and 1 <= int(duree) <= 24):
                    raise ValueError("durée : de 1 à 24 mois, ou jusqu'à aujourd'hui")
                poste.appeler("simulation_creer", debut, duree)
                messages.success(request, "Simulation lancée en arrière-plan : vous pouvez continuer à travailler. "
                                          "Cette page montre sa progression.")
            elif action == "simulation_supprimer":
                if request.POST.get("confirmation") != "SUPPRIMER":
                    raise ValueError("tapez SUPPRIMER pour confirmer")
                poste.appeler("simulation_supprimer")
                messages.success(request, "Simulation supprimée (seul le dossier fictif est effacé).")
            elif action == "demarrage_auto":
                messages.success(request, poste.appeler("demarrage_auto_basculer"))
        except (ValueError, RuntimeError, OSError) as exc:
            messages.error(request, f"Impossible : {exc}")
        return redirect(request.get_full_path())
    etat = poste.appeler("etat")
    hote = request.get_host().rsplit(":", 1)[0] if not request.get_host().endswith("]") else request.get_host()
    simulation = etat.get("simulation") or {}
    if simulation.get("port"):
        simulation["url"] = f"{request.scheme}://{hote}:{simulation['port']}/"
    from apps.licences.licence import etat as etat_licence

    return render(request, "core/poste.html", {"titre": "Administration du poste", "etat": etat, "simulation": simulation,
                                               "licence_etat": etat_licence()})
