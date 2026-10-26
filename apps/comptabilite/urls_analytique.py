"""Logiciel « Comptabilité analytique » : affichage distinct, sur la même comptabilité que la Comptabilité générale.

Les états analytiques restent servis par les vues de la comptabilité (une seule source : les lignes d'écriture
générales, avec leur véhicule et leur section) ; ce module leur donne leur propre accueil et leurs menus.
"""
from django.urls import path

from apps.core import views as core_views

from . import views

app_name = "analytique"

urlpatterns = [
    path("", core_views.accueil_module, {"module": "analytique"}, name="accueil"),
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("autorisations/", core_views.autorisations, {"module": "analytique"}, name="autorisations"),
    path("journal-evenements/", core_views.journal_evenements, {"module": "analytique"}, name="journal_evenements"),
    path("sauvegarde/", core_views.sauvegarde, {"module": "analytique"}, name="sauvegarde"),
    path("sections/", views.structure_liste, {"structure": "sections"}, name="sections"),
]
