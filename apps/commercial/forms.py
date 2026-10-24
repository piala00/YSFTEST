from functools import reduce
from operator import or_

from django import forms
from django.db.models import F, Q
from django.forms import inlineformset_factory

from apps.comptabilite.models import Journal
from apps.core.forms import BootstrapMixin, DateInput

from apps.comptabilite.models import Compte
from apps.core.models import Agence

from .models import (Article, Depot, Document, FamilleArticle, Inventaire, LigneDocument, LigneInventaire, OperationCaisse,
                     Reglement, Tiers)


class TiersForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Tiers
        exclude = ("cree_le",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_tiers = self.data.get("type_tiers") or self.initial.get("type_tiers") or self.instance.type_tiers
        # Payeur : un tiers du même type qui règle lui-même (un seul niveau, comme le compte payeur de Sage)
        self.fields["payeur"].queryset = (Tiers.objects.filter(type_tiers=type_tiers, payeur__isnull=True, actif=True)
                                          .exclude(pk=self.instance.pk))

    def clean(self):
        donnees = super().clean()
        if self.instance.pk or self.errors or self.data.get("confirmer_doublon"):
            return donnees
        candidat = Tiers(type_tiers=donnees.get("type_tiers"), nom=donnees.get("nom") or "")
        doublons = candidat.doublons_possibles()
        if doublons:
            # Même nom : revue manuelle, jamais de refus définitif (deux tiers peuvent porter le même nom)
            self.fields["confirmer_doublon"] = forms.BooleanField(
                required=False, label="Créer quand même ce tiers", widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
            raise forms.ValidationError(
                "Un tiers porte déjà ce nom : " + ", ".join(str(t) for t in doublons)
                + ". Vérifiez qu'il ne s'agit pas du même, puis cochez « Créer quand même ce tiers ».")
        return donnees


class FamilleArticleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = FamilleArticle
        fields = "__all__"


class ArticleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Article
        exclude = ("stock", "cmup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Article de détail : un article simple (qui ne se convertit pas lui-même), autre que celui-ci
        self.fields["article_detail"].queryset = (Article.objects.filter(article_detail__isnull=True, actif=True)
                                                  .exclude(pk=self.instance.pk))


class DepotForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Depot
        fields = "__all__"


class DocumentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ("tiers", "payeur", "date", "date_echeance", "depot", "depot_destination", "reference_externe", "notes")
        widgets = {"date": DateInput(), "date_echeance": DateInput(), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, type_document=None, **kwargs):
        super().__init__(*args, **kwargs)
        doc = self.instance
        doc.type_document = type_document or doc.type_document
        depots = Depot.objects.filter(actif=True)
        self.fields["depot"].queryset = depots
        self.fields["depot_destination"].queryset = depots
        if not doc.depot_id and not self.initial.get("depot"):
            self.initial["depot"] = Depot.par_defaut().pk
        if doc.est_stock:
            del self.fields["tiers"], self.fields["payeur"], self.fields["date_echeance"]
            self.fields["depot"].required = True
            self.fields["depot"].label = "Dépôt d'origine" if doc.est_virement else "Dépôt"
            if doc.est_virement:
                self.fields["depot_destination"].required = True
            else:
                del self.fields["depot_destination"]
        else:
            del self.fields["depot_destination"]
            type_tiers = Tiers.CLIENT if doc.est_vente else Tiers.FOURNISSEUR
            self.fields["tiers"].queryset = Tiers.objects.filter(type_tiers=type_tiers, actif=True)
            self.fields["tiers"].label = "Client" if type_tiers == Tiers.CLIENT else "Fournisseur"
            self.fields["tiers"].required = True
            self.fields["payeur"].queryset = Tiers.objects.filter(type_tiers=type_tiers, payeur__isnull=True, actif=True)
            self.fields["payeur"].empty_label = "Le tiers lui-même (ou le payeur de sa fiche)"
            if not doc.est_facturation:
                del self.fields["date_echeance"]


class LigneDocumentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LigneDocument
        fields = ("article", "designation", "quantite", "prix_unitaire", "remise", "taux_tva")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["article"].queryset = Article.objects.filter(actif=True)
        self.fields["article"].widget.attrs["class"] += " ligne-article"
        for name in ("quantite", "prix_unitaire", "remise", "taux_tva"):
            self.fields[name].widget.attrs["class"] += f" ligne-{name} text-end"

    def clean(self):
        data = super().clean()
        if not data.get("article") and not data.get("designation") and not data.get("DELETE"):
            if self.has_changed():
                raise forms.ValidationError("Choisissez un article ou saisissez une désignation.")
        return data


LigneDocumentFormSet = inlineformset_factory(
    Document, LigneDocument, form=LigneDocumentForm, extra=3, can_delete=True, min_num=1, validate_min=True,
)


def non_soldees(factures):
    """Factures dont le reste dû est positif (total TTC > règlements imputés)."""
    from django.db.models import DecimalField, Sum, Value
    from django.db.models.functions import Coalesce

    return factures.annotate(regle=Coalesce(Sum("imputations__montant"), Value(0), output_field=DecimalField())).filter(
        total_ttc__gt=F("regle"))


class ReglementForm(BootstrapMixin, forms.ModelForm):
    factures = forms.ModelMultipleChoiceField(
        queryset=Document.objects.none(), required=False, label="Factures réglées",
        widget=forms.SelectMultiple(attrs={"size": 6}),
        help_text="Une ou plusieurs factures (Ctrl + clic), réglées de la plus ancienne à la plus récente. "
                  "Si le montant dépasse leur reste dû, l'excédent reste en attente de rattachement à une prochaine facture.")

    en_attente = forms.BooleanField(
        required=False, label="Règlement en attente de facture",
        help_text="Aucune facture à régler : tout le montant attend d'être rattaché à une prochaine facture")

    class Meta:
        model = Reglement
        fields = ("tiers", "date", "mode", "journal", "agence_encaissement", "montant", "reference", "libelle", "commande",
                  "factures", "en_attente")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.models import Agence

        self.fields["journal"].queryset = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)
        self.fields["journal"].required = False
        self.fields["journal"].help_text = "Caisse, banque ou Mobile Money qui reçoit l'argent (inutile si une autre agence a encaissé)"
        self.fields["tiers"].queryset = Tiers.objects.filter(actif=True)
        factures = (Document.objects.filter(type_document__in=(Document.FACTURE, Document.ACHAT_FACTURE), statut=Document.VALIDE)
                    .select_related("tiers").order_by("date", "numero"))
        tiers = self.data.get("tiers") or self.initial.get("tiers")
        tiers = getattr(tiers, "pk", tiers)
        if tiers:                                       # factures du client (ou de ceux dont il est le payeur)
            factures = factures.filter(Q(tiers_id=tiers) | Q(payeur_id=tiers))
        self.fields["factures"].queryset = non_soldees(factures)
        self.fields["factures"].label_from_instance = (
            lambda d: f"{d.numero} du {d.date:%d/%m/%Y} · {d.tiers.nom if d.tiers else ''} · reste dû {d.reste_a_payer:,.0f}".replace(",", " "))
        self.fields["commande"].queryset = (Document.objects.filter(type_document__in=(Document.COMMANDE, Document.ACHAT_COMMANDE))
                                            .exclude(statut=Document.ANNULE).select_related("tiers").order_by("-date"))
        self.fields["commande"].label_from_instance = lambda d: f"{d.numero_affiche} · {d.tiers.nom if d.tiers else ''} · {d.total_ttc:,.0f}".replace(",", " ")
        self.fields["agence_encaissement"].queryset = Agence.objects.filter(actif=True, locale=False)

    def clean(self):
        donnees = super().clean()
        if donnees.get("agence_encaissement"):
            donnees["journal"] = Journal.objects.filter(type_journal=Journal.TYPE_OD).first() or donnees.get("journal")
        elif not donnees.get("journal"):
            self.add_error("journal", "Choisissez la caisse, la banque ou le compte Mobile Money qui reçoit l'argent.")
        return donnees


class RattachementForm(BootstrapMixin, forms.Form):
    facture = forms.ModelChoiceField(queryset=Document.objects.none(), label="Facture à régler")
    montant = forms.DecimalField(max_digits=18, decimal_places=2, required=False, label="Montant",
                                 help_text="Vide : le plus petit du reste du reçu et du reste dû de la facture")

    def __init__(self, reglement, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tiers = reglement.tiers_id
        self.fields["facture"].queryset = non_soldees(Document.objects.filter(type_document=Document.FACTURE, statut=Document.VALIDE)
                                                      .filter(Q(tiers_id=tiers) | Q(payeur_id=tiers)).order_by("date", "numero"))
        self.fields["facture"].label_from_instance = (
            lambda d: f"{d.numero} du {d.date:%d/%m/%Y} · reste dû {d.reste_a_payer:,.0f}".replace(",", " "))


class AgenceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Agence
        fields = ("code", "nom", "ville", "locale", "compte_liaison", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["compte_liaison"].queryset = Compte.objects.filter(numero__startswith="18")


class OperationCaisseForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = OperationCaisse
        fields = ("date", "nature", "journal", "montant", "libelle", "agence", "tiers_libre", "compte", "reference")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["journal"].queryset = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)
        self.fields["agence"].queryset = Agence.objects.filter(actif=True, locale=False)
        self.fields["compte"].queryset = Compte.objects.filter(  # classes 1 à 8 (sans expression régulière : compatible SQL Server)
            reduce(or_, (Q(numero__startswith=str(c)) for c in range(1, 9)))).exclude(numero__startswith="57")


class InventaireForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Inventaire
        fields = ("date", "depot", "famille", "notes")
        widgets = {"date": DateInput(), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["depot"].queryset = Depot.objects.filter(actif=True)
        if not self.initial.get("depot"):
            self.initial["depot"] = Depot.par_defaut().pk


class LigneInventaireForm(forms.ModelForm):
    class Meta:
        model = LigneInventaire
        fields = ("stock_reel",)
        widgets = {"stock_reel": forms.NumberInput(attrs={"class": "form-control form-control-sm text-end saisie-reel", "step": "any"})}


LigneInventaireFormSet = forms.modelformset_factory(LigneInventaire, form=LigneInventaireForm, extra=0)
