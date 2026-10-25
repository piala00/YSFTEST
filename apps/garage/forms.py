from django import forms

from apps.commercial.models import Tiers
from apps.comptabilite.models import Journal
from apps.core.forms import BootstrapMixin, DateInput
from apps.transport.models import Depart, Vehicule

from .models import LigneReparation, OrdreReparation, PleinCarburant


class PleinForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = PleinCarburant
        fields = ("date", "vehicule", "litres", "prix_litre", "montant", "kilometrage", "station", "depart", "paiement", "caisse",
                  "fournisseur")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["depart"].queryset = Depart.objects.exclude(statut=Depart.ANNULE).select_related("ligne")[:200]
        self.fields["caisse"].queryset = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)
        self.fields["fournisseur"].queryset = Tiers.objects.filter(type_tiers=Tiers.FOURNISSEUR, actif=True)
        self.fields["montant"].required = False


class OrdreForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = OrdreReparation
        fields = ("vehicule", "date_entree", "kilometrage", "panne", "intervenant")
        widgets = {"date_entree": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)


class LigneReparationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LigneReparation
        fields = ("nature", "designation", "quantite", "prix_unitaire", "paiement", "fournisseur")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fournisseur"].queryset = Tiers.objects.filter(type_tiers=Tiers.FOURNISSEUR, actif=True)
