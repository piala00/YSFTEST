from django.urls import path

from . import views

app_name = "relais"

urlpatterns = [
    path("v1/boites/<str:code>/", views.boite, name="boite"),
    path("v1/boites/<str:code>/<str:nom>", views.lot, name="lot"),
]
