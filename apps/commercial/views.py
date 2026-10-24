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
from django.utils.html import format_html
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.comptabilite.models import Journal

from .forms import (AgenceForm, ArticleForm, DepotForm, DocumentForm, FamilleArticleForm, InventaireForm, LigneDocumentFormSet,
                    OperationCaisseForm,
                    LigneInventaireFormSet, ReglementForm, TiersForm)
from .models import (Article, CategorieTarifaire, Depot, Document, FamilleArticle, Inventaire, MouvementStock, OperationCaisse,
                     Reglement,
                     StockDepot, TarifCategorie, Tiers, ZERO)


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
        tarifs = {t.categorie_id: t.prix_vente for t in self.object.tarifs.all()}
        ctx["tarifs"] = [(c, tarifs.get(c.pk)) for c in CategorieTarifaire.objects.all()]
        seuils = {s.depot_id: s for s in self.object.stocks_depots.all()}
        ctx["seuils"] = [(d, seuils.get(d.pk)) for d in Depot.objects.filter(actif=True)]
        return ctx


@login_required
@require_POST
def article_parametres(request, pk):
    """Enregistre les tarifs par catégorie et les seuils mini/maxi par dépôt de la fiche article."""
    from decimal import Decimal, InvalidOperation

    article = get_object_or_404(Article, pk=pk)

    def nombre(cle):
        valeur = "".join((request.POST.get(cle) or "").split()).replace("\u202f", "").replace(",", ".")
        if not valeur:
            return None
        try:
            return Decimal(valeur)
        except InvalidOperation:
            raise ValidationError(f"Valeur invalide : « {request.POST.get(cle)} ».")

    try:
        with transaction.atomic():
            for categorie in CategorieTarifaire.objects.all():
                prix = nombre(f"tarif_{categorie.pk}")
                if prix is None:
                    TarifCategorie.objects.filter(article=article, categorie=categorie).delete()
                else:
                    TarifCategorie.objects.update_or_create(article=article, categorie=categorie, defaults={"prix_vente": prix})
            for depot in Depot.objects.filter(actif=True):
                mini, maxi = nombre(f"mini_{depot.pk}") or ZERO, nombre(f"maxi_{depot.pk}") or ZERO
                if maxi and maxi < mini:
                    raise ValidationError(f"Dépôt {depot} : le stock maxi doit être supérieur ou égal au mini.")
                ligne = StockDepot.objects.filter(article=article, depot=depot).first()
                if ligne or mini or maxi:
                    StockDepot.objects.update_or_create(article=article, depot=depot,
                                                        defaults={"stock_mini": mini, "stock_maxi": maxi})
        messages.success(request, "Tarifs et seuils enregistrés.")
    except ValidationError as exc:
        _erreur(request, exc)
    return redirect("commercial:article_detail", pk=pk)


# ---------------------------------------------------------------- Catégories tarifaires
class CategorieListView(LoginRequiredMixin, ListView):
    model = CategorieTarifaire
    template_name = "commercial/categorie_list.html"


@login_required
def categorie_create(request):
    from django import forms

    from apps.core.forms import BootstrapMixin

    class CategorieForm(BootstrapMixin, forms.ModelForm):
        class Meta:
            model = CategorieTarifaire
            fields = "__all__"

    form = CategorieForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Catégorie tarifaire créée.")
        return redirect("commercial:categories")
    return render(request, "core/form.html", {"form": form, "titre": "Nouvelle catégorie tarifaire"})


