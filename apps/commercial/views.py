from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.comptabilite.models import Journal

from .forms import ArticleForm, DocumentForm, FamilleArticleForm, LigneDocumentFormSet, ReglementForm, TiersForm
from .models import Article, Document, FamilleArticle, MouvementStock, Reglement, Tiers


def _erreur(request, exc):
    for msg in getattr(exc, "messages", [str(exc)]):
        messages.error(request, msg)


# ---------------------------------------------------------------- Tiers
class TiersListView(LoginRequiredMixin, ListView):
    model = Tiers
    template_name = "commercial/tiers_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = Tiers.objects.select_related("compte_collectif")
        self.type_tiers = self.kwargs.get("type_tiers", Tiers.CLIENT)
        qs = qs.filter(type_tiers=self.type_tiers)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(nom__icontains=q) | Q(ville__icontains=q) | Q(telephone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["type_tiers"] = self.type_tiers
        ctx["titre"] = "Clients" if self.type_tiers == Tiers.CLIENT else "Fournisseurs"
        return ctx


class TiersCreateView(LoginRequiredMixin, CreateView):
    model = Tiers
    form_class = TiersForm
    template_name = "core/form.html"
    extra_context = {"titre": "Nouveau tiers"}

    def get_initial(self):
        type_tiers = self.request.GET.get("type", Tiers.CLIENT)
        prefixe = "C" if type_tiers == Tiers.CLIENT else "F"
        n = Tiers.objects.filter(type_tiers=type_tiers).count() + 1
        return {"type_tiers": type_tiers, "code": f"{prefixe}{n:04d}"}

    def get_success_url(self):
        return reverse("commercial:tiers_detail", args=[self.object.pk])


class TiersUpdateView(LoginRequiredMixin, UpdateView):
    model = Tiers
    form_class = TiersForm
    template_name = "core/form.html"
    extra_context = {"titre": "Modifier le tiers"}

    def get_success_url(self):
        return reverse("commercial:tiers_detail", args=[self.object.pk])


class TiersDetailView(LoginRequiredMixin, DetailView):
    model = Tiers
    template_name = "commercial/tiers_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["documents"] = self.object.documents.exclude(statut=Document.ANNULE)[:30]
        ctx["reglements"] = self.object.reglements.all()[:30]
        ctx["solde"] = self.object.solde_comptable()
        ctx["encours"] = self.object.encours()
        return ctx


# ---------------------------------------------------------------- Articles
class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "commercial/article_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = Article.objects.select_related("famille")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(reference__icontains=q) | Q(designation__icontains=q))
        if self.request.GET.get("alerte"):
            qs = [a for a in qs if a.en_alerte]
        return qs


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:articles")
    extra_context = {"titre": "Nouvel article"}


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "core/form.html"
    extra_context = {"titre": "Modifier l'article"}

    def get_success_url(self):
        return reverse("commercial:article_detail", args=[self.object.pk])


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = "commercial/article_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mouvements"] = self.object.mouvements.select_related("document")[:100]
        return ctx


class FamilleListView(LoginRequiredMixin, ListView):
    model = FamilleArticle
    template_name = "commercial/famille_list.html"


class FamilleCreateView(LoginRequiredMixin, CreateView):
    model = FamilleArticle
    form_class = FamilleArticleForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:familles")
    extra_context = {"titre": "Nouvelle famille d'articles"}


class FamilleUpdateView(LoginRequiredMixin, UpdateView):
    model = FamilleArticle
    form_class = FamilleArticleForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:familles")
    extra_context = {"titre": "Modifier la famille"}


