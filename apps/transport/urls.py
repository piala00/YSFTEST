from django.urls import path

from apps.core import views as core_views
from apps.echanges import views as echanges_views

from . import views

app_name = "transport"

urlpatterns = [
    path("", core_views.accueil_module, {"module": "transport"}, name="accueil"),
    path("echanges/", echanges_views.echanges, {"module": "transport"}, name="echanges"),
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("autorisations/", core_views.autorisations, {"module": "transport"}, name="autorisations"),
    path("journal-evenements/", core_views.journal_evenements, {"module": "transport"}, name="journal_evenements"),
    path("sauvegarde/", core_views.sauvegarde, {"module": "transport"}, name="sauvegarde"),
    path("parametres/", views.parametres, name="parametres"),
    path("fiches/<str:genre>/", views.fiches, name="fiches"),
    path("fiches/<str:genre>/nouvelle/", views.fiche_form, name="fiche_create"),
    path("fiches/<str:genre>/<int:pk>/", views.fiche_form, name="fiche_update"),
    path("departs/", views.departs, name="departs"),
    path("departs/nouveau/", views.depart_form, name="depart_create"),
    path("departs/<int:pk>/", views.depart_detail, name="depart_detail"),
    path("departs/<int:pk>/modifier/", views.depart_form, name="depart_update"),
    path("departs/<int:pk>/manifeste/", views.manifeste, name="manifeste"),
    path("billets/", views.billets, name="billets"),
    path("billets/vendre/", views.billet_vente, name="billet_vente"),
    path("billets/<int:pk>/", views.billet_detail, name="billet_detail"),
    path("billets/<int:pk>/imprimer/", views.billet_imprimer, name="billet_imprimer"),
    path("colis/", views.colis_liste, name="colis"),
    path("colis/nouveau/", views.colis_form, name="colis_create"),
    path("colis/<int:pk>/", views.colis_detail, name="colis_detail"),
    path("colis/<int:pk>/imprimer/", views.colis_imprimer, name="colis_imprimer"),
    path("flotte/depenses/", views.depenses, name="depenses"),
    path("flotte/depenses/nouvelle/", views.depense_form, name="depense_create"),
    path("etats/recette/", views.recette_journaliere, name="recette"),
    path("etats/rentabilite/", views.rentabilite, name="rentabilite"),
]
