from django import forms

from apps.commercial.models import Tiers

from .models import ContratPartenaire


class ContratForm(forms.ModelForm):
    class Meta:
        model = ContratPartenaire
        fields = ["vehicule", "partenaire", "modele", "debut", "fin", "taux_commission", "montant_location", "periodicite",
                  "taux_proprietaire", "plancher_zero",
                  "charge_carburant", "charge_reparations", "charge_equipage", "charge_route", "charge_autres", "notes"]
        widgets = {"debut": forms.DateInput(attrs={"type": "date"}), "fin": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partenaire"].queryset = Tiers.objects.filter(actif=True).order_by("nom")     # son compte propriétaire est à part
        self.fields["partenaire"].help_text = ("Le propriétaire : ses droits et paiements vont sur le compte des propriétaires "
                                               "(467), séparé de son éventuel compte fournisseur")
        for nom in ("taux_proprietaire", "montant_location", "taux_commission"):     # selon le modèle choisi
            self.fields[nom].required = False
        for nom, champ in self.fields.items():
            champ.widget.attrs.setdefault("class", "form-check-input" if isinstance(champ.widget, forms.CheckboxInput)
                                          else "form-select form-select-sm" if isinstance(champ.widget, forms.Select)
                                          else "form-control form-control-sm")

    def _zero(self, nom):
        return self.cleaned_data.get(nom) or 0

    def clean_taux_proprietaire(self):
        return self._zero("taux_proprietaire")

    def clean_montant_location(self):
        return self._zero("montant_location")

    def clean_taux_commission(self):
        return self._zero("taux_commission")
