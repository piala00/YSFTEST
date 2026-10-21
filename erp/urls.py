from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="reporting:dashboard", permanent=False)),
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("parametres/", include("apps.core.urls")),
    path("commercial/", include("apps.commercial.urls")),
    path("comptabilite/", include("apps.comptabilite.urls")),
    path("reporting/", include("apps.reporting.urls")),
    path("api/", include("apps.api.urls")),
]
