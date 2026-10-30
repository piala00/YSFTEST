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
    """Assistant : 1. identité de la société, 2. rôle de ce serveur (un seul site, direction ou agence),
    3. base de données (SQLite, SQL Server, ou SQLite avec copie miroir vers SQL Server ; programme compilé)."""
    if not request.user.is_superuser:
        return redirect("core:portail")
    from apps.echanges import lots
    from apps.echanges.publication import site_local

    from apps.licences import licence as lic

    societe = Societe.get()
    etape = request.GET.get("etape") or "identite"
    prevue = poste.appeler("installation_prevue") if "installation_prevue" in poste.ACTIONS else {}
    if lic.cle_installation_requise() and lic.cle_installation() is None:
        etape = "cle"                                             # rien d'autre sans la clé remise par l'éditeur
        texte = request.POST.get("cle", "") if request.method == "POST" else prevue.get("cle_installation", "")
        if texte:
            try:
                d = lic.enregistrer_cle_installation(texte)
                messages.success(request, f"Clé d'installation acceptée : {d['societe']}.")
                return redirect(f"{request.path}?etape=identite")
            except lic.LicenceInvalide as exc:
                messages.error(request, f"Clé d'installation refusée : {exc}")
                if request.method == "POST":
                    return redirect(request.path)
    form = IdentiteSocieteForm(instance=Societe.get())
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
        if "configurer" in poste.ACTIONS:                          # programme compilé : choix de la base ensuite
            return redirect(f"{request.path}?etape=base")
        return _terminer(request)
    elif request.method == "POST" and etape == "base":
        from . import base_donnees as bd

        action = request.POST.get("action")
        try:
            if action == "sqlite":
                return _terminer(request)
            if action == "tester":
                messages.info(request, bd.tester_sqlserver(_reglage_formulaire(request.POST)))
            elif action in ("sqlserver", "miroir"):
                cible = _reglage_formulaire(request.POST)
                messages.info(request, bd.tester_sqlserver(cible))
                Societe.objects.filter(pk=societe.pk).update(assistant_termine=True)   # copié avec le reste
                if action == "miroir":
                    poste.appeler("configurer", {
                        "MIROIR_DB_ENGINE": "mssql", "MIROIR_DB_HOST": cible["HOST"], "MIROIR_DB_NAME": cible["NAME"],
                        "MIROIR_DB_USER": cible["USER"] or None, "MIROIR_DB_PASSWORD": cible["PASSWORD"] or None,
                        "MIROIR_DB_PYTHON_DRIVER": "mssql_python"})
                    poste.appeler("redemarrer")
                    return render(request, "core/redemarrage.html", {"titre": "Redémarrage"})
                bd.lancer_changement(cible, apres=lambda: poste.appeler("configurer", _configuration_sqlserver(cible)))
            elif action == "redemarrer":
                poste.appeler("redemarrer")
                return render(request, "core/redemarrage.html", {"titre": "Redémarrage"})
        except (ValueError, RuntimeError) as exc:
            messages.error(request, f"Impossible : {exc}")
        except Exception as exc:
            messages.error(request, f"Le serveur SQL a répondu : {str(exc)[:300]}")
        return redirect(f"{request.path}?etape=base")
    from . import base_donnees as bd

    return render(request, "core/installation.html", {
        "etape": etape, "form": form, "local": site_local(), "edition": societe.activite,
        "role_prevu": prevue.get("role", ""), "fichier_prevu": prevue.get("fichier_agence"),
        "changement": bd.ETAT_CHANGEMENT,
        "base_actuelle": bd.info() if etape == "base" else None,
        "erreur_base": poste.appeler("erreur_base") if "erreur_base" in poste.ACTIONS else ""})


def _terminer(request):
    from apps.echanges.publication import site_local

    Societe.objects.filter(pk=Societe.get().pk).update(assistant_termine=True)
    local = site_local()
    messages.success(request, "Configuration terminée." + (f" Ce serveur : {local.code} — {local.get_role_display()}." if local else "")
                     + " Pour des données d'essai : Fichier › Administration du poste › Simulation.")
    return redirect("core:portail")