# ---------------------------------------------------------------- Gestion des besoins
@login_required
def besoins(request):
    from decimal import Decimal, InvalidOperation

    from . import reappro

    depot = Depot.objects.filter(pk=request.GET.get("depot")).first() if request.GET.get("depot") else None
    lignes = reappro.propositions(depot)
    if request.method == "POST":
        choisies = []
        for stock in lignes:
            if f"choisir_{stock.pk}" in request.POST:
                try:
                    quantite = Decimal((request.POST.get(f"quantite_{stock.pk}") or "0").replace(",", "."))
                except InvalidOperation:
                    quantite = ZERO
                choisies.append((stock, quantite))
        commandes, sans_fournisseur = reappro.generer_commandes(choisies, request.user)
        for c in commandes:
            messages.success(request, f"Bon de commande en brouillon créé pour {c.tiers.nom} ({c.depot}).")
        for s in sans_fournisseur:
            messages.warning(request, f"{s.article.reference} : aucun fournisseur principal sur la fiche article, ligne ignorée.")
        if not commandes and not sans_fournisseur:
            messages.info(request, "Aucune ligne sélectionnée.")
        if len(commandes) == 1:
            return redirect("commercial:document_detail", pk=commandes[0].pk)
        return redirect(request.get_full_path())
    return render(request, "commercial/besoins.html", {"lignes": lignes, "depot": depot, "depots": Depot.objects.all()})


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
        g = self.request.GET
        if g.get("depot"):
            qs = qs.filter(depot_id=g["depot"])
        if g.get("date_debut"):
            qs = qs.filter(date__gte=g["date_debut"])
        if g.get("date_fin"):
            qs = qs.filter(date__lte=g["date_fin"])
        if g.get("famille"):
            qs = qs.filter(article__famille_id=g["famille"])
        if g.get("article"):
            qs = qs.filter(article_id=g["article"])
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(article__reference__icontains=q) | Q(article__designation__icontains=q) | Q(libelle__icontains=q))
        return qs


# ---------------------------------------------------------------- Documents
class DocumentListView(LoginRequiredMixin, ListView):
    """Documents des ventes / des achats / des stocks, présentés comme la liste de Sage 100 V12 : filtres prédéfinis
    à gauche (Documents en cours, un filtre par type, Facture comptabilisée, Tous les documents), tri par colonne."""
    model = Document
    template_name = "commercial/document_list.html"
    paginate_by = 100
    TRIS = {"date": "date", "piece": "numero", "tiers": "tiers__code", "intitule": "tiers__nom", "reference": "reference_externe",
            "ht": "total_ht", "depot": "depot__intitule", "type": "type_document"}
    FACTURES = {"ventes": (Document.FACTURE, Document.FACTURE_RETOUR, Document.AVOIR),
                "achats": (Document.ACHAT_FACTURE, Document.ACHAT_FACTURE_RETOUR, Document.ACHAT_AVOIR)}

    def filtres(self):
        """[(code, libellé)] du volet de gauche, comme dans Sage."""
        libelles = dict(Document.TYPES)
        factures = self.FACTURES.get(self.domaine, ())
        courts = {Document.ACHAT_COMMANDE: "Bon de commande", Document.ACHAT_RECEPTION: "Bon de livraison",
                  Document.ACHAT_RETOUR: "Bon de retour", Document.ACHAT_AVOIR_FINANCIER: "Bon d'avoir financier"}
        liste = [("en_cours", "Documents en cours")]
        liste += [(t, courts.get(t, libelles[t])) for t in self._types() if t not in factures]
        if factures:
            liste += [("facture", "Facture"), ("facture_comptabilisee", "Facture comptabilisée")]
        return liste + [("tous", "Tous les documents")]

    def get_queryset(self):
        self.domaine = self.kwargs["domaine"]
        g = self.request.GET
        qs = Document.objects.filter(type_document__in=self._types()).select_related("tiers", "depot", "depot_destination")
        if g.get("depot"):
            qs = qs.filter(Q(depot_id=g["depot"]) | Q(depot_destination_id=g["depot"]))
        self.type_document = g.get("type", "")
        self.filtre = g.get("filtre") or self.type_document or ("tous" if g.get("impayees") or g.get("q") else "en_cours")
        factures = self.FACTURES.get(self.domaine, ())
        if self.type_document:
            qs = qs.filter(type_document=self.type_document)
        elif self.filtre == "en_cours":
            qs = qs.filter(statut__in=(Document.BROUILLON, Document.VALIDE))
        elif self.filtre == "facture":
            qs = qs.filter(type_document__in=factures, ecriture__isnull=True).exclude(statut=Document.ANNULE)
        elif self.filtre == "facture_comptabilisee":
            qs = qs.filter(type_document__in=factures, ecriture__isnull=False)
        elif self.filtre in dict(Document.TYPES):
            qs = qs.filter(type_document=self.filtre)
        if g.get("statut"):
            qs = qs.filter(statut=g["statut"])
        q = g.get("q")
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(tiers__nom__icontains=q) | Q(tiers__code__icontains=q)
                           | Q(reference_externe__icontains=q))
        self.tri = g.get("tri") if g.get("tri") in self.TRIS else "date"
        self.sens = "asc" if g.get("sens") == "asc" else "desc"
        champ = self.TRIS[self.tri]
        qs = qs.order_by(("" if self.sens == "asc" else "-") + champ, "-id")
        if g.get("impayees"):
            qs = [d for d in qs.filter(type_document__in=(Document.FACTURE, Document.ACHAT_FACTURE), statut=Document.VALIDE)
                  if d.reste_a_payer > 0]
        return qs

    def _types(self):
        return {"ventes": Document.TYPES_VENTE, "achats": Document.TYPES_ACHAT}.get(self.domaine, Document.TYPES_STOCK)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        libelles = dict(Document.TYPES)
        g = self.request.GET.copy()
        for cle in ("page", "tri", "sens"):
            g.pop(cle, None)
        base_tri = g.urlencode()
        g.pop("filtre", None)
        g.pop("type", None)
        base_filtre = g.urlencode()
        tiers = "client" if self.domaine == "ventes" else "fournisseur"
        colonnes = [("type", "Type"), ("", "Etat"), ("date", "Date"), ("tiers", f"N° {tiers}"), ("piece", "N° pièce"),
                    ("reference", "Référence"), ("", "Solde dû"), ("ht", "Hors taxe"), ("", "Statut"),
                    ("intitule", f"Intitulé {tiers}"), ("depot", "Dépôt")]
        if self.domaine == "stocks":
            colonnes = [("type", "Type"), ("date", "Date"), ("piece", "N° pièce"), ("reference", "Référence"),
                        ("depot", "Dépôt"), ("", "Destination"), ("ht", "Valeur"), ("", "Statut")]
        ctx.update(domaine=self.domaine, types=[(t, libelles[t]) for t in self._types()], type_document=self.type_document,
                   statuts=Document.STATUTS, depots=Depot.objects.all(), filtres=self.filtres(),
                   filtre=self.filtre, colonnes=colonnes, tri=self.tri, sens=self.sens, base_tri=base_tri,
                   base_filtre=base_filtre, prefixes=Document.PREFIXES,
                   total=ctx["paginator"].count if ctx.get("paginator") else len(ctx["object_list"]))
        return ctx


