import datetime

from django import forms
from django.forms import inlineformset_factory

from apps.core.forms import BootstrapMixin, DateInput
from apps.core.models import Exercice

from .models import Compte, Ecriture, Journal, LigneEcriture


class CompteForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Compte
        fields = "__all__"


class JournalForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Journal
        fields = "__all__"


class EcritureForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Ecriture
        fields = ("journal", "date", "libelle", "reference")
        widgets = {"date": DateInput()}


class LigneEcritureForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LigneEcriture
        fields = ("compte", "tiers", "libelle", "debit", "credit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["compte"].queryset = Compte.objects.filter(actif=True)
        for name in ("debit", "credit"):
            self.fields[name].widget.attrs["class"] += f" ligne-{name} text-end"
            self.fields[name].required = False

    def clean(self):
        data = super().clean()
        data["debit"] = data.get("debit") or 0
        data["credit"] = data.get("credit") or 0
        return data


LigneEcritureFormSet = inlineformset_factory(
    Ecriture, LigneEcriture, form=LigneEcritureForm, extra=4, can_delete=True, min_num=2, validate_min=True,
)


class PeriodeForm(BootstrapMixin, forms.Form):
    date_debut = forms.DateField(label="Du", widget=DateInput())
    date_fin = forms.DateField(label="Au", widget=DateInput())
    compte_debut = forms.CharField(label="Compte de", required=False, max_length=20)
    compte_fin = forms.CharField(label="à", required=False, max_length=20)

    @classmethod
    def depuis_requete(cls, request, avec_comptes=True):
        exercice = Exercice.courant()
        today = datetime.date.today()
        initial = {
            "date_debut": exercice.date_debut if exercice else today.replace(month=1, day=1),
            "date_fin": exercice.date_fin if exercice else today,
        }
        data = request.GET.copy()
        for key, value in initial.items():
            data.setdefault(key, value.isoformat())
        form = cls(data)
        if not avec_comptes:
            del form.fields["compte_debut"], form.fields["compte_fin"]
        form.is_valid()
        cd = form.cleaned_data
        cd.setdefault("date_debut", initial["date_debut"])
        cd.setdefault("date_fin", initial["date_fin"])
        return form, cd
