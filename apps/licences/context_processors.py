def licence(request):
    """Bandeau de licence : essai et rappel pour l'administrateur ; grâce et lecture seule pour tous."""
    from django.conf import settings

    if not settings.ERP_LICENCE or not request.user.is_authenticated:
        return {}
    from . import licence as l

    e = l.etat()
    visible = e.statut in ("grace", "expiree") or (request.user.is_superuser and (e.mode == "essai" or e.statut == "rappel"))
    return {"licence_bandeau": e if visible and e.message else None}