def _articles_json():
    return {
        a.pk: {"designation": a.designation, "prix_vente": float(a.prix_vente),
               "prix_achat": float(a.prix_achat), "cout": round(float(a.cout_unitaire), 2),
               "taux_tva": float(a.taux_tva), "stock": float(a.stock),
               "tarifs": {t.categorie_id: float(t.prix_vente) for t in a.tarifs.all()}}
        for a in Article.objects.filter(actif=True).prefetch_related("tarifs")
    }


def _tiers_json():
    return {t.pk: {"categorie": t.categorie_tarifaire_id,
                   "libelle": str(t.categorie_tarifaire) if t.categorie_tarifaire_id else ""}
            for t in Tiers.objects.filter(type_tiers=Tiers.CLIENT).select_related("categorie_tarifaire")}


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
                        if getattr(doc, "avertissement", None):
                            messages.warning(request, doc.avertissement)
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
        "articles_json": _articles_json(), "tiers_json": _tiers_json(),
        # En-tête en trois colonnes, comme la fenêtre de pièce de Sage 100 V12
        "colonnes_entete": [("tiers", "payeur", "depot", "depot_destination"), ("date", "date_echeance"),
                            ("reference_externe", "notes")],
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
        facture = getattr(document, "facture_auto", None)
        if facture is not None:
            lien = reverse("commercial:document_detail", args=[facture.pk])
            etat = "validée" if facture.statut == Document.VALIDE else "en brouillon"
            messages.info(request, format_html('Facture <a href="{}" data-nouvelle-fenetre>{}</a> établie automatiquement ({}).',
                                               lien, facture.numero_affiche, etat))
        if getattr(document, "avertissement", None):
            messages.warning(request, document.avertissement)
        if document.mentions_manquantes():
            messages.warning(request, "Mentions obligatoires de la facture (CGI art. 150-5) manquantes : "
                             + ", ".join(document.mentions_manquantes()) + ". Complétez les fiches.")
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
    suivant = request.POST.get("suivant", "")
    if suivant.startswith("/") and not suivant.startswith("//"):      # retour à la liste d'où vient la demande
        return redirect(suivant)
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
        initial = {"tiers": facture.tiers_payeur, "factures": [facture], "montant": facture.reste_a_payer,
                   "libelle": f"Règlement {facture.numero}"}
    elif request.GET.get("commande"):
        commande = get_object_or_404(Document, pk=request.GET["commande"], type_document__in=(Document.COMMANDE, Document.ACHAT_COMMANDE))
        initial = {"tiers": commande.tiers_payeur, "commande": commande, "montant": commande.total_ttc,
                   "libelle": f"Acompte {commande.numero_affiche}"}
    elif request.GET.get("tiers"):
        initial = {"tiers": request.GET["tiers"]}
    initial.setdefault("journal", Journal.objects.filter(code="CA").first())

    form = ReglementForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                reglement = form.save(commit=False)
                reglement.journal = form.cleaned_data["journal"]
                factures = list(form.cleaned_data.get("factures") or [])
                reglement.enregistrer(factures if factures else None)
            messages.success(request, f"Règlement {reglement.numero} enregistré et comptabilisé.")
            return redirect("commercial:reglement_detail", pk=reglement.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Nouveau règlement", "facture": facture})


class ReglementDetailView(LoginRequiredMixin, DetailView):
    model = Reglement
    template_name = "commercial/reglement_detail.html"


@login_required
def reglement_rattacher(request, pk):
    """Rattacher le reste en attente d'un reçu à une nouvelle facture du client."""
    from .forms import RattachementForm

    reglement = get_object_or_404(Reglement, pk=pk)
    form = RattachementForm(reglement, request.POST or None, initial={"facture": request.GET.get("facture")})
    if request.method == "POST" and form.is_valid():
        try:
            imputation = reglement.rattacher(form.cleaned_data["facture"], form.cleaned_data.get("montant"))
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"{imputation.montant:,.0f} rattachés à la facture {imputation.document.numero}.".replace(",", " "))
            return redirect("commercial:reglement_detail", pk=reglement.pk)
    return render(request, "core/form.html", {"form": form, "titre": f"Rattacher le reste du reçu {reglement.numero} "
                                                                     f"({reglement.en_attente_de_rattachement:,.0f})".replace(",", " ")})


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


