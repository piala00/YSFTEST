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
    arrets = forms.CharField(
        label="Arrêts intermédiaires", required=False,
        help_text="Codes des gares desservies en route, dans l'ordre, séparés par des virgules (ex. EDE, PKL). Un voyageur "
                  "peut y monter ou en descendre ; son siège est revendu pour la suite du trajet. Le prix entre deux gares "
                  "vient de la ligne-tarif qui les relie (sinon il est saisi à la vente).")

    class Meta:
        model = Ligne
        fields = ("code", "gare_depart", "gare_arrivee", "arrets", "distance_km", "duree", "prix_billet", "colis_forfait",
                  "colis_prix_kg", "gamme", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["arrets"] = ", ".join(a.gare.code for a in self.instance.arrets.select_related("gare"))

    def clean_arrets(self):
        codes = [c.strip().upper() for c in self.cleaned_data["arrets"].replace(";", ",").split(",") if c.strip()]
        gares = []
        for code in codes:
            g = Gare.objects.filter(code__iexact=code).first()
            if g is None:
                raise forms.ValidationError(f"Gare « {code} » inconnue.")
            if g in gares:
                raise forms.ValidationError(f"Gare « {code} » en double.")
            gares.append(g)
        return gares

    def clean(self):
        donnees = super().clean()
        extremites = {donnees.get("gare_depart"), donnees.get("gare_arrivee")}
        if any(g in extremites for g in donnees.get("arrets") or []):
            self.add_error("arrets", "Un arrêt ne peut pas être la gare de départ ou d'arrivée.")
        return donnees

    def save(self, commit=True):
        from apps.echanges.publication import publier_objet

        from .models import ArretLigne

        ligne = super().save(commit=True)
        gares = self.cleaned_data.get("arrets") or []
        ligne.arrets.exclude(gare__in=gares).delete()
        for ordre, g in enumerate(gares, 1):
            ArretLigne.objects.update_or_create(ligne=ligne, gare=g, defaults={"ordre": ordre})
        publier_objet(ligne)                                # les agences reçoivent la ligne avec ses arrêts
        return ligne


class VehiculeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ("immatriculation", "designation", "type_vehicule", "gamme", "nombre_places", "proprietaire", "carte_grise",
                  "mise_en_service", "assurance_echeance", "visite_technique_echeance", "actif")
        widgets = {"mise_en_service": DateInput(), "assurance_echeance": DateInput(), "visite_technique_echeance": DateInput()}


class ChauffeurForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Chauffeur
        fields = ("nom", "telephone", "permis", "actif")


class DepartForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Depart
        fields = ("ligne", "date", "heure", "vehicule", "chauffeur", "convoyeur", "places", "km_depart")
        widgets = {"date": DateInput(), "heure": forms.TimeInput(attrs={"type": "time"}, format="%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ligne"].queryset = Ligne.objects.filter(actif=True)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["chauffeur"].queryset = Chauffeur.objects.filter(actif=True)
        from apps.personnel.models import Employe

        self.fields["convoyeur"].queryset = Employe.objects.filter(actif=True)


class BilletForm(BootstrapMixin, forms.ModelForm):
    depart_correspondance = forms.ModelChoiceField(
        queryset=Depart.objects.none(), required=False, label="Départ de correspondance",
        help_text="Si la destination est au-delà du terminus : véhicule pris à la gare de changement (vide : choisi sur place)")
    siege_correspondance = forms.IntegerField(required=False, min_value=1, label="Siège dans la correspondance")

    class Meta:
        model = Billet
        fields = ("depart", "gare_montee", "gare_arrivee", "voyageur", "telephone", "piece_identite", "siege", "prix", "paiement", "caisse",
                  "client", "bagages", "bagages_nombre", "bagages_poids", "prix_bagages")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        programmes = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").select_related("ligne").order_by("date", "heure")
        self.fields["depart"].queryset = programmes
        self.fields["depart_correspondance"].queryset = programmes
        self.fields["gare_arrivee"].queryset = Gare.objects.filter(actif=True)
        self.fields["gare_montee"].queryset = Gare.objects.filter(actif=True)
        self.fields["caisse"].queryset = _caisses()
        self.fields["caisse"].help_text = "Vide : caisse de la gare"
        self.fields["client"].queryset = Tiers.objects.filter(type_tiers=Tiers.CLIENT, actif=True)
        for champ in ("bagages_nombre", "bagages_poids", "prix_bagages"):    # pas de bagage : laisser vide
            self.fields[champ].required = False

    def clean_bagages_nombre(self):
        return self.cleaned_data.get("bagages_nombre") or 0

    def clean_bagages_poids(self):
        return self.cleaned_data.get("bagages_poids") or 0

    def clean_prix_bagages(self):
        return self.cleaned_data.get("prix_bagages") or 0


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
        fields = ("compte_billets", "compte_colis", "compte_bagages", "compte_fret", "compte_contre_remboursement", "compte_billets_a_voyager",
                  "compte_colis_a_transporter", "compte_remboursements", "compte_carburant", "compte_pieces", "compte_main_oeuvre", "taxe_billets",
                  "taxe_colis", "retenue_annulation", "sessions_caisse_obligatoires")
