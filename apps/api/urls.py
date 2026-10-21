from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("tiers", views.TiersViewSet, basename="tiers")
router.register("articles", views.ArticleViewSet)
router.register("documents", views.DocumentViewSet, basename="documents")
router.register("reglements", views.ReglementViewSet)
router.register("comptes", views.CompteViewSet)
router.register("journaux", views.JournalViewSet)
router.register("ecritures", views.EcritureViewSet)

urlpatterns = [
    path("token/", obtain_auth_token, name="api_token"),
    path("reporting/dashboard/", views.dashboard),
    path("reporting/balance/", views.balance),
    path("reporting/bilan/", views.bilan),
    path("reporting/compte-resultat/", views.compte_resultat),
    path("reporting/balance-agee/", views.balance_agee),
    path("", include(router.urls)),
]
