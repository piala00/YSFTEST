from django.urls import path

from apps.core import views as core_views
from apps.reporting import views as reporting_views

from . import views

app_name = "commercial"

urlpatterns = [
    path("a-propos/", core_views.a_propos, name="a_propos"),
    path("", core_views.accueil_module, {"module": "commercial"}, name="accueil"),
    path("societe/", core_views.SocieteUpdateView.as_view(), name="societe"),
    path("etats/ventes/", reporting_views.ventes, name="etat_ventes"),
    path("etats/balance-agee/", reporting_views.balance_agee, name="etat_balance_agee"),
    path("etats/achats/", reporting_views.achats, name="etat_achats"),
    path("recherche/entetes/", views.recherche_entetes, name="recherche_entetes"),
    path("recherche/lignes/", views.recherche_lignes, name="recherche_lignes"),
    path("stock/mouvements/", views.MouvementListView.as_view(), name="mouvements"),
    path("stock/etat-inventaire/", views.EtatInventaireView.as_view(), name="etat_inventaire"),
    path("stock/inventaires/", views.InventaireListView.as_view(), name="inventaires"),
    path("stock/inventaires/nouveau/", views.inventaire_create, name="inventaire_create"),
    path("stock/inventaires/<int:pk>/", views.inventaire_detail, name="inventaire_detail"),
    path("depots/", views.DepotListView.as_view(), name="depots"),
    path("depots/nouveau/", views.DepotCreateView.as_view(), name="depot_create"),
    path("depots/<int:pk>/", views.DepotUpdateView.as_view(), name="depot_update"),
    path("clients/", views.TiersListView.as_view(), {"type_tiers": "CLIENT"}, name="clients"),
    path("fournisseurs/", views.TiersListView.as_view(), {"type_tiers": "FOURNISSEUR"}, name="fournisseurs"),
    path("tiers/nouveau/", views.TiersCreateView.as_view(), name="tiers_create"),
    path("tiers/<int:pk>/", views.TiersDetailView.as_view(), name="tiers_detail"),
    path("tiers/<int:pk>/modifier/", views.TiersUpdateView.as_view(), name="tiers_update"),

    path("articles/", views.ArticleListView.as_view(), name="articles"),
    path("articles/nouveau/", views.ArticleCreateView.as_view(), name="article_create"),
    path("articles/<int:pk>/", views.ArticleDetailView.as_view(), name="article_detail"),
    path("articles/<int:pk>/modifier/", views.ArticleUpdateView.as_view(), name="article_update"),
    path("familles/", views.FamilleListView.as_view(), name="familles"),
    path("familles/nouvelle/", views.FamilleCreateView.as_view(), name="famille_create"),
    path("familles/<int:pk>/", views.FamilleUpdateView.as_view(), name="famille_update"),
    path("stock/", views.StockListView.as_view(), name="stock"),
    path("stock/comptabiliser/", views.stock_comptabiliser, name="stock_comptabiliser"),

    path("documents/<str:domaine>/", views.DocumentListView.as_view(), name="documents"),
    path("document/nouveau/<str:type_document>/", views.document_create, name="document_create"),
    path("document/<int:pk>/", views.DocumentDetailView.as_view(), name="document_detail"),
    path("document/<int:pk>/modifier/", views.document_update, name="document_update"),
    path("document/<int:pk>/imprimer/", views.DocumentPrintView.as_view(), name="document_print"),
    path("document/<int:pk>/valider/", views.document_valider, name="document_valider"),
    path("document/<int:pk>/transformer/", views.document_transformer, name="document_transformer"),
    path("document/<int:pk>/annuler/", views.document_annuler, name="document_annuler"),

    path("reglements/", views.ReglementListView.as_view(), name="reglements"),
    path("reglements/nouveau/", views.reglement_create, name="reglement_create"),
    path("reglements/<int:pk>/", views.ReglementDetailView.as_view(), name="reglement_detail"),
]
