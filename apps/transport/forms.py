from decimal import Decimal

from django import forms

from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal
from apps.core.forms import BootstrapMixin, DateInput

from .models_contacts import PersonneGuichet
from .contacts_normalisation import nom_normalise, telephone_normalise

from .models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, ParametresTransport, Vehicule


def _caisses():
    return Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)


class GareForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Gare
        fields = ("code", "nom", "ville", "type_gare", "rattachement", "agence", "caisse", "mobile_money", "actif")

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
        fields = ("ligne", "date", "heure", "vehicule", "vehicule_remplacement", "motif_remplacement", "chauffeur", "convoyeur",
                  "places", "km_depart")
        widgets = {"date": DateInput(), "heure": forms.TimeInput(attrs={"type": "time"}, format="%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ligne"].queryset = Ligne.objects.filter(actif=True)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["chauffeur"].queryset = Chauffeur.objects.filter(actif=True)
        from apps.personnel.models import Employe

        self.fields["convoyeur"].queryset = Employe.objects.filter(actif=True)


class CoordonneesMixin:
    def clean(self):
        donnees = super().clean()
        for selection, nom, telephone in self.groupes_contacts:
            personne = donnees.get(selection)
            if personne is not None and (personne.telephone_normalise != telephone_normalise(donnees.get(telephone))
                                        or personne.nom_normalise != nom_normalise(donnees.get(nom))):
                raise forms.ValidationError("Les coordonnées ont changé : effacez la sélection ou relancez la recherche.")
        return donnees

    def champs(self, noms):
        return [self[n] for n in noms]


class BilletForm(CoordonneesMixin, BootstrapMixin, forms.ModelForm):
    cle_saisie = forms.CharField(required=False, widget=forms.HiddenInput)
    personne = forms.ModelChoiceField(queryset=PersonneGuichet.objects.all(), required=False, widget=forms.HiddenInput)
    groupes_contacts = [("personne", "voyageur", "telephone")]
    mode = forms.ChoiceField(required=False, widget=forms.HiddenInput,
                             choices=[("direct", "Vente habituelle"), ("transit", "Montée intermédiaire"),
                                      ("correspondance", "Avec correspondance")])
    rapides = ("telephone", "voyageur", "piece_identite", "siege", "prix", "paiement")
    complementaires = ("gare_arrivee", "gare_montee", "caisse", "client", "depart_correspondance", "siege_correspondance")

    @property
    def champs_trajet(self):
        return self.champs(self.trajet)

    def clean(self):
        donnees = super().clean()
        depart = donnees.get("depart")
        if depart is not None and donnees.get("mode") == "transit":
            montee = donnees.get("gare_montee")
            if montee is None or montee not in depart.ligne.gares()[1:-1]:
                self.add_error("gare_montee", "Choisissez un arrêt intermédiaire de ce départ.")
        if depart is not None and donnees.get("mode") == "correspondance":
            destination = donnees.get("gare_arrivee")
            if destination is None or destination in depart.ligne.gares():
                self.add_error("gare_arrivee", "Choisissez la destination au-delà du terminus du premier véhicule.")
        return donnees
    bagages_champs = ("bagages", "bagages_nombre", "bagages_poids", "prix_bagages")

    @property
    def champs_rapides(self):
        return self.champs(self.rapides)

    @property
    def champs_complementaires(self):
        return self.champs(self.complementaires)

    @property
    def champs_bagages(self):
        return self.champs(self.bagages_champs)

    @property
    def complements_ouverts(self):
        return self.is_bound and any(self.errors.get(n) for n in self.complementaires)

    @property
    def bagages_ouverts(self):
        return self.is_bound and any(self.errors.get(n) or self[n].value() not in (None, "", 0, "0", "0.0", "0.00")
                                     for n in self.bagages_champs)

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
        programmes = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").select_related("ligne", "vehicule").order_by("date", "heure")
        self.mode_vente = (self.data.get("mode") if self.is_bound else self.initial.get("mode")) or "direct"
        self.trajet = {"transit": ("gare_montee", "gare_arrivee"),
                       "correspondance": ("gare_arrivee", "depart_correspondance", "siege_correspondance")}.get(self.mode_vente, ())
        self.complementaires = tuple(n for n in self.complementaires if n not in self.trajet)
        self.fields["gare_arrivee"].empty_label = "Terminus du départ"
        self.fields["gare_montee"].empty_label = "Origine du départ"
        self.fields["depart_correspondance"].empty_label = "À choisir à la gare de changement"
        self.fields["telephone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "off"})
        self.fields["voyageur"].widget.attrs["autocomplete"] = "off"
        self.fields["depart"].label_from_instance = lambda d: (
            f"{d.numero} — {d.date:%d/%m} {d.heure:%H:%M} — {d.ligne} — {d.vehicule or 'Sans véhicule'}")
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


class ColisForm(CoordonneesMixin, BootstrapMixin, forms.ModelForm):
    cle_saisie = forms.CharField(required=False, widget=forms.HiddenInput)
    personne_expediteur = forms.ModelChoiceField(queryset=PersonneGuichet.objects.all(), required=False, widget=forms.HiddenInput)
    personne_destinataire = forms.ModelChoiceField(queryset=PersonneGuichet.objects.all(), required=False, widget=forms.HiddenInput)
    groupes_contacts = [("personne_expediteur", "expediteur", "tel_expediteur"),
                        ("personne_destinataire", "destinataire", "tel_destinataire")]
    rapides = ("gare_depart", "gare_arrivee", "description", "prix", "port")
    complementaires = ("nombre", "poids", "nature", "valeur_declaree", "contre_remboursement", "client")

    @property
    def champs_rapides(self):
        return self.champs(self.rapides)

    @property
    def champs_complementaires(self):
        return self.champs(self.complementaires)

    @property
    def complements_ouverts(self):
        return self.is_bound and any(self.errors.get(n) for n in self.complementaires)

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
                  "compte_colis_a_transporter", "compte_remboursements", "compte_proprietaires", "compte_carburant", "compte_pieces", "compte_main_oeuvre", "taxe_billets",
                  "taxe_colis", "retenue_annulation", "sessions_caisse_obligatoires", "plafond_depense_sans_autorisation",
                  "avance_depart_toleree")




class TransitDepartForm(BootstrapMixin, forms.Form):
    depart = forms.ModelChoiceField(queryset=Depart.objects.none(), label="Véhicule / départ de cette agence")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["depart"].queryset = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").select_related(
            "ligne", "vehicule").order_by("date", "heure")
        self.fields["depart"].label_from_instance = lambda d: f"{d.numero} — {d.ligne} — {d.vehicule or 'Sans véhicule'}"


class TransitPlacementForm(BootstrapMixin, forms.Form):
    siege = forms.IntegerField(required=False, min_value=1, label="Siège dans ce véhicule")


class TransvasementForm(BootstrapMixin, forms.Form):
    depart = forms.ModelChoiceField(queryset=Depart.objects.none(), label="Voyage interrompu")
    vehicule_secours = forms.ModelChoiceField(queryset=Vehicule.objects.none(), required=False, label="Véhicule de secours",
                                            empty_label="Car loué à un transporteur")
    part_restante = forms.DecimalField(label="Part du trajet restant (%)", min_value=Decimal("0.01"), max_value=100,
                                       max_digits=5, decimal_places=2)
    lieu = forms.CharField(max_length=120, label="Lieu")
    description = forms.CharField(max_length=250, label="Motif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["depart"].queryset = Depart.objects.filter(statut__in=[Depart.PARTI, Depart.ARRIVE], site_origine="").select_related(
            "ligne", "vehicule").order_by("-date", "heure")
        self.fields["vehicule_secours"].queryset = Vehicule.objects.filter(actif=True)
