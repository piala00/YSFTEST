"""Indicateur de fraîcheur des lots reçus au siège, sans sonder le réseau."""
from django import template

register = template.Library()


@register.inclusion_tag("comptabilite/_fraicheur_agences.html")
def fraicheur_agences():
    """Expose les dernières réceptions enregistrées uniquement sur le dossier siège."""
    from apps.core.models import Agence

    role_local = Agence.objects.filter(locale=True).values_list("role", flat=True).first()
    if role_local != Agence.SIEGE:
        return {"fraicheur_agences": []}

    agences = (
        Agence.objects.filter(actif=True, role=Agence.AGENCE, locale=False)
        .order_by("nom", "code")
        .values("code", "nom", "derniere_reception", "sequence_integree")
    )
    return {"fraicheur_agences": list(agences)}
