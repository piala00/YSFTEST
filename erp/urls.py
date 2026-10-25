from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("commercial/", include("apps.commercial.urls")),
    path("comptabilite/", include("apps.comptabilite.urls")),
    path("reporting/", include("apps.reporting.urls")),
    path("transport/", include("apps.transport.urls")),
    path("api/", include("apps.api.urls")),
]
