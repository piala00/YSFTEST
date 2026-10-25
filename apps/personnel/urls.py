from django.urls import path

from apps.core.urls_communes import urls_communes

from . import views

app_name = "personnel"

urlpatterns = [
    *urls_communes("personnel"),
    path("employes/", views.employes, name="employes"),
    path("employes/nouveau/", views.employe_form, name="employe_create"),
    path("employes/<int:pk>/", views.employe_form, name="employe_update"),
    path("rubriques/", views.rubriques, name="rubriques"),
    path("rubriques/nouvelle/", views.rubrique_form, name="rubrique_create"),
    path("rubriques/<int:pk>/", views.rubrique_form, name="rubrique_update"),
    path("avances/", views.avances, name="avances"),
    path("avances/nouvelle/", views.avance_form, name="avance_create"),
    path("paie/", views.paies, name="paies"),
    path("paie/<int:pk>/", views.paie, name="paie"),
    path("paie/bulletin/<int:pk>/", views.bulletin, name="bulletin"),
]
