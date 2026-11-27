"""Indicateur de fraîcheur des lots reçus au siège, sans sonder le réseau."""
from django import template
from django.db.models import Q

register = template.Library()


@register.inclusion_tag("comptabilite/_fraicheur_agences.html", takes_context=True)
def fraicheur_agences(context):
    """Expose les dernières réceptions au siège, avec une lecture SQL par requête HTTP."""
    from apps.core.models import Agence

    request = context.get("request")
    if request is not None and hasattr(request, "_erp_fraicheur_agences"):
        return {"fraicheur_agences": request._erp_fraicheur_agences}

    # Une seule lecture récupère le dossier local et les agences affichables.
    # Le cache reste limité à la requête HTTP : une synchronisation suivante est visible.
    lignes = list(
        Agence.objects.filter(
            Q(locale=True)
            | Q(actif=True, role=Agence.AGENCE, locale=False)
        )
        .order_by("nom", "code")
        .values(
            "locale",
            "role",
            "code",
            "nom",
            "derniere_reception",
            "sequence_integree",
        )
    )
    siege_local = any(
        ligne["locale"] and ligne["role"] == Agence.SIEGE
        for ligne in lignes
    )
    agences = (
        [
            {
                "code": ligne["code"],
                "nom": ligne["nom"],
                "derniere_reception": ligne["derniere_reception"],
                "sequence_integree": ligne["sequence_integree"],
            }
            for ligne in lignes
            if not ligne["locale"]
        ]
        if siege_local
        else []
    )

    if request is not None:
        request._erp_fraicheur_agences = agences
    return {"fraicheur_agences": agences}
