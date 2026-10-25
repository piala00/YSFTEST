from django import forms

from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal
from apps.core.forms import BootstrapMixin, DateInput

from .models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, ParametresTransport, Vehicule


def _caisses():
    return Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)


class GareForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Gare
        fields = ("code", "nom", "ville", "agence", "caisse", "mobile_money", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["caisse"].queryset = _caisses()
        self.fields["mobile_money"].queryset = _caisses()


class LigneForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Ligne
        fields = ("code", "gare_depart", "gare_arrivee", "distance_km", "duree", "prix_billet", "colis_forfait", "colis_prix_kg", "actif")


class VehiculeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ("immatriculation", "designation", "type_vehicule", "nombre_places", "proprietaire", "carte_grise",
                  "mise_en_service", "assurance_echeance", "visite_technique_echeance", "actif")
        widgets = {"mise_en_service": DateInput(), "assurance_echeance": DateInput(), "visite_technique_echeance": DateInput()}


class ChauffeurForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Chauffeur
        fields = ("nom", "telephone", "permis", "actif")


class DepartForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Depart
        fields = ("ligne", "date", "heure", "vehicule", "chauffeur", "places")
        widgets = {"date": DateInput(), "heure": forms.TimeInput(attrs={"type": "time"}, format="%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ligne"].queryset = Ligne.objects.filter(actif=True)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["chauffeur"].queryset = Chauffeur.objects.filter(actif=True)


class BilletForm(BootstrapMixin, forms.ModelForm):
    depart_correspondance = forms.ModelChoiceField(
        queryset=Depart.objects.none(), required=False, label="Départ de correspondance",
        help_text="Si la destination est au-delà du terminus : véhicule pris à la gare de changement (vide : choisi sur place)")
    siege_correspondance = forms.IntegerField(required=False, min_value=1, label="Siège dans la correspondance")

    class Meta:
        model = Billet
        fields = ("depart", "gare_arrivee", "voyageur", "telephone", "piece_identite", "siege", "prix", "paiement", "caisse",
                  "client")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        programmes = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").select_related("ligne").order_by("date", "heure")
        self.fields["depart"].queryset = programmes
        self.fields["depart_correspondance"].queryset = programmes
        self.fields["gare_arrivee"].queryset = Gare.objects.filter(actif=True)
        self.fields["caisse"].queryset = _caisses()
        self.fields["caisse"].help_text = "Vide : caisse de la gare"
        self.fields["client"].queryset = Tiers.objects.filter(type_tiers=Tiers.CLIENT, actif=True)


class ColisForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Colis
        fields = ("nature", "gare_depart", "gare_arrivee", "expediteur", "tel_expediteur", "destinataire", "tel_destinataire",
                  "description", "nombre", "poids", "valeur_declaree", "prix", "port", "contre_remboursement", "client")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for champ in ("gare_depart", "gare_arrivee"):
            self.fields[champ].queryset = Gare.objects.filter(actif=True)
        self.fields["client"].queryset = Tiers.objects.filter(type_tiers=Tiers.CLIENT, actif=True)


class DepenseVehiculeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = DepenseVehicule
        fields = ("date", "vehicule", "depart", "nature", "libelle", "montant", "caisse", "compte", "reference")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["depart"].queryset = Depart.objects.exclude(statut=Depart.ANNULE).select_related("ligne")
        self.fields["caisse"].queryset = _caisses()
        self.fields["compte"].queryset = Compte.objects.filter(numero__startswith="6")


class ParametresTransportForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ParametresTransport
        fields = ("compte_billets", "compte_colis", "compte_fret", "compte_contre_remboursement", "taxe_billets", "taxe_colis",
                  "retenue_annulation")
