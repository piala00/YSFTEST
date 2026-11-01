"""Pages communes à chaque logiciel (accueil, à propos, autorisations, journal, sauvegarde, échanges)."""
from django.urls import path


def urls_communes(code, accueil=True):
    from apps.echanges import views as echanges_views

    from . import views

    return [
        *([path("", views.accueil_module, {"module": code}, name="accueil")] if accueil else []),
        path("a-propos/", views.a_propos, name="a_propos"),
        path("autorisations/", views.autorisations, {"module": code}, name="autorisations"),
        path("journal-evenements/", views.journal_evenements, {"module": code}, name="journal_evenements"),
        path("sauvegarde/", views.sauvegarde, {"module": code}, name="sauvegarde"),
        path("echanges/", echanges_views.echanges, {"module": code}, name="echanges"),
    ]
