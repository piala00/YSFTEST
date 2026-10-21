from django import forms
from django.forms import inlineformset_factory

from apps.comptabilite.models import Journal
from apps.core.forms import BootstrapMixin, DateInput

from .models import Article, Depot, Document, FamilleArticle, Inventaire, LigneDocument, LigneInventaire, Reglement, Tiers


class TiersForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Tiers
        exclude = ("cree_le",)


class FamilleArticleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = FamilleArticle
        fields = "__all__"


class ArticleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Article
        exclude = ("stock", "cmup")


class DepotForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Depot
        fields = "__all__"


class DocumentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ("tiers", "date", "date_echeance", "depot", "depot_destination", "reference_externe", "notes")
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
            del self.fields["tiers"], self.fields["date_echeance"]
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


class ReglementForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Reglement
        fields = ("tiers", "date", "mode", "journal", "montant", "reference", "libelle")
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["journal"].queryset = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE)
        self.fields["tiers"].queryset = Tiers.objects.filter(actif=True)


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
