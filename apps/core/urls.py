from django.urls import path

from . import views, views_poste

app_name = "core"

urlpatterns = [
    path("", views.portail, name="portail"),
    path("installation/compte/", views_poste.installation_compte, name="installation_compte"),
    path("installation/", views_poste.installation, name="installation"),
    path("poste/", views_poste.administration_poste, name="poste"),
    path("poste/base/", views_poste.base_donnees, name="base_donnees"),
    path("poste/echanges/", views_poste.echanges_poste, name="echanges_poste"),
]
