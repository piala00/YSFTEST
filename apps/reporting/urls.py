from django.urls import path

from apps.comptabilite import views as compta_views
from apps.core import views as core_views
from apps.transport import views as transport_views

from . import views, views_analyses

app_name = "reporting"

urlpatterns = [
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("autorisations/", core_views.autorisations, {"module": "reporting"}, name="autorisations"),
    path("journal-evenements/", core_views.journal_evenements, {"module": "reporting"}, name="journal_evenements"),
    path("sauvegarde/", core_views.sauvegarde, {"module": "reporting"}, name="sauvegarde"),
    path("", views.dashboard, name="dashboard"),
    path("etats/", views_analyses.catalogue, name="catalogue"),
    path("evolution/", views_analyses.evolution, name="evolution"),
    path("comparaison/", views_analyses.comparaison, name="comparaison"),
    path("mensuel/", views_analyses.matrice, name="matrice"),
    path("classement/", views_analyses.classement, name="classement"),
    path("ventes/", views.ventes, name="ventes"),
    path("balance-agee/", views.balance_agee, name="balance_agee"),
    path("rapport-commercial/", views.rapport_commercial, name="rapport_commercial"),
    path("transport/comparaisons/", transport_views.comparaisons, name="comparaisons_transport"),
    path("transport/", views_analyses.transport_tableau_de_bord, name="transport_tableau_de_bord"),
    path("transport/billetterie/", views_analyses.transport_billetterie, name="transport_billetterie"),
    path("transport/colis/", views_analyses.transport_colis, name="transport_colis"),
    path("bilan/", compta_views.bilan_view, name="bilan"),
    path("compte-de-resultat/", compta_views.compte_resultat_view, name="compte_resultat"),
]
