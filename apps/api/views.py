import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from apps.commercial.models import Article, Document, Reglement, Tiers
from apps.comptabilite import etats, services as compta
from apps.comptabilite.models import Compte, Ecriture, Journal
from apps.core.models import Exercice
from apps.core.navigation import MODULES, MODULES_PAR_CODE, serialiser_module
from apps.reporting import services as reporting

from . import serializers as s


def _erreur(exc):
    return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)


class RechercheMixin:
    champs_recherche = ()

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q")
        if q and self.champs_recherche:
            filtre = Q()
            for champ in self.champs_recherche:
                filtre |= Q(**{f"{champ}__icontains": q})
            qs = qs.filter(filtre)
        return qs


class TiersViewSet(RechercheMixin, viewsets.ModelViewSet):
    serializer_class = s.TiersSerializer
    champs_recherche = ("code", "nom", "ville")

    def get_queryset(self):
        qs = Tiers.objects.all()
        if self.request.query_params.get("type"):
            qs = qs.filter(type_tiers=self.request.query_params["type"])
        self.queryset = qs
        return super().get_queryset()

    @action(detail=True)
    def solde(self, request, pk=None):
        tiers = self.get_object()
        return Response({"solde_comptable": tiers.solde_comptable(), "encours": tiers.encours()})


class ArticleViewSet(RechercheMixin, viewsets.ModelViewSet):
    queryset = Article.objects.select_related("famille")
    serializer_class = s.ArticleSerializer
    champs_recherche = ("reference", "designation")


class DocumentViewSet(RechercheMixin, viewsets.ModelViewSet):
    serializer_class = s.DocumentSerializer
    champs_recherche = ("numero", "tiers__nom", "reference_externe")

    def get_queryset(self):
        qs = Document.objects.select_related("tiers", "depot").prefetch_related("lignes")
        p = self.request.query_params
        if p.get("type"):
            qs = qs.filter(type_document=p["type"])
        if p.get("domaine") == "ventes":
            qs = qs.filter(type_document__in=Document.TYPES_VENTE)
        elif p.get("domaine") == "achats":
            qs = qs.filter(type_document__in=Document.TYPES_ACHAT)
        elif p.get("domaine") == "stocks":
            qs = qs.filter(type_document__in=Document.TYPES_STOCK)
        if p.get("statut"):
            qs = qs.filter(statut=p["statut"])
        if p.get("tiers"):
            qs = qs.filter(tiers_id=p["tiers"])
        self.queryset = qs
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if not document.modifiable:
            return Response({"detail": "Seul un brouillon peut être supprimé."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        try:
            document = self.get_object().valider()
        except DjangoValidationError as exc:
            return _erreur(exc)
        return Response({**self.get_serializer(document).data, "avertissement": getattr(document, "avertissement", None)})

    @action(detail=True, methods=["post"])
    def transformer(self, request, pk=None):
        try:
            nouveau = self.get_object().transformer(request.data.get("type_cible"), request.user)
        except DjangoValidationError as exc:
            return _erreur(exc)
        return Response(self.get_serializer(nouveau).data, status=status.HTTP_201_CREATED)


class ReglementViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Reglement.objects.select_related("tiers")
    serializer_class = s.ReglementSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except DjangoValidationError as exc:
            return _erreur(exc)


class CompteViewSet(RechercheMixin, viewsets.ModelViewSet):
    queryset = Compte.objects.all()
    serializer_class = s.CompteSerializer
    champs_recherche = ("numero", "intitule")
    pagination_class = None


class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = s.JournalSerializer
    pagination_class = None


class EcritureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ecriture.objects.select_related("journal").prefetch_related("lignes__compte")
    serializer_class = s.EcritureSerializer


def _dates(request):
    exercice = Exercice.courant()
    def lire(cle, defaut):
        valeur = request.query_params.get(cle)
        return datetime.date.fromisoformat(valeur) if valeur else defaut
    debut = lire("du", exercice.date_debut if exercice else datetime.date.today().replace(month=1, day=1))
    fin = lire("au", exercice.date_fin if exercice else datetime.date.today())
    return debut, fin


@api_view(["GET"])
def dashboard(request):
    d = reporting.tableau_de_bord()
    d["alertes_stock"] = [{"id": a.id, "reference": a.reference, "designation": a.designation,
                           "stock": a.stock, "stock_minimum": a.stock_minimum} for a in d["alertes_stock"]]
    return Response(d)


@api_view(["GET"])
def balance(request):
    debut, fin = _dates(request)
    lignes, totaux = compta.balance(debut, fin, request.query_params.get("compte_debut", ""),
                                    request.query_params.get("compte_fin", ""))
    for l in lignes:
        l["numero"], l["intitule"] = l["compte"].numero, l["compte"].intitule
        del l["compte"]
    return Response({"du": debut, "au": fin, "lignes": lignes, "totaux": totaux})


@api_view(["GET"])
def bilan(request):
    _, fin = _dates(request)
    return Response(etats.bilan(fin))


@api_view(["GET"])
def compte_resultat(request):
    debut, fin = _dates(request)
    return Response(etats.compte_de_resultat(debut, fin))


@api_view(["GET"])
def balance_agee(request):
    data = reporting.balance_agee(request.query_params.get("type", Tiers.CLIENT))
    for l in data["lignes"]:
        l["tiers"] = {"id": l["tiers"].id, "code": l["tiers"].code, "nom": l["tiers"].nom}
    return Response(data)


@api_view(["GET"])
def navigation(request):
    """Structure Module → Onglets → Éléments → Sous-éléments (utilisée par le client bureau)."""
    code = request.query_params.get("module")
    if code:
        if code not in MODULES_PAR_CODE:
            return Response({"detail": "Module inconnu."}, status=status.HTTP_404_NOT_FOUND)
        return Response(_navigation_avec_droits(request, MODULES_PAR_CODE[code]))
    return Response([_navigation_avec_droits(request, m) for m in MODULES])


def _navigation_avec_droits(request, module):
    """Menus du logiciel, les entrées interdites au profil marquées (« interdit ») et sans lien."""
    from apps.core.droits import Droits, annoter

    donnees = serialiser_module(module)
    droits = Droits(request.user, module)
    if not droits.libre:
        for onglet in donnees["onglets"]:
            annoter(onglet["elements"], droits)
    return donnees
