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
    class Meta:
        model = Societe
        fields = "__all__"
        widgets = {"pied_facture": forms.Textarea(attrs={"rows": 3})}


class ExerciceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ("code", "date_debut", "date_fin")  # la clôture passe par Traitement > Fin d'exercice
        widgets = {"date_debut": DateInput(), "date_fin": DateInput()}
