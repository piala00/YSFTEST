from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.core.urls_communes import urls_communes

urlpatterns = [
    path("", include("apps.core.urls")),
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("commercial/", include("apps.commercial.urls")),
    path("comptabilite/", include("apps.comptabilite.urls")),
    path("reporting/", include("apps.reporting.urls")),
    # Logiciels des services du transport : leurs pages communes, puis les écrans (espace de noms « transport »)
    path("transport/billetterie/", include((urls_communes("billetterie"), "billetterie"))),
    path("transport/colis/", include((urls_communes("colis"), "colis"))),
    path("transport/garage/", include("apps.garage.urls")),
    path("transport/partenaires/", include("apps.partenaires.urls")),
    path("transport/", include("apps.transport.urls")),
    path("personnel/", include("apps.personnel.urls")),
    path("api/", include("apps.api.urls")),
]
