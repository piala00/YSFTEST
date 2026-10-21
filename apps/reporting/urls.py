from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ventes/", views.ventes, name="ventes"),
    path("balance-agee/", views.balance_agee, name="balance_agee"),
]
