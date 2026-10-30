"""Écrans du transport. Les chemins indiquent le logiciel du service qui les utilise :
/transport/billetterie/…, /transport/colis/…, /transport/garage/… ; le reste est la Direction de l'agence."""
from django.urls import path

from apps.core.urls_communes import urls_communes

from . import views

app_name = "transport"

urlpatterns = [
    *urls_communes("transport"),
    # Direction de l'agence
    path("parametres/", views.parametres, name="parametres"),
    path("fiches/<str:genre>/", views.fiches, name="fiches"),
    path("fiches/<str:genre>/nouvelle/", views.fiche_form, name="fiche_create"),
    path("fiches/<str:genre>/<int:pk>/", views.fiche_form, name="fiche_update"),
    path("etats/rapport-journalier/", views.rapport_journalier, name="rapport_journalier"),
    path("depenses-fonctionnement/", views.depenses_fonctionnement, name="depenses_fonctionnement"),
    path("etats/rapport-journalier/imprimer/", views.rapport_journalier_imprimer, name="rapport_journalier_imprimer"),
    path("etats/recette/", views.recette_journaliere, name="recette"),
    path("etats/rentabilite/", views.rentabilite, name="rentabilite"),
    path("etats/balance-vehicules/", views.balance_vehicules, name="balance_vehicules"),
    path("etats/grand-livre-vehicules/", views.grand_livre_vehicules, name="grand_livre_vehicules"),
    path("caisses/sessions/", views.sessions_caisse, name="sessions_caisse"),
    path("caisses/transferts/", views.transferts, name="transferts"),
    path("cloture/", views.cloture_journee, name="cloture"),
    path("voyages-a-cloturer/", views.voyages_a_cloturer, name="voyages_a_cloturer"),
    path("billetterie/caisse/", views.ma_caisse, {"service": "BILLETTERIE"}, name="ma_caisse_billetterie"),
    path("billetterie/cloture/", views.cloture_journee, {"perimetre": "BILLETTERIE"}, name="cloture_billetterie"),
    path("colis/caisse/", views.ma_caisse, {"service": "COLIS"}, name="ma_caisse_colis"),
    path("colis/cloture/", views.cloture_journee, {"perimetre": "COLIS"}, name="cloture_colis"),
    path("garage/cloture/", views.cloture_journee, {"perimetre": "GARAGE"}, name="cloture_garage"),
    path("billetterie/contacts/rechercher/", views.contacts_rechercher, {"service": "billetterie"}, name="contacts_billetterie"),
    path("colis/contacts/rechercher/", views.contacts_rechercher, {"service": "colis"}, name="contacts_colis"),
    # Billetterie
    path("billetterie/departs/", views.departs, name="departs"),
    path("billetterie/departs/nouveau/", views.depart_form, name="depart_create"),
    path("billetterie/departs/<int:pk>/", views.depart_detail, name="depart_detail"),
    path("billetterie/departs/<int:pk>/modifier/", views.depart_form, name="depart_update"),
    path("billetterie/departs/<int:pk>/manifeste/", views.manifeste, name="manifeste"),
    path("billetterie/billets/", views.billets, name="billets"),
    path("billetterie/billets/vendre/", views.billet_vente, name="billet_vente"),
    path("billetterie/billets/<int:pk>/", views.billet_detail, name="billet_detail"),
    path("billetterie/billets/<int:pk>/imprimer/", views.billet_imprimer, name="billet_imprimer"),
    path("billetterie/recette/", views.recette_journaliere, {"service": "billetterie"}, name="recette_billetterie"),
    # Colis et expéditions
    path("colis/envois/", views.colis_liste, name="colis"),
    path("colis/envois/nouveau/", views.colis_form, name="colis_create"),
    path("colis/envois/<int:pk>/", views.colis_detail, name="colis_detail"),
    path("colis/envois/<int:pk>/imprimer/", views.colis_imprimer, name="colis_imprimer"),
    path("colis/recette/", views.recette_journaliere, {"service": "colis"}, name="recette_colis"),
    # Garage : véhicules et autres dépenses (pleins et réparations : logiciel Garage)
    path("garage/vehicules/", views.fiches, {"genre": "vehicules"}, name="vehicules"),
    path("garage/vehicules/nouveau/", views.fiche_form, {"genre": "vehicules"}, name="vehicule_create"),
    path("garage/vehicules/<int:pk>/", views.vehicule_fiche, name="vehicule_fiche"),
    path("garage/vehicules/<int:pk>/modifier/", views.fiche_form, {"genre": "vehicules"}, name="vehicule_update"),
    path("garage/depenses/", views.depenses, name="depenses"),
    path("garage/depenses/nouvelle/", views.depense_form, name="depense_create"),
]

