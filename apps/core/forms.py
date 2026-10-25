from django import forms

from .models import Exercice, Societe


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select form-select-sm")
            else:
                widget.attrs.setdefault("class", "form-control form-control-sm")


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class SocieteForm(BootstrapMixin, forms.ModelForm):
    depots_detail = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=forms.CheckboxSelectMultiple, label="Dépôts de vente au détail (boutiques)",
        help_text="Un ou deux dépôts où l'on vend au détail ; les autres magasins les approvisionnent par transfert")

    class Meta:
        model = Societe
        fields = "__all__"
        widgets = {"pied_facture": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.commercial.models import Depot

        self.fields["depots_detail"].queryset = Depot.objects.filter(actif=True)
        self.fields["depots_detail"].initial = Depot.objects.filter(vente_detail=True)
        self.fields["depots_detail"].widget.attrs.pop("class", None)
        ordre = [n for n in self.fields if n != "depots_detail"]          # la liste des boutiques juste après l'option
        ordre.insert(ordre.index("separation_gros_detail") + 1, "depots_detail")
        self.order_fields(ordre)
        self.fields["activite"].required = False                   # absent du formulaire envoyé : activité inchangée

    def clean_activite(self):
        return self.cleaned_data.get("activite") or self.instance.activite or Societe.ACTIVITE_COMMERCE

    def clean(self):
        donnees = super().clean()
        if donnees.get("separation_gros_detail") and not donnees.get("depots_detail"):
            self.add_error("depots_detail", "Désignez au moins un dépôt de vente au détail.")
        return donnees

    def save(self, commit=True):
        from apps.commercial.models import Depot

        societe = super().save(commit)
        if "depots_detail" in self.cleaned_data:
            choisis = [d.pk for d in self.cleaned_data["depots_detail"]]
            Depot.objects.filter(pk__in=choisis).update(vente_detail=True)
            Depot.objects.exclude(pk__in=choisis).update(vente_detail=False)
        return societe


class ExerciceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ("code", "date_debut", "date_fin")  # la clôture passe par Traitement > Fin d'exercice
        widgets = {"date_debut": DateInput(), "date_fin": DateInput()}