@login_required
def administration_poste(request):
    """Fichier › Administration du poste : sauvegardes de la base, restauration, simulation, démarrage avec Windows."""
    from . import droits as d

    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {
            "chemin": "Fichier › Administration du poste", "operation": "administrer le serveur",
            "niveau": "réservé à l'administrateur", "profil": d.profil_de(request.user) or "sans profil"}, status=403)
    if not poste.disponible():
        return render(request, "core/poste.html", {"indisponible": True, "titre": "Administration du poste",
            "onglet_poste": "simulation" if request.GET.get("onglet") == "simulation" else "poste"})
    from apps.licences.licence import fonctions_pro_disponibles

    pro_ok, pro_message = fonctions_pro_disponibles()
    onglet = "simulation" if request.GET.get("onglet") == "simulation" else "poste"
    if request.method == "POST":
        action = request.POST.get("action")
        if not pro_ok and action in ("sauvegarder", "restaurer", "annuler_restauration"):
            messages.error(request, pro_message)
            return redirect(request.get_full_path())
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
                if "departs_jour" in request.POST or "scenarios_complets" in request.POST:
                    from .dossiers_simulation import normaliser_criteres
                    criteres = normaliser_criteres({"departs_jour": request.POST.get("departs_jour", "0"),
                        "echelle": request.POST.get("echelle", "1"), "scenarios_complets": request.POST.get("scenarios_complets") == "1"})
                    poste.appeler("simulation_creer", debut, duree, criteres)
                else:
                    poste.appeler("simulation_creer", debut, duree)
                messages.success(request, "Simulation lancée en arrière-plan : vous pouvez continuer à travailler. "
                                          "Cette page montre sa progression.")
            elif action == "simulation_supprimer":
                if request.POST.get("confirmation") != "SUPPRIMER":
                    raise ValueError("tapez SUPPRIMER pour confirmer")
                if request.POST.get("dossier"):
                    poste.appeler("simulation_supprimer", request.POST["dossier"])
                else:
                    poste.appeler("simulation_supprimer")
                messages.success(request, "Simulation supprimée (seul le dossier fictif est effacé).")
            elif action == "dossier_exporter":
                from django.http import FileResponse

                fichier = poste.appeler("dossier_exporter", request.POST.get("dossier", ""))
                return FileResponse(fichier, as_attachment=True, filename="ERP-SIMULATION.erpsim",
                                    content_type="application/zip")
            elif action == "dossier_importer":
                from .dossiers_simulation import MAX_ARCHIVE

                fichier = request.FILES.get("fichier")
                if fichier is None or fichier.size > MAX_ARCHIVE:
                    raise ValueError("choisissez un dossier de simulation .erpsim (512 Mo maximum)")
                poste.appeler("dossier_importer", fichier, (request.user.username, request.user.password))
                messages.success(request, "Dossier fictif importé séparément. Vous pourrez l'ouvrir dans ce logiciel avec vos identifiants administrateur.")
            elif action == "dossier_ancienne":
                poste.appeler("dossier_ancienne", (request.user.username, request.user.password))
                messages.success(request, "Ancienne simulation reprise dans un dossier importable ; le fichier d'origine est conservé.")
            elif action in ("dossier_ouvrir", "dossier_revenir"):
                if not poste.local(request) or request.POST.get("confirmation") != "OUVRIR":
                    raise ValueError("sur le serveur, terminez les saisies de tous les postes et tapez OUVRIR")
                identifiant = request.POST.get("dossier", "") if action == "dossier_ouvrir" else ""
                if action == "dossier_ouvrir" and not identifiant:
                    raise ValueError("choisissez le dossier fictif à ouvrir")
                poste.appeler("dossier_ouvrir", identifiant, (request.user.username, request.user.password))
                poste.appeler("redemarrer")
                return render(request, "core/redemarrage.html", {"titre": "Ouverture du dossier"})
            elif action == "demarrage_auto":
                messages.success(request, poste.appeler("demarrage_auto_basculer"))
        except (ValueError, RuntimeError, OSError) as exc:
            messages.error(request, f"Impossible : {exc}")
        retour = request.GET.copy()
        if (action or "").startswith(("simulation_", "dossier_")):
            retour["onglet"] = "simulation"
        return redirect(request.path + ("?" + retour.urlencode() if retour else ""))
    etat = poste.appeler("etat")
    simulation = etat.get("simulation") or {}
    from apps.licences.licence import etat as etat_licence

    return render(request, "core/poste.html", {"titre": "Administration du poste", "etat": etat, "simulation": simulation,
                                               "onglet_poste": onglet,
                                               "preparation_simulation": any(d.get("etat") == "preparation" for d in etat.get("simulations", [])),
                                               "licence_etat": etat_licence(), "pro_ok": pro_ok, "pro_message": pro_message})


