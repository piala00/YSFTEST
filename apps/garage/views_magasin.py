"""Écrans du magasin : articles et stock, achats (stock, véhicule, immobilisation), sorties."""
import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal
from apps.transport.models import Vehicule

from .models_magasin import AchatMagasin, ArticleMagasin, LigneAchatMagasin, MouvementMagasin, sortir

LIGNES_ACHAT = 6


def _erreur(request, exc):
    messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))


def _decimal(valeur, defaut="0"):
    try:
        return Decimal(str(valeur if valeur is not None else "").replace(",", ".").replace(" ", "") or defaut)
    except InvalidOperation:
        raise ValidationError(f"Nombre invalide : {valeur}")


@login_required
def stock(request):
    """Articles du magasin, quantités et valeur au coût moyen ; création d'un article."""
    if request.method == "POST":
        try:
            code = request.POST.get("code", "").strip().upper()
            if not code or not request.POST.get("designation", "").strip():
                raise ValidationError("Indiquez le code et la désignation.")
            if ArticleMagasin.objects.filter(code=code).exists():
                raise ValidationError(f"Le code {code} existe déjà.")
            ArticleMagasin.objects.create(code=code, designation=request.POST["designation"].strip(),
                                          categorie=request.POST.get("categorie") or ArticleMagasin.PIECE,
                                          unite=request.POST.get("unite") or "pièce", seuil=_decimal(request.POST.get("seuil")))
            messages.success(request, f"Article {code} créé.")
        except ValidationError as exc:
            _erreur(request, exc)
        return redirect(request.path)
    articles = ArticleMagasin.objects.filter(actif=True).select_related("compte_stock", "compte_charge")
    return render(request, "garage/magasin_stock.html", {
        "articles": articles, "categories": ArticleMagasin.CATEGORIES,
        "valeur": sum((a.valeur for a in articles), Decimal(0))})


@login_required
def achats(request):
    return render(request, "garage/magasin_achats.html", {
        "achats": AchatMagasin.objects.select_related("fournisseur", "ecriture").prefetch_related("lignes")[:200]})


@login_required
def achat_nouveau(request):
    """Une facture d'achat : chaque ligne va au stock, à un véhicule précis, ou en immobilisation."""
    if request.method == "POST":
        try:
            achat = AchatMagasin(date=datetime.date.fromisoformat(request.POST.get("date") or datetime.date.today().isoformat()),
                                 fournisseur=Tiers.objects.filter(pk=request.POST.get("fournisseur") or None).first(),
                                 facture=request.POST.get("facture", "").strip(), paiement=request.POST.get("paiement") or AchatMagasin.COMPTE,
                                 caisse=Journal.objects.filter(pk=request.POST.get("caisse") or None).first(), cree_par=request.user)
            lignes = []
            for i in range(LIGNES_ACHAT):
                article = ArticleMagasin.objects.filter(pk=request.POST.get(f"article_{i}") or None).first()
                designation = request.POST.get(f"designation_{i}", "").strip()
                if not article and not designation:
                    continue
                lignes.append(LigneAchatMagasin(
                    destination=request.POST.get(f"destination_{i}") or LigneAchatMagasin.STOCK, article=article,
                    designation=designation, quantite=_decimal(request.POST.get(f"quantite_{i}"), "1"),
                    prix_unitaire=_decimal(request.POST.get(f"prix_{i}")),
                    vehicule=Vehicule.objects.filter(pk=request.POST.get(f"vehicule_{i}") or None).first(),
                    compte=Compte.objects.filter(numero=request.POST.get(f"compte_{i}", "").strip()).first()
                    if request.POST.get(f"compte_{i}", "").strip() else None))
            if not lignes:
                raise ValidationError("Ajoutez au moins une ligne.")
            from django.db import transaction

            with transaction.atomic():
                achat.save()
                for l in lignes:
                    l.achat = achat
                    l.save()
                achat.valider(request.user)
            messages.success(request, f"Achat {achat.numero} enregistré : {achat.total:,.0f} FCFA.".replace(",", " "))
            return redirect("garage:magasin_achats")
        except (ValidationError, ValueError) as exc:
            _erreur(request, exc)
    return render(request, "garage/magasin_achat.html", {
        "lignes": range(LIGNES_ACHAT), "articles": ArticleMagasin.objects.filter(actif=True),
        "vehicules": Vehicule.objects.filter(actif=True), "destinations": LigneAchatMagasin.DESTINATIONS,
        "fournisseurs": Tiers.objects.filter(type_tiers=Tiers.FOURNISSEUR, actif=True).order_by("nom"),
        "caisses": Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE, compte_tresorerie__isnull=False),
        "paiements": AchatMagasin.PAIEMENTS, "aujourdhui": datetime.date.today()})


@login_required
def sorties(request):
    """Sortie du stock : la charge passe au véhicule (ou à l'agence) au coût moyen."""
    if request.method == "POST":
        try:
            m = sortir(get_object_or_404(ArticleMagasin, pk=request.POST.get("article")), _decimal(request.POST.get("quantite"), "1"),
                       Vehicule.objects.filter(pk=request.POST.get("vehicule") or None).first(), request.POST.get("motif", ""),
                       utilisateur=request.user)
            messages.success(request, f"Sortie enregistrée : {m.montant:,.0f} FCFA.".replace(",", " "))
        except (ValidationError, ValueError) as exc:
            _erreur(request, exc)
        return redirect(request.path)
    return render(request, "garage/magasin_sorties.html", {
        "mouvements": MouvementMagasin.objects.select_related("article", "vehicule", "ordre", "ecriture")[:300],
        "articles": ArticleMagasin.objects.filter(actif=True, quantite__gt=0), "vehicules": Vehicule.objects.filter(actif=True)})
