from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("societe/", views.SocieteUpdateView.as_view(), name="societe"),
    path("exercices/", views.ExerciceListView.as_view(), name="exercices"),
    path("exercices/nouveau/", views.ExerciceCreateView.as_view(), name="exercice_create"),
    path("exercices/<int:pk>/", views.ExerciceUpdateView.as_view(), name="exercice_update"),
]
