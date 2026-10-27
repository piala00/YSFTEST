from django.urls import path

from . import views

app_name = "partenaires"

urlpatterns = [
    path("", views.contrats, name="contrats"),
    path("decomptes/", views.decomptes, name="decomptes"),
    path("proprietaires/", views.proprietaires, name="proprietaires"),
    path("releves/", views.releve, name="releves"),
    path("releves/<int:pk>/", views.releve, name="releve"),
]
