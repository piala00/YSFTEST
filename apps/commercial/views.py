from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.comptabilite.models import Journal

from .forms import (ArticleForm, DepotForm, DocumentForm, FamilleArticleForm, InventaireForm, LigneDocumentFormSet,
                    LigneInventaireFormSet, ReglementForm, TiersForm)
from .models import Article, Depot, Document, FamilleArticle, Inventaire, MouvementStock, Reglement, StockDepot, Tiers, ZERO


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
        if self.request.GET.get("vue") == "comptes":
            for t in ctx["object_list"]:
                t.solde = t.solde_comptable()
                t.reste_du = t.encours()
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
        ctx["mouvements"] = self.object.mouvements.select_related("document", "depot")[:100]
        ctx["stocks_depots"] = self.object.stocks_depots.select_related("depot")
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
        self.depot = Depot.objects.filter(pk=self.request.GET.get("depot")).first() if self.request.GET.get("depot") else None
        qs = Article.objects.filter(suivi_stock=True, actif=True).select_related("famille")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(reference__icontains=q) | Q(designation__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        depots = list(Depot.objects.filter(actif=True))
        quantites = {(s.article_id, s.depot_id): s.quantite for s in StockDepot.objects.all()}
        lignes = []
        for article in ctx["object_list"]:
            par_depot = [quantites.get((article.pk, d.pk), ZERO) for d in depots]
            quantite = quantites.get((article.pk, self.depot.pk), ZERO) if self.depot else article.stock
            lignes.append({"article": article, "par_depot": par_depot, "quantite": quantite,
                           "valeur": round(quantite * article.cout_unitaire),
                           "alerte": article.suivi_stock and quantite <= article.stock_minimum})
        ctx.update(depots=depots, depot=self.depot, lignes=lignes,
                   valeur_totale=sum(l["valeur"] for l in lignes),
                   mouvements=MouvementStock.objects.select_related("article", "document", "depot")[:30])
        return ctx


class EtatInventaireView(LoginRequiredMixin, ListView):
    """État › Inventaire : quantités et valeur du stock à une date, par dépôt."""
    template_name = "commercial/etat_inventaire.html"

    def get_queryset(self):
        return Article.objects.filter(suivi_stock=True).select_related("famille").order_by("famille__libelle", "reference")

    def get_context_data(self, **kwargs):
        import datetime

        ctx = super().get_context_data(**kwargs)
        try:
            date = datetime.date.fromisoformat(self.request.GET.get("date", ""))
        except ValueError:
            date = timezone.localdate()
        depot = Depot.objects.filter(pk=self.request.GET.get("depot")).first() if self.request.GET.get("depot") else None
        # Stock à date = stock actuel - mouvements postérieurs à la date
        posterieurs = MouvementStock.objects.filter(date__gt=date)
        actuels = StockDepot.objects.all()
        if depot:
            posterieurs = posterieurs.filter(depot=depot)
            actuels = actuels.filter(depot=depot)
        apres = {r["article"]: r["q"] for r in posterieurs.values("article").annotate(q=Sum("quantite"))}
        stock = {r["article"]: r["q"] for r in actuels.values("article").annotate(q=Sum("quantite"))}
        lignes = []
        for article in ctx["object_list"]:
            quantite = (stock.get(article.pk) or ZERO) - (apres.get(article.pk) or ZERO)
            if quantite:
                lignes.append({"article": article, "quantite": quantite, "cout": article.cout_unitaire,
                               "valeur": round(quantite * article.cout_unitaire)})
        ctx.update(date=date, depot=depot, depots=Depot.objects.all(), lignes=lignes,
                   prep=self.request.GET.get("vue") == "preparatoire",
                   total=sum(l["valeur"] for l in lignes))
        return ctx


# ---------------------------------------------------------------- Dépôts
class DepotListView(LoginRequiredMixin, ListView):
    model = Depot
    template_name = "commercial/depot_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for depot in ctx["object_list"]:
            stocks = depot.stocks.select_related("article")
            depot.nb_articles = sum(1 for s in stocks if s.quantite)
            depot.valeur = sum(round(s.quantite * s.article.cout_unitaire) for s in stocks)
        return ctx


class DepotCreateView(LoginRequiredMixin, CreateView):
    model = Depot
    form_class = DepotForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:depots")
    extra_context = {"titre": "Nouveau dépôt de stockage"}


class DepotUpdateView(LoginRequiredMixin, UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "core/form.html"
    success_url = reverse_lazy("commercial:depots")
    extra_context = {"titre": "Modifier le dépôt"}


# ---------------------------------------------------------------- Inventaires
class InventaireListView(LoginRequiredMixin, ListView):
    model = Inventaire
    template_name = "commercial/inventaire_list.html"

    def get_queryset(self):
        return Inventaire.objects.select_related("depot", "famille")


@login_required
def inventaire_create(request):
    form = InventaireForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            inventaire = form.save()
            inventaire.initialiser_lignes()
        messages.success(request, f"Inventaire {inventaire.numero} ouvert : saisissez les quantités comptées.")
        return redirect("commercial:inventaire_detail", pk=inventaire.pk)
    return render(request, "core/form.html", {"form": form, "titre": "Nouvelle saisie d'inventaire"})


@login_required
def inventaire_detail(request, pk):
    inventaire = get_object_or_404(Inventaire.objects.select_related("depot"), pk=pk)
    lignes = inventaire.lignes.select_related("article", "article__famille")
    formset = LigneInventaireFormSet(request.POST or None, queryset=lignes)
    if request.method == "POST":
        if inventaire.statut != Inventaire.BROUILLON:
            messages.error(request, "Cet inventaire est validé : il n'est plus modifiable.")
            return redirect("commercial:inventaire_detail", pk=pk)
        if formset.is_valid():
            formset.save()
            if "valider" in request.POST:
                try:
                    inventaire.valider()
                    messages.success(request, "Inventaire validé : les écarts ont été passés en mouvements de stock.")
                except ValidationError as exc:
                    _erreur(request, exc)
            else:
                messages.success(request, "Quantités enregistrées.")
            return redirect("commercial:inventaire_detail", pk=pk)
    return render(request, "commercial/inventaire_detail.html", {
        "inventaire": inventaire, "formset": formset, "lignes": zip(lignes, formset.forms),
    })


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


class MouvementListView(LoginRequiredMixin, ListView):
    template_name = "commercial/mouvement_list.html"
    paginate_by = 100
    extra_context = {"depots": Depot.objects.all}

    def get_queryset(self):
        qs = MouvementStock.objects.select_related("article", "document", "depot")
        if self.request.GET.get("depot"):
            qs = qs.filter(depot_id=self.request.GET["depot"])
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(article__reference__icontains=q) | Q(article__designation__icontains=q) | Q(libelle__icontains=q))
        return qs


# ---------------------------------------------------------------- Documents
class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "commercial/document_list.html"
    paginate_by = 50

    def get_queryset(self):
        self.domaine = self.kwargs["domaine"]
        qs = Document.objects.filter(type_document__in=self._types()).select_related("tiers", "depot", "depot_destination")
        if self.request.GET.get("depot"):
            qs = qs.filter(Q(depot_id=self.request.GET["depot"]) | Q(depot_destination_id=self.request.GET["depot"]))
        self.type_document = self.request.GET.get("type", "")
        if self.type_document:
            qs = qs.filter(type_document=self.type_document)
        statut = self.request.GET.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(tiers__nom__icontains=q) | Q(reference_externe__icontains=q))
        if self.request.GET.get("impayees"):
            qs = [d for d in qs.filter(type_document__in=(Document.FACTURE, Document.ACHAT_FACTURE), statut=Document.VALIDE)
                  if d.reste_a_payer > 0]
        return qs

    def _types(self):
        return {"ventes": Document.TYPES_VENTE, "achats": Document.TYPES_ACHAT}.get(self.domaine, Document.TYPES_STOCK)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        libelles = dict(Document.TYPES)
        ctx.update(domaine=self.domaine, types=[(t, libelles[t]) for t in self._types()],
                   type_document=self.type_document, statuts=Document.STATUTS, depots=Depot.objects.all())
        return ctx


