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
    """Page d'accueil d'un logiciel : raccourcis, indicateurs et dernières pièces (les menus restent en haut)."""
    from .accueil import PAGES

    from . import droits as d

    contexte = PAGES[module]()
    droits = d.Droits(request.user, MODULES_PAR_CODE[module])
    if not droits.total and droits.reglages:
        # Raccourcis et indicateurs limités à ce que le profil peut ouvrir
        contexte["raccourcis"] = [{**g, "liens": [l for l in g["liens"] if d.url_permise(droits, l["url"])]}
                                  for g in contexte["raccourcis"]]
        contexte["raccourcis"] = [g for g in contexte["raccourcis"] if g["liens"]]
        contexte["indicateurs"] = [i for i in contexte["indicateurs"] if not i["url"] or d.url_permise(droits, i["url"])]
    return render(request, "core/module_accueil.html", {"module_def": MODULES_PAR_CODE[module], **contexte})


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


# ---------------------------------------------------------------------------
# Fichier › Autorisations d'accès
# ---------------------------------------------------------------------------
@login_required
def autorisations(request, module):
    """Profils, utilisateurs et droits par menu (réservé à l'administrateur)."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.shortcuts import redirect

    from . import droits as d
    from .models import DroitAcces

    if not request.user.is_superuser:
        return render(request, "core/acces_refuse.html", {
            "chemin": "Fichier › Autorisations d'accès", "operation": "gérer les autorisations",
            "niveau": "réservé à l'administrateur", "profil": d.profil_de(request.user) or "sans profil"}, status=403)
    User = get_user_model()
    logiciel = MODULES_PAR_CODE.get(request.GET.get("logiciel") or request.POST.get("logiciel") or module, MODULES_PAR_CODE[module])
    profil = Group.objects.filter(pk=request.GET.get("profil") or request.POST.get("profil")).first()
    url = f"{request.path}?logiciel={logiciel.code}"

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profil_creer" and request.POST.get("nom", "").strip():
            profil, _ = Group.objects.get_or_create(name=request.POST["nom"].strip()[:150])
            messages.success(request, f"Profil « {profil} » créé : réglez ses droits ci-dessous.")
        elif action == "profil_supprimer" and profil:
            if profil.user_set.exists():
                messages.error(request, f"Le profil « {profil} » a encore des utilisateurs : changez-les de profil d'abord.")
            else:
                messages.success(request, f"Profil « {profil} » supprimé.")
                profil.delete()
                profil = None
        elif action == "utilisateur":
            nom = request.POST.get("nom_utilisateur", "").strip()
            cible = Group.objects.filter(pk=request.POST.get("profil_utilisateur")).first()
            utilisateur = User.objects.filter(username=nom).first()
            if not nom:
                messages.error(request, "Indiquez le nom de l'utilisateur.")
            elif utilisateur is None and not request.POST.get("mot_de_passe"):
                messages.error(request, "Nouvel utilisateur : indiquez un mot de passe.")
            else:
                if utilisateur is None:
                    utilisateur = User.objects.create_user(nom, "", request.POST["mot_de_passe"])
                elif request.POST.get("mot_de_passe"):
                    utilisateur.set_password(request.POST["mot_de_passe"])
                    utilisateur.save()
                if utilisateur.is_superuser:
                    messages.warning(request, f"{utilisateur} est administrateur : il garde tous les droits.")
                utilisateur.groups.set([cible] if cible else [])
                messages.success(request, f"Utilisateur « {utilisateur} » : profil {cible or 'aucun (tous les droits)'}.")
        elif action == "droits" and profil:
            _, parents = d.arbre(logiciel)
            existants = {r.code: r for r in DroitAcces.objects.filter(groupe=profil, module=logiciel.code)}
            for code in [o.code for o in logiciel.onglets] + list(parents):
                valeur = request.POST.get(f"droit_{code}", "")
                if valeur in d.LIBELLES:
                    DroitAcces.objects.update_or_create(groupe=profil, module=logiciel.code, code=code, defaults={"niveau": valeur})
                elif code in existants:
                    existants[code].delete()
            messages.success(request, f"Droits du profil « {profil} » dans {logiciel.titre} enregistrés.")
        return redirect(url + (f"&profil={profil.pk}" if profil else ""))

    lignes = []
    if profil:
        droits = d.Droits(request.user, logiciel)
        droits.total, droits.profil = False, profil
        droits.reglages = dict(DroitAcces.objects.filter(groupe=profil, module=logiciel.code).values_list("code", "niveau"))
        onglets, parents = d.arbre(logiciel)
        droits._parents = parents
        for onglet, elements in onglets:
            enfants = {e.code for e, _ in elements if parents.get(e.code) == onglet.code}
            lignes.append({"code": onglet.code, "parent": "", "titre": onglet.titre, "profondeur": 0, "a_enfants": bool(enfants),
                           "reglage": droits.reglages.get(onglet.code, ""), "effectif": d.LIBELLES[droits.niveau(onglet.code)]})
            for el, profondeur in elements:
                lignes.append({"code": el.code, "parent": parents[el.code], "titre": el.titre, "profondeur": profondeur,
                               "a_enfants": bool(el.tous_enfants()), "reglage": droits.reglages.get(el.code, ""),
                               "effectif": d.LIBELLES[droits.niveau(parents[el.code])]})
    return render(request, "core/autorisations.html", {
        "profils": Group.objects.order_by("name"), "profil": profil, "logiciel": logiciel, "logiciels": MODULES_PAR_CODE.values(),
        "utilisateurs": User.objects.order_by("username").prefetch_related("groups"), "lignes": lignes, "niveaux": d.NIVEAUX,
    })
