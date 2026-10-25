from django.urls import path

from apps.core import views as core_views
from apps.echanges import views as echanges_views
from apps.partenaires import views as partenaires_views
from apps.transport import views as transport_views
from apps.reporting import views as reporting_views

from . import views

app_name = "comptabilite"

urlpatterns = [
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("autorisations/", core_views.autorisations, {"module": "comptabilite"}, name="autorisations"),
    path("echanges/", echanges_views.echanges, {"module": "comptabilite"}, name="echanges"),
    path("vehicules/balance/", transport_views.balance_vehicules, name="balance_vehicules"),
    path("vehicules/grand-livre/", transport_views.grand_livre_vehicules, name="grand_livre_vehicules"),
    path("vehicules/<int:pk>/", transport_views.vehicule_fiche, name="vehicule_fiche"),
    path("analytique/vehicules/", transport_views.analytique_vehicules, name="analytique_vehicules"),
    path("analytique/vehicules/<int:pk>/", transport_views.analytique_vehicule, name="analytique_vehicule"),
    path("analytique/proprietaires/", transport_views.analytique_proprietaires, name="analytique_proprietaires"),
    path("analytique/proprietaires/releves/", partenaires_views.releve, name="analytique_releves"),
    path("analytique/proprietaires/releves/<int:pk>/", partenaires_views.releve, name="analytique_releve"),
    path("journal-evenements/", core_views.journal_evenements, {"module": "comptabilite"}, name="journal_evenements"),
    path("sauvegarde/", core_views.sauvegarde, {"module": "comptabilite"}, name="sauvegarde"),
    path("reprise-dossier/", core_views.reprise_dossier, {"module": "comptabilite"}, name="reprise_dossier"),
    path("", core_views.accueil_module, {"module": "comptabilite"}, name="accueil"),
    path("societe/", core_views.SocieteUpdateView.as_view(), name="societe"),
    path("balance-agee/", reporting_views.balance_agee, name="balance_agee"),
    path("exercices/", core_views.ExerciceListView.as_view(), name="exercices"),
    path("exercices/nouveau/", core_views.ExerciceCreateView.as_view(), name="exercice_create"),
    path("exercices/<int:pk>/", core_views.ExerciceUpdateView.as_view(), name="exercice_update"),
    path("plan/", views.CompteListView.as_view(), name="comptes"),
    path("plan/nouveau/", views.CompteCreateView.as_view(), name="compte_create"),
    path("plan/<int:pk>/", views.CompteUpdateView.as_view(), name="compte_update"),
    path("journaux/", views.JournalListView.as_view(), name="journaux"),
    path("journaux/nouveau/", views.JournalCreateView.as_view(), name="journal_create"),
    path("journaux/<int:pk>/", views.JournalUpdateView.as_view(), name="journal_update"),

    path("ecritures/", views.EcritureListView.as_view(), name="ecritures"),
    path("ecritures/saisie/", views.ecriture_create, name="ecriture_create"),
    path("ecritures/<int:pk>/", views.EcritureDetailView.as_view(), name="ecriture_detail"),
    path("ecritures/<int:pk>/modifier/", views.ecriture_update, name="ecriture_update"),
    path("ecritures/<int:pk>/valider/", views.ecriture_valider, name="ecriture_valider"),
    path("ecritures/<int:pk>/supprimer/", views.ecriture_supprimer, name="ecriture_supprimer"),

    path("journal/", views.journal_view, name="journal"),
    path("grand-livre/", views.grand_livre_view, name="grand_livre"),
    path("balance/", views.balance_view, name="balance"),
    path("bilan/", views.bilan_view, name="bilan"),
    path("compte-de-resultat/", views.compte_resultat_view, name="compte_resultat"),
    path("tva/", views.tva_view, name="tva"),
    path("lettrage/", views.lettrage_view, name="lettrage"),
    path("lettrage/delettrer/", views.delettrage, name="delettrage"),
    path("lettrage/automatique/", views.lettrage_auto_view, name="lettrage_auto"),
    path("rapprochement/", views.rapprochement_view, name="rapprochement"),
    path("tiers/justificatif-solde/", views.justificatif_solde_view, name="justificatif_solde"),
    path("tiers/statistiques/", views.statistiques_tiers_view, name="statistiques_tiers"),
    path("controles/liaison-commerciale/", views.controle_liaison_view, name="controle_liaison"),
    path("cloture/exercice/", views.cloture_exercice_view, name="cloture_exercice"),
    path("cloture/journaux/", views.cloture_journaux_view, name="cloture_journaux"),
    path("analytique/ventilation/", views.ventilation_view, name="ventilation"),
    path("analytique/balance/", views.balance_analytique_view, name="balance_analytique"),
    path("structure/<str:structure>/", views.structure_liste, name="structure"),
    path("structure/<str:structure>/nouveau/", views.structure_fiche, name="structure_create"),
    path("structure/<str:structure>/<int:pk>/", views.structure_fiche, name="structure_update"),
]