def _articles_json():
    return {
        a.pk: {"designation": a.designation, "prix_vente": float(a.prix_vente),
               "prix_achat": float(a.prix_achat), "cout": round(float(a.cout_unitaire), 2),
               "taux_tva": float(a.taux_tva), "stock": float(a.stock)}
        for a in Article.objects.filter(actif=True)
    }


def _document_form(request, document, type_document):
    document.type_document = type_document
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
        "titre": dict(Document.TYPES)[type_document], "est_vente": est_vente, "domaine": document.domaine,
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
        sens = self.request.GET.get("sens")
        if sens:
            qs = qs.filter(tiers__type_tiers=Tiers.CLIENT if sens == "E" else Tiers.FOURNISSEUR)
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


# ---------------------------------------------------------------- Recherche de documents
def _filtres_recherche(request, prefixe=""):
    g = request.GET
    filtres = Q()
    if g.get("domaine"):
        types = {"ventes": Document.TYPES_VENTE, "achats": Document.TYPES_ACHAT, "stocks": Document.TYPES_STOCK}[g["domaine"]]
        filtres &= Q(**{f"{prefixe}type_document__in": types})
    if g.get("type"):
        filtres &= Q(**{f"{prefixe}type_document": g["type"]})
    if g.get("statut"):
        filtres &= Q(**{f"{prefixe}statut": g["statut"]})
    if g.get("du"):
        filtres &= Q(**{f"{prefixe}date__gte": g["du"]})
    if g.get("au"):
        filtres &= Q(**{f"{prefixe}date__lte": g["au"]})
    if g.get("depot"):
        filtres &= Q(**{f"{prefixe}depot_id": g["depot"]})
    if g.get("tiers"):
        filtres &= Q(**{f"{prefixe}tiers__nom__icontains": g["tiers"]}) | Q(**{f"{prefixe}tiers__code__icontains": g["tiers"]})
    if g.get("numero"):
        filtres &= Q(**{f"{prefixe}numero__icontains": g["numero"]}) | Q(**{f"{prefixe}reference_externe__icontains": g["numero"]})
    return filtres


def _contexte_recherche():
    return {"types": Document.TYPES, "statuts": Document.STATUTS, "depots": Depot.objects.all()}


@login_required
def recherche_entetes(request):
    documents = Document.objects.none()
    if request.GET:
        documents = Document.objects.filter(_filtres_recherche(request)).select_related("tiers", "depot")[:500]
    return render(request, "commercial/recherche.html", {**_contexte_recherche(), "documents": documents, "mode": "entetes"})


@login_required
def recherche_lignes(request):
    from .models import LigneDocument

    lignes = LigneDocument.objects.none()
    if request.GET:
        lignes = LigneDocument.objects.filter(_filtres_recherche(request, "document__")).select_related(
            "document", "document__tiers", "article")
        if request.GET.get("article"):
            a = request.GET["article"]
            lignes = lignes.filter(Q(article__reference__icontains=a) | Q(designation__icontains=a))
        lignes = lignes.order_by("-document__date")[:500]
    return render(request, "commercial/recherche.html", {**_contexte_recherche(), "lignes": lignes, "mode": "lignes"})
