from django import forms
from django.forms import inlineformset_factory

from apps.comptabilite.models import Journal
from apps.core.forms import BootstrapMixin, DateInput

from .models import Article, Document, FamilleArticle, LigneDocument, Reglement, Tiers


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
        exclude = ("stock",)


class DocumentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ("tiers", "date", "date_echeance", "reference_externe", "notes")
        widgets = {"date": DateInput(), "date_echeance": DateInput(), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, type_document=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.type_document = type_document or self.instance.type_document
        type_tiers = Tiers.CLIENT if self.instance.type_document in Document.TYPES_VENTE else Tiers.FOURNISSEUR
        self.fields["tiers"].queryset = Tiers.objects.filter(type_tiers=type_tiers, actif=True)
        self.fields["tiers"].label = "Client" if type_tiers == Tiers.CLIENT else "Fournisseur"


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
