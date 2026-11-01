from django.conf import settings


def dossier(request):
    return {"dossier_simulation": bool(getattr(settings, "ERP_DOSSIER_SIMULATION", ""))}
