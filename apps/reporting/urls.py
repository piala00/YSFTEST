from django.urls import path

from apps.comptabilite import views as compta_views

from . import views

app_name = "reporting"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ventes/", views.ventes, name="ventes"),
    path("balance-agee/", views.balance_agee, name="balance_agee"),
    path("bilan/", compta_views.bilan_view, name="bilan"),
    path("compte-de-resultat/", compta_views.compte_resultat_view, name="compte_resultat"),
]
