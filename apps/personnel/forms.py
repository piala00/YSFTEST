from django import forms

from apps.comptabilite.models import Compte, Journal
from apps.core.forms import BootstrapMixin, DateInput
from apps.transport.models import Chauffeur, Vehicule

from .models import Avance, Employe, RubriquePaie


class EmployeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Employe
        fields = ("matricule", "nom", "telephone", "poste", "service", "agence", "vehicule", "chauffeur", "salaire_base",
                  "date_embauche", "numero_cnps", "mode_paiement", "actif")
        widgets = {"date_embauche": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["chauffeur"].queryset = Chauffeur.objects.filter(actif=True)


class RubriqueForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = RubriquePaie
        fields = ("code", "libelle", "nature", "calcul", "valeur", "plafond", "compte", "compte_contrepartie", "automatique", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        comptes = Compte.objects.filter(actif=True)
        self.fields["compte"].queryset = comptes
        self.fields["compte_contrepartie"].queryset = comptes


class AvanceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Avance
        fields = ("employe", "date", "montant", "caisse", "motif")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employe"].queryset = Employe.objects.filter(actif=True)
        self.fields["caisse"].queryset = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)