# ---------------------------------------------------------------- Agences et opérations de caisse
@login_required
def agences(request):
    """Fichier › Paramètres société › Agences : l'agence de ce dossier et les autres agences (comptes de liaison)."""
    from apps.core.models import Agence

    return render(request, "commercial/agence_list.html", {"agences": Agence.objects.select_related("compte_liaison")})


@login_required
def agence_form(request, pk=None):
    from apps.core.models import Agence

    agence = get_object_or_404(Agence, pk=pk) if pk else None
    form = AgenceForm(request.POST or None, instance=agence)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Agence enregistrée.")
        return redirect("commercial:agences")
    return render(request, "core/form.html", {"form": form, "titre": "Agence" if agence else "Nouvelle agence"})


@login_required
def operations_caisse(request):
    """Opérations de caisse du jour (ou de la période) : dépenses, hors recettes, sorties pour une autre agence."""
    g = request.GET
    jour = g.get("date") or timezone.localdate().isoformat()
    qs = OperationCaisse.objects.filter(date=jour).select_related("journal", "agence", "compte", "ecriture")
    if g.get("nature"):
        qs = qs.filter(nature=g["nature"])
    return render(request, "commercial/operation_caisse_list.html", {
        "operations": qs, "jour": jour, "natures": OperationCaisse.NATURES,
        "total_entrees": sum((o.montant for o in qs if o.est_entree), 0),
        "total_sorties": sum((o.montant for o in qs if not o.est_entree), 0)})


@login_required
def operation_caisse_create(request):
    initial = {"journal": Journal.objects.filter(code="CA").first(), "nature": request.GET.get("nature", OperationCaisse.DEPENSE)}
    form = OperationCaisseForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        operation = form.save(commit=False)
        operation.cree_par = request.user
        try:
            operation.enregistrer()
            messages.success(request, f"Opération {operation.numero} enregistrée et comptabilisée.")
            return redirect(f"{reverse('commercial:operations_caisse')}?date={operation.date.isoformat()}")
        except ValidationError as exc:
            _erreur(request, exc)
    return render(request, "core/form.html", {"form": form, "titre": "Nouvelle opération de caisse"})


# ---------------------------------------------------------------- Fiche de stock numérique (magasin)
def _depot_choisi(request):
    return Depot.objects.filter(pk=request.GET.get("depot") or request.POST.get("depot")).first() or Depot.par_defaut()


