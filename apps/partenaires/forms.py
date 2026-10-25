from django import forms

from apps.commercial.models import Tiers

from .models import ContratPartenaire


class ContratForm(forms.ModelForm):
    class Meta:
        model = ContratPartenaire
        fields = ["vehicule", "partenaire", "modele", "debut", "fin", "taux_commission", "montant_location", "periodicite",
                  "charge_carburant", "charge_reparations", "charge_equipage", "charge_route", "charge_autres", "notes"]
        widgets = {"debut": forms.DateInput(attrs={"type": "date"}), "fin": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partenaire"].queryset = Tiers.objects.filter(type_tiers=Tiers.FOURNISSEUR).order_by("nom")
        for nom, champ in self.fields.items():
            champ.widget.attrs.setdefault("class", "form-check-input" if isinstance(champ.widget, forms.CheckboxInput)
                                          else "form-select form-select-sm" if isinstance(champ.widget, forms.Select)
                                          else "form-control form-control-sm")
