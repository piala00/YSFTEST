from django.urls import path

from . import views, views_poste, views_societes

app_name = "core"

urlpatterns = [
    path("", views.portail, name="portail"),
    path("demarrage/", views_poste.demarrage, name="demarrage"),
    path("choix-societe/", views_societes.choix_societe, name="choix_societe"),
    path("restaurer-societe/", views_poste.restaurer_societe, name="restaurer_societe"),
    path("installation/compte/", views_poste.installation_compte, name="installation_compte"),
    path("installation/", views_poste.installation, name="installation"),
    path("poste/", views_poste.administration_poste, name="poste"),
    path("poste/base/", views_poste.base_donnees, name="base_donnees"),
    # Sauvegarde intégrale (logique, .json / .erpcoffre) : même écran que le raccourci du menu
    # Fichier, rangé dans le hub Administration du poste (module « core » → onglets du poste).
    path("poste/sauvegarde/", views.sauvegarde, {"module": "core"}, name="sauvegarde_integrale"),
    path("poste/echanges/", views_poste.echanges_poste, name="echanges_poste"),
]
