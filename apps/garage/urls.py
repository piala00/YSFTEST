from django.urls import path

from apps.core.urls_communes import urls_communes

from . import views

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
]
