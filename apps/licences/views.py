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
    if request.method == "POST":
        fichier = request.FILES.get("fichier")
        if fichier is None or fichier.size > 64 * 1024:
            messages.error(request, "Choisissez le fichier de licence (.erplic) envoyé par l'éditeur.")
        else:
            try:
                _, donnees = l.deposer(fichier.read(), request.user)
                from apps.core import journal

                journal.enregistrer("LICENCE", libelle=f"{donnees.get('numero', '')} — {donnees.get('client', '')}")
                messages.success(request, f"Licence {donnees.get('numero', '')} installée pour {donnees.get('client', '')}.")
            except l.LicenceInvalide as exc:
                messages.error(request, f"Licence refusée : {exc}")
        return redirect(request.get_full_path())
    return render(request, "licences/licence.html", {
        "titre": "Licence", "etat": l.etat(), "code": l.code_activation(), "actifs": l.comptes_actifs(),
        "roles": l.ROLES, "historique": LicenceDeposee.objects.select_related("deposee_par")[:20],
        "cles": bool(l.cles_publiques())})