class StockListView(LoginRequiredMixin, ListView):
    template_name = "commercial/stock.html"

    def get_queryset(self):
        return Article.objects.filter(suivi_stock=True, actif=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["valeur_totale"] = sum(a.valeur_stock for a in ctx["object_list"])
        ctx["mouvements"] = MouvementStock.objects.select_related("article", "document")[:50]
        return ctx


@login_required
@require_POST
def stock_comptabiliser(request):
    from django.utils import timezone

    from apps.comptabilite.services import constater_variation_stock

    try:
        ecriture = constater_variation_stock(timezone.localdate())
        messages.success(request, f"Variation de stock comptabilisée (pièce {ecriture.numero}).")
    except ValidationError as exc:
        _erreur(request, exc)
    return redirect("commercial:stock")


# ---------------------------------------------------------------- Documents
class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "commercial/document_list.html"
    paginate_by = 50

    def get_queryset(self):
        self.domaine = self.kwargs["domaine"]
        types = Document.TYPES_VENTE if self.domaine == "ventes" else Document.TYPES_ACHAT
        qs = Document.objects.filter(type_document__in=types).select_related("tiers")
        self.type_document = self.request.GET.get("type", "")
        if self.type_document:
            qs = qs.filter(type_document=self.type_document)
        statut = self.request.GET.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(tiers__nom__icontains=q) | Q(reference_externe__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        types = Document.TYPES_VENTE if self.domaine == "ventes" else Document.TYPES_ACHAT
        libelles = dict(Document.TYPES)
        ctx.update(domaine=self.domaine, types=[(t, libelles[t]) for t in types],
                   type_document=self.type_document, statuts=Document.STATUTS)
        return ctx


def _articles_json():
    return {
        a.pk: {"designation": a.designation, "prix_vente": float(a.prix_vente),
               "prix_achat": float(a.prix_achat), "taux_tva": float(a.taux_tva)}
        for a in Article.objects.filter(actif=True)
    }


def _document_form(request, document, type_document):
    est_vente = type_document in Document.TYPES_VENTE
    if request.method == "POST":
        form = DocumentForm(request.POST, instance=document, type_document=type_document)
        formset = LigneDocumentFormSet(request.POST, instance=document)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                doc = form.save(commit=False)
                if not doc.pk:
                    doc.cree_par = request.user
                doc.save()
                formset.instance = doc
                formset.save()
                doc.recalculer()
                if "valider" in request.POST:
                    try:
                        doc.valider()
                        messages.success(request, f"Document {doc.numero} validé.")
                    except ValidationError as exc:
                        _erreur(request, exc)
                else:
                    messages.success(request, "Brouillon enregistré.")
            return redirect("commercial:document_detail", pk=doc.pk)
    else:
        form = DocumentForm(instance=document, type_document=type_document)
        formset = LigneDocumentFormSet(instance=document)
    return render(request, "commercial/document_form.html", {
        "form": form, "formset": formset, "document": document,
        "titre": dict(Document.TYPES)[type_document], "est_vente": est_vente,
        "articles_json": _articles_json(),
    })


@login_required
def document_create(request, type_document):
    if type_document not in dict(Document.TYPES):
        raise Http404
    document = Document(type_document=type_document)
    tiers_id = request.GET.get("tiers")
    if tiers_id:
        document.tiers_id = tiers_id
    return _document_form(request, document, type_document)


@login_required
def document_update(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not document.modifiable:
        messages.warning(request, "Ce document est validé et ne peut plus être modifié.")
        return redirect("commercial:document_detail", pk=pk)
    return _document_form(request, document, document.type_document)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = "commercial/document_detail.html"

    def get_queryset(self):
        return Document.objects.select_related("tiers", "origine", "ecriture")


class DocumentPrintView(DocumentDetailView):
    template_name = "commercial/document_print.html"


@login_required
@require_POST
def document_valider(request, pk):
    document = get_object_or_404(Document, pk=pk)
    try:
        document.valider()
        messages.success(request, f"Document {document.numero} validé.")
    except ValidationError as exc:
        _erreur(request, exc)
    return redirect("commercial:document_detail", pk=pk)


@login_required
@require_POST
def document_transformer(request, pk):
    document = get_object_or_404(Document, pk=pk)
    try:
        nouveau = document.transformer(request.POST["type_cible"], request.user)
        messages.success(request, f"{nouveau.get_type_document_display()} créé(e) en brouillon.")
        return redirect("commercial:document_update", pk=nouveau.pk)
    except ValidationError as exc:
        _erreur(request, exc)
    return redirect("commercial:document_detail", pk=pk)


@login_required
@require_POST
def document_annuler(request, pk):
    document = get_object_or_404(Document, pk=pk)
    try:
        document.annuler()
        messages.success(request, "Document annulé.")
    except ValidationError as exc:
        _erreur(request, exc)
    return redirect("commercial:document_detail", pk=pk)


# ---------------------------------------------------------------- Règlements
class ReglementListView(LoginRequiredMixin, ListView):
    model = Reglement
    template_name = "commercial/reglement_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = Reglement.objects.select_related("tiers", "journal")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(tiers__nom__icontains=q) | Q(reference__icontains=q))
        return qs


@login_required
def reglement_create(request):
    initial = {}
    facture = None
    if request.GET.get("document"):
        facture = get_object_or_404(Document, pk=request.GET["document"], type_document__in=Document.TYPES_FACTURATION)
        initial = {"tiers": facture.tiers, "montant": facture.reste_a_payer,
                   "libelle": f"Règlement {facture.numero}"}
    elif request.GET.get("tiers"):
        initial = {"tiers": request.GET["tiers"]}
    initial.setdefault("journal", Journal.objects.filter(code="CA").first())

    form = ReglementForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                reglement = form.save(commit=False)
                if facture and reglement.tiers_id != facture.tiers_id:
                    raise ValidationError("Le tiers du règlement doit être celui de la facture.")
                reglement.enregistrer(factures=[facture] if facture else None)
            messages.success(request, f"Règlement {reglement.numero} enregistré et comptabilisé.")
            return redirect("commercial:reglement_detail", pk=reglement.pk)
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Nouveau règlement", "facture": facture})


class ReglementDetailView(LoginRequiredMixin, DetailView):
    model = Reglement
    template_name = "commercial/reglement_detail.html"
