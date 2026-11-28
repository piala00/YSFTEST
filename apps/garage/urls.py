from django.urls import path

from apps.core.urls_communes import urls_communes

from . import views, views_magasin

app_name = "garage"

urlpatterns = [
    *urls_communes("garage"),
    path("pleins/", views.pleins, name="pleins"),
    path("pleins/nouveau/", views.plein_form, name="plein_create"),
    path("reparations/", views.reparations, name="reparations"),
    path("reparations/nouvelle/", views.reparation_form, name="reparation_create"),
    path("reparations/<int:pk>/", views.reparation, name="reparation"),
    path("consommation/", views.consommation, name="consommation"),
    path("echeances/", views.echeances, name="echeances"),
    path("magasin/", views_magasin.stock, name="magasin_stock"),
    path("magasin/achats/", views_magasin.achats, name="magasin_achats"),
    path("magasin/achats/nouveau/", views_magasin.achat_nouveau, name="magasin_achat"),
    path("magasin/sorties/", views_magasin.sorties, name="magasin_sorties"),
]