@login_required
def pointage(request):
    """Le fichiste tape le numéro du bon : les articles s'affichent sans quantité ; il saisit celles du bon papier."""
    from decimal import Decimal, InvalidOperation

    from . import fiche_stock
    from .models import PointageFiche

    depot = _depot_choisi(request)
    numero = (request.GET.get("numero") or request.POST.get("numero") or "").strip()
    document = fiche_stock.trouver_bon(numero) if numero else None
    articles, existant = [], None
    if numero and document is None:
        if Document.objects.filter(numero__iendswith=numero).count() > 1:
            messages.error(request, f"Plusieurs bons se terminent par « {numero} » : tapez le numéro complet (ex. BL2026-{numero}).")
        else:
            messages.error(request, f"Aucun bon ne porte le numéro « {numero} ».")
    elif document:
        articles = sorted(PointageFiche.quantites_machine(document, depot), key=lambda a: a.reference)
        existant = PointageFiche.objects.filter(document=document, depot=depot).first()
        if not articles:
            messages.warning(request, f"Le bon {document.numero_affiche} ne fait pas bouger le stock du dépôt {depot}.")
    if request.method == "POST" and document and articles:
        saisies = {}
        try:
            for a in articles:
                valeur = (request.POST.get(f"qte_{a.pk}") or "").replace(",", ".").replace(" ", "").replace("\xa0", "")
                saisies[a.pk] = Decimal(valeur) if valeur else None          # vide = non saisi (différent de 0)
        except InvalidOperation:
            messages.error(request, "Quantité incorrecte : saisissez un nombre (ex. 12 ou 12,5).")
        else:
            p = existant or PointageFiche(document=document, depot=depot)
            p.observation = request.POST.get("observation", "")[:200]
            try:
                p.enregistrer(saisies, fichiste=request.user)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                return redirect("commercial:pointage_detail", pk=p.pk)
    return render(request, "commercial/pointage.html", {
        "depots": Depot.objects.filter(actif=True), "depot": depot, "numero": numero, "document": document,
        "articles": articles, "existant": existant})


@login_required
def pointage_detail(request, pk):
    from .models import PointageFiche

    p = get_object_or_404(PointageFiche.objects.select_related("document", "depot", "fichiste"), pk=pk)
    # Le fichiste voit conforme / écart ; les quantités de l'ordinateur sont réservées aux contrôleurs
    return render(request, "commercial/pointage_detail.html", {"p": p, "voir_quantites": request.user.is_superuser or request.user.is_staff})


@login_required
def pointages(request):
    from .models import PointageFiche

    qs = PointageFiche.objects.select_related("document", "depot", "fichiste")
    if request.GET.get("statut"):
        qs = qs.filter(statut=request.GET["statut"])
    return render(request, "commercial/pointage_list.html", {"pointages": qs[:300]})


@login_required
def fiche_rapprochement(request):
    """Rapprochement fiche de stock / ordinateur : bons à pointer, écarts, stock de la fiche par article."""
    import datetime

    from django.utils.dateparse import parse_date

    from . import fiche_stock

    depot = _depot_choisi(request)
    debut = parse_date(request.GET.get("date_debut") or "") or datetime.date.today().replace(day=1)
    fin = parse_date(request.GET.get("date_fin") or "") or datetime.date.today()
    from apps.core.models import Societe

    delai = Societe.get().delai_pointage
    en_retard = {d.pk for d in fiche_stock.bons_en_retard(depot, datetime.date.today(), delai)}
    return render(request, "commercial/fiche_rapprochement.html", {
        "depot": depot, "debut": debut, "fin": fin, "a_pointer": fiche_stock.bons_a_pointer(depot, debut, fin),
        "en_retard": en_retard, "delai": delai,
        "ecarts": fiche_stock.ecarts(depot, debut, fin),
        "articles": fiche_stock.rapprochement(depot, ecarts_seulement=request.GET.get("tous") != "1")})


@login_required
def fiche_article(request):
    """Fiche de stock d'un article (numérique), comme la fiche papier du fichiste."""
    import datetime

    from django.utils.dateparse import parse_date

    from . import fiche_stock

    depot = _depot_choisi(request)
    article = Article.objects.filter(pk=request.GET.get("article")).first()
    debut = parse_date(request.GET.get("date_debut") or "") or datetime.date.today().replace(day=1)
    fin = parse_date(request.GET.get("date_fin") or "") or datetime.date.today()
    fiche = fiche_stock.fiche_article(article, depot, debut, fin) if article else None
    return render(request, "commercial/fiche_article.html", {"depot": depot, "article": article, "debut": debut, "fin": fin, "fiche": fiche})
