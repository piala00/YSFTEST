import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import licence as l
from .models import LicenceDeposee


@login_required
def licence(request):
    """Fichier › Administration du poste › Licence : état, code d'activation, dépôt du fichier .erplic."""
    from apps.core import droits as d

    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {
            "chemin": "Licence", "operation": "gérer la licence", "niveau": "réservé à l'administrateur",
            "profil": d.profil_de(request.user) or "sans profil"}, status=403)
    if request.GET.get("demande"):
        from django.http import HttpResponse

        d = l.demande()
        reponse = HttpResponse(l.fc.demande_ecrire(d), content_type="text/plain; charset=utf-8")
        nom = re.sub(r"[^A-Za-z0-9]+", "-", f"{d['societe']}-{d['machine_nom']}").strip("-")[:60]
        reponse["Content-Disposition"] = f'attachment; filename="DEMANDE-LICENCE-{nom}.erpdem"'
        return reponse
    if request.method == "POST":
        from apps.core import journal

        action = request.POST.get("action", "fichier")
        try:
            if action == "installation":
                d = l.enregistrer_cle_installation(request.POST.get("cle", ""))
                journal.enregistrer("LICENCE", libelle=f"Installation enregistrée — {d['societe']}")
                messages.success(request, f"Clé d'installation enregistrée pour {d['societe']}.")
            elif action == "activation":
                _, donnees = l.activer(request.POST.get("cle", ""), request.user)
                journal.enregistrer("LICENCE", libelle=f"{donnees.get('numero', '')} — {donnees.get('client', '')}")
                messages.success(request, f"Licence {donnees.get('numero', '')} activée pour {donnees.get('client', '')}.")
            else:
                fichier = request.FILES.get("fichier")
                if fichier is None or fichier.size > 64 * 1024:
                    raise l.LicenceInvalide("choisissez le fichier de licence (.erplic) envoyé par l'éditeur")
                publique = request.FILES.get("verification")
                if publique is not None:
                    if publique.size > 8192:
                        raise l.LicenceInvalide("fichier de vérification trop volumineux")
                    l.verifier_fichier_public(publique.read())
                _, donnees = l.deposer(fichier.read(), request.user)
                journal.enregistrer("LICENCE", libelle=f"{donnees.get('numero', '')} — {donnees.get('client', '')}")
                messages.success(request, f"Licence {donnees.get('numero', '')} installée pour {donnees.get('client', '')}.")
        except l.LicenceInvalide as exc:
            messages.error(request, f"Refusé : {exc}")
        return redirect(request.path)
    return render(request, "licences/licence.html", {
        "onglet_poste": "licence",
        "titre": "Licence", "etat": l.etat(), "demande": l.demande(), "installation": l.cle_installation(),
        "installation_requise": l.cle_installation_requise(), "actifs": l.comptes_actifs(), "roles": l.ROLES,
        "essai_ouvertures": l.ESSAI_OUVERTURES,
        "historique": LicenceDeposee.objects.select_related("deposee_par")[:20], "cles": bool(l.cles_publiques())})
