from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ExerciceForm, SocieteForm
from .models import Exercice, Societe


class SocieteUpdateView(LoginRequiredMixin, UpdateView):
    form_class = SocieteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("core:societe")
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
    success_url = reverse_lazy("core:exercices")
    extra_context = {"titre": "Nouvel exercice"}


class ExerciceUpdateView(LoginRequiredMixin, UpdateView):
    model = Exercice
    form_class = ExerciceForm
    template_name = "core/form.html"
    success_url = reverse_lazy("core:exercices")
    extra_context = {"titre": "Modifier l'exercice"}
