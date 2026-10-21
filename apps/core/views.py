from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ExerciceForm, SocieteForm
from .models import Exercice, Societe
from .navigation import MODULES_PAR_CODE


@login_required
def portail(request):
    return render(request, "core/portail.html")


@login_required
def a_propos(request):
    from django import get_version

    from .navigation import VERSION

    return render(request, "core/a_propos.html", {"version": VERSION, "django": get_version()})


@login_required
def accueil_module(request, module):
    """Page d'accueil d'un module : vue d'ensemble de ses onglets et éléments."""
    return render(request, "core/module_accueil.html", {"module_def": MODULES_PAR_CODE[module]})


class SocieteUpdateView(LoginRequiredMixin, UpdateView):
    form_class = SocieteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:societe")
    extra_context = {"titre": "Paramètres de la société"}

    def get_object(self, queryset=None):
        return Societe.get()

    def form_valid(self, form):
        messages.success(self.request, "Paramètres enregistrés.")
        return super().form_valid(form)


class ExerciceListView(LoginRequiredMixin, ListView):
    model = Exercice
    template_name = "core/exercice_list.html"


class ExerciceCreateView(LoginRequiredMixin, CreateView):
    model = Exercice
    form_class = ExerciceForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:exercices")
    extra_context = {"titre": "Nouvel exercice"}


class ExerciceUpdateView(LoginRequiredMixin, UpdateView):
    model = Exercice
    form_class = ExerciceForm
    template_name = "core/form.html"
    success_url = reverse_lazy("comptabilite:exercices")
    extra_context = {"titre": "Modifier l'exercice"}
