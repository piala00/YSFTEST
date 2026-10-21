"""Gestion des besoins : réapprovisionnement selon les seuils mini/maxi de chaque dépôt (atelier 5.4 du skill formateur)."""
from collections import defaultdict

from django.db import transaction

from .models import Document, LigneDocument, StockDepot

def propositions(depot=None):
    """Couples article × dépôt sous le stock mini, avec la quantité qui ramène au stock maxi."""
    qs = (StockDepot.objects.filter(stock_mini__gt=0, article__actif=True, article__suivi_stock=True)
          .select_related("article", "article__fournisseur_principal", "depot"))
    if depot is not None:
        qs = qs.filter(depot=depot)
    return [s for s in qs.order_by("depot__intitule", "article__reference") if s.besoin > 0]


@transaction.atomic
def generer_commandes(lignes_choisies, utilisateur=None):
    """Crée un bon de commande fournisseur en brouillon par couple (fournisseur, dépôt).

    `lignes_choisies` : liste de (StockDepot, quantité). Les lignes sans fournisseur principal sont ignorées
    et renvoyées pour que l'utilisateur complète la fiche article.
    """
    groupes, sans_fournisseur = defaultdict(list), []
    for stock, quantite in lignes_choisies:
        if quantite <= 0:
            continue
        fournisseur = stock.article.fournisseur_principal
        if fournisseur is None:
            sans_fournisseur.append(stock)
            continue
        groupes[(fournisseur.pk, stock.depot_id)].append((stock, quantite))
    commandes = []
    for (_, _), lignes in groupes.items():
        premier = lignes[0][0]
        commande = Document.objects.create(
            type_document=Document.ACHAT_COMMANDE, tiers=premier.article.fournisseur_principal,
            depot=premier.depot, cree_par=utilisateur, notes="Proposition de réapprovisionnement (stock sous le mini)")
        for stock, quantite in lignes:
            LigneDocument.objects.create(document=commande, article=stock.article, quantite=quantite,
                                         prix_unitaire=stock.article.prix_achat, taux_tva=stock.article.taux_tva)
        commande.recalculer()
        commandes.append(commande)
    return commandes, sans_fournisseur