def _reglage_formulaire(post):
    """Réglage SQL Server saisi à l'écran (compte Windows si l'utilisateur est vide)."""
    from . import base_donnees as bd

    hote, base = post.get("hote", "").strip(), post.get("base", "").strip() or "ERP"
    if not hote:
        raise ValueError("indiquez le serveur SQL (ex. SERVEUR\\SQLEXPRESS ou 192.168.1.10)")
    return bd.reglage_sqlserver(hote, base, post.get("utilisateur", "").strip(), post.get("mot_de_passe", ""),
                                post.get("port", "").strip())


def _configuration_sqlserver(reglage):
    return {"DB_ENGINE": "mssql", "DB_HOST": reglage["HOST"], "DB_NAME": reglage["NAME"], "DB_USER": reglage["USER"] or None,
            "DB_PASSWORD": reglage["PASSWORD"] or None, "DB_PORT": reglage["PORT"] or None, "DB_PYTHON_DRIVER": "mssql_python",
            "DB_EXTRA_PARAMS": "TrustServerCertificate=yes"}


@login_required
def base_donnees(request):
    """Fichier › Administration du poste › Base de données : état, vérifier, réparer, optimiser, sauvegarder,
    restaurer, changer de moteur (SQLite ↔ SQL Server), copie miroir, redémarrer."""
    from . import base_donnees as bd
    from . import droits as d

    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {
            "chemin": "Fichier › Administration du poste › Base de données", "operation": "administrer la base",
            "niveau": "réservé à l'administrateur", "profil": d.profil_de(request.user) or "sans profil"}, status=403)
    from apps.licences.licence import fonctions_pro_disponibles

    pro_ok, pro_message = fonctions_pro_disponibles()
    if not pro_ok:                                             # gestion de la base indisponible en version d'essai
        if request.method == "POST":
            messages.error(request, pro_message)
            return redirect(request.path)
        return render(request, "core/base_donnees.html", {"titre": "Base de données", "essai_bloque": pro_message,
            "onglet_poste": "sauvegardes" if request.GET.get("onglet") == "sauvegardes" else "base"})
    compile_ = poste.disponible()
    resultat = None
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "verifier":
                intacte, details = bd.verifier()
                resultat = {"ok": intacte, "titre": "Vérification de l'intégrité", "details": details}
            elif action == "structure":
                from . import structure_base

                resultat = {**structure_base.analyser(), "titre": "Analyse de la structure"}
            elif action == "migrer":
                from . import structure_base

                if not poste.local(request) or request.POST.get("confirmation") != "METTRE A JOUR":
                    raise ValueError("sur le poste serveur, terminez les saisies et tapez METTRE A JOUR pour confirmer")
                def sauvegarde_avant_structure():
                    return bd.sauvegarder_sqlserver() if bd.moteur() == "mssql" else poste.appeler("sauvegarder")
                resultat = {**structure_base.appliquer_migrations(sauvegarde_avant_structure), "titre": "Mise à jour de structure"}
            elif action == "reparer":
                if not poste.local(request):
                    raise ValueError("la réparation se lance sur le poste serveur après arrêt des saisies")
                bd.sauvegarder_sqlserver() if bd.moteur() == "mssql" else poste.appeler("sauvegarder")
                ok, message = bd.reparer()
                resultat = {"ok": ok, "titre": "Réparation", "details": [message]}
            elif action == "optimiser":
                if not poste.local(request):
                    raise ValueError("l'optimisation se lance sur le poste serveur après arrêt des saisies")
                bd.sauvegarder_sqlserver() if bd.moteur() == "mssql" else poste.appeler("sauvegarder")
                resultat = {"ok": True, "titre": "Optimisation", "details": [bd.optimiser()]}
            elif action == "sauvegarder":
                fichier = bd.sauvegarder_sqlserver() if bd.moteur() == "mssql" else poste.appeler("sauvegarder")
                messages.success(request, f"Sauvegarde faite : {fichier}")
            elif action == "restaurer":
                if request.POST.get("confirmation") != "RESTAURER":
                    raise ValueError("tapez RESTAURER pour confirmer")
                fichier = request.POST.get("fichier", "")
                if bd.moteur() == "mssql":
                    if fichier not in {s["nom"] for s in bd.sauvegardes_sqlserver()}:
                        raise ValueError("sauvegarde inconnue")
                    poste.appeler("restaurer_sqlserver_au_demarrage", fichier)
                else:
                    poste.appeler("restaurer_au_demarrage", fichier)
                messages.warning(request, "Restauration prévue au redémarrage (la base actuelle est sauvegardée d'abord). "
                                          "Cliquez sur « Redémarrer le logiciel » quand personne ne saisit.")
            elif action == "annuler_restauration":
                poste.appeler("restaurer_sqlserver_au_demarrage", None)
                poste.appeler("restaurer_au_demarrage", None)
                messages.success(request, "Restauration annulée.")
            elif action == "tester":
                resultat = {"ok": True, "titre": "Test de connexion", "details": [bd.tester_sqlserver(_reglage_formulaire(request.POST))]}
            elif action in ("vers_sqlserver", "vers_sqlite"):
                if request.POST.get("confirmation") != "CHANGER":
                    raise ValueError("tapez CHANGER pour confirmer")
                if action == "vers_sqlserver":
                    cible = _reglage_formulaire(request.POST)
                    bd.tester_sqlserver(cible)
                    configuration = _configuration_sqlserver(cible)
                else:
                    fichier = poste.appeler("nouveau_fichier_sqlite")
                    cible = bd.reglage_sqlite(fichier)
                    configuration = {"DB_ENGINE": "sqlite", "SQLITE_FICHIER": str(fichier)}
                bd.lancer_changement(cible, apres=lambda: poste.appeler("configurer", configuration))
                messages.info(request, "Copie lancée : cette page suit son avancement.")
            elif action == "miroir":
                if request.POST.get("desactiver"):
                    poste.appeler("configurer", {"MIROIR_DB_ENGINE": None})
                    messages.success(request, "Copie miroir désactivée au prochain démarrage.")
                else:
                    reglage = _reglage_formulaire(request.POST)
                    message = bd.tester_sqlserver(reglage)
                    poste.appeler("configurer", {
                        "MIROIR_DB_ENGINE": "mssql", "MIROIR_DB_HOST": reglage["HOST"], "MIROIR_DB_NAME": reglage["NAME"],
                        "MIROIR_DB_USER": reglage["USER"] or None, "MIROIR_DB_PASSWORD": reglage["PASSWORD"] or None,
                        "MIROIR_DB_PYTHON_DRIVER": "mssql_python",
                        "MIROIR_INTERVALLE_MINUTES": request.POST.get("intervalle") or "60"})
                    messages.success(request, f"{message} Copie miroir réglée : elle démarre au redémarrage du logiciel.")
            elif action == "planifier":
                from . import planification

                poste.appeler("configurer", planification.valider(request.POST))
                messages.success(request, "Programmation des sauvegardes enregistrée (appliquée tout de suite).")
            elif action == "redemarrer":
                poste.appeler("redemarrer")
                return render(request, "core/redemarrage.html", {"titre": "Redémarrage"})
        except (ValueError, RuntimeError, OSError) as exc:
            messages.error(request, f"Impossible : {exc}")
        except Exception as exc:                                  # erreur du serveur SQL : message lisible
            messages.error(request, f"Le serveur de base de données a répondu : {str(exc)[:400]}")
        if resultat is None:
            return redirect(request.get_full_path())
    info = bd.info()
    sauvegardes = []
    try:
        sauvegardes = (bd.sauvegardes_sqlserver() if info["moteur"] == "mssql"
                       else poste.appeler("etat")["sauvegardes"] if compile_ else [])
    except Exception as exc:
        messages.warning(request, f"Liste des sauvegardes indisponible : {str(exc)[:200]}")
    from django.conf import settings

    miroir = settings.DATABASES.get("miroir")
    from . import planification

    planif = poste.appeler("planification") if "planification" in poste.ACTIONS else {}
    return render(request, "core/base_donnees.html", {
        "onglet_poste": "sauvegardes" if request.GET.get("onglet") == "sauvegardes" else "base",
        "planif": planif, "reglages": planif.get("config") or planification.reglages(), "modes": planification.MODES,
        "titre": "Base de données", "info": info, "resultat": resultat, "sauvegardes": sauvegardes, "compile": compile_,
        "changement": bd.ETAT_CHANGEMENT,
        "restauration": (poste.appeler("restauration_sqlserver_prevue") or poste.appeler("etat")["restauration_prevue"])
        if compile_ else "",
        "miroir": f"{miroir.get('HOST', '')} · {miroir['NAME']}" if miroir else ""})


@login_required
def echanges_poste(request):
    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {"chemin": "Import et export agences",
            "operation": "administrer les échanges", "niveau": "réservé à l'administrateur"}, status=403)
    from apps.echanges.views import echanges

    return echanges(request, module="transport" if Societe.get().activite == "TRANSPORT" else "commercial",
                    administration=True)

