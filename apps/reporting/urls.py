from django.urls import path

from apps.comptabilite import views as compta_views
from apps.core import views as core_views
from apps.transport import views as transport_views

from . import views

app_name = "reporting"

urlpatterns = [
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("autorisations/", core_views.autorisations, {"module": "reporting"}, name="autorisations"),
    path("journal-evenements/", core_views.journal_evenements, {"module": "reporting"}, name="journal_evenements"),
    path("sauvegarde/", core_views.sauvegarde, {"module": "reporting"}, name="sauvegarde"),
    path("", views.dashboard, name="dashboard"),
    path("ventes/", views.ventes, name="ventes"),
    path("balance-agee/", views.balance_agee, name="balance_agee"),
    path("rapport-commercial/", views.rapport_commercial, name="rapport_commercial"),
    path("transport/comparaisons/", transport_views.comparaisons, name="comparaisons_transport"),
    path("bilan/", compta_views.bilan_view, name="bilan"),
    path("compte-de-resultat/", compta_views.compte_resultat_view, name="compte_resultat"),
]
