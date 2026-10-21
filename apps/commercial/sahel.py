"""Société fictive SAHEL DISTRIBUTION (skill « sage-100-gescom-v12-formateur-expert », exercices/01).

Données entièrement inventées, pour s'exercer aux cas pratiques du formateur dans l'ERP :
    python manage.py init_erp --sahel
"""
from django.db import transaction

from .models import Article, CategorieTarifaire, Depot, Document, FamilleArticle, LigneDocument, TarifCategorie, Tiers

# (référence, désignation, famille, prix d'achat, prix GROS, prix DÉTAIL, nature)
ARTICLES = [
    ("JUS-001", "Jus mangue 1 L", "BOISSONS", 800, 1200, 1500, Article.MARCHANDISE),
    ("EAU-001", "Eau plate 1,5 L", "BOISSONS", 250, 350, 450, Article.MARCHANDISE),
    ("RIZ-025", "Riz sac 25 kg", "ALIMENTAIRE", 13000, 15500, 16000, Article.MARCHANDISE),
    ("TRANS-001", "Frais de transport (prestation)", "SERVICES", 0, None, None, Article.SERVICE),
]
# Stocks initiaux par dépôt : JUS-001, EAU-001, RIZ-025
STOCKS_INITIAUX = {"DPT-PRINCIPAL": (100, 200, 50), "DPT-BOUTIQUE": (20, 40, 10), "DPT-BOISSONS": (80, 150, 0)}


@transaction.atomic
def creer_societe():
    """Crée dépôts, familles, articles, catégories tarifaires et tiers. Renvoie un dictionnaire d'accès."""
    s = {}
    principal = Depot.par_defaut()
    principal.code, principal.intitule = "DPT-PRINCIPAL", "Magasin principal"
    principal.save()
    s["depots"] = {"DPT-PRINCIPAL": principal}
    for code, intitule in (("DPT-BOUTIQUE", "Boutique (vente détail)"), ("DPT-BOISSONS", "Dépôt boissons"),
                           ("DPT-TRANSIT", "Transit")):
        s["depots"][code] = Depot.objects.create(code=code, intitule=intitule)
    s["familles"] = {code: FamilleArticle.objects.create(code=code, libelle=code.capitalize())
                     for code in ("BOISSONS", "ALIMENTAIRE", "SERVICES")}
    s["categories"] = {"GROS": CategorieTarifaire.objects.create(code="GROS", intitule="Gros"),
                       "DETAIL": CategorieTarifaire.objects.create(code="DETAIL", intitule="Détail")}
    s["fournisseurs"] = {
        "FOU-BOIS-01": Tiers.objects.create(code="FOU-BOIS-01", nom="Fournisseur boissons", type_tiers=Tiers.FOURNISSEUR),
        "FOU-ALIM-01": Tiers.objects.create(code="FOU-ALIM-01", nom="Fournisseur aliments", type_tiers=Tiers.FOURNISSEUR),
    }
    s["articles"] = {}
    for reference, designation, famille, achat, gros, detail, nature in ARTICLES:
        article = Article.objects.create(
            reference=reference, designation=designation, famille=s["familles"][famille], nature=nature,
            suivi_stock=nature != Article.SERVICE, prix_achat=achat, prix_vente=detail or 0,
            fournisseur_principal=s["fournisseurs"]["FOU-BOIS-01" if famille == "BOISSONS" else "FOU-ALIM-01"]
            if nature != Article.SERVICE else None)
        if gros:
            TarifCategorie.objects.create(article=article, categorie=s["categories"]["GROS"], prix_vente=gros)
            TarifCategorie.objects.create(article=article, categorie=s["categories"]["DETAIL"], prix_vente=detail)
        s["articles"][reference] = article
    s["clients"] = {
        "CLI-GROS-01": Tiers.objects.create(code="CLI-GROS-01", nom="Client gros (crédit)", delai_paiement=30,
                                            categorie_tarifaire=s["categories"]["GROS"], plafond_credit=300000),
        "CLI-DETAIL-01": Tiers.objects.create(code="CLI-DETAIL-01", nom="Client détail (comptant)", delai_paiement=0,
                                              categorie_tarifaire=s["categories"]["DETAIL"]),
        "CLI-ENC-01": Tiers.objects.create(code="CLI-ENC-01", nom="Client sous plafond", delai_paiement=15,
                                           plafond_credit=100000, code_risque=Tiers.RISQUE_BLOQUER),
    }
    return s


@transaction.atomic
def saisir_stocks_initiaux(societe, date):
    """Stocks initiaux par mouvements d'entrée (jamais en écrivant la quantité dans la fiche article)."""
    articles = [societe["articles"][r] for r in ("JUS-001", "EAU-001", "RIZ-025")]
    for code, quantites in STOCKS_INITIAUX.items():
        entree = Document.objects.create(type_document=Document.STOCK_ENTREE, depot=societe["depots"][code], date=date,
                                         reference_externe="STOCK-INITIAL", notes="Stock initial SAHEL DISTRIBUTION")
        for article, quantite in zip(articles, quantites):
            if quantite:
                LigneDocument.objects.create(document=entree, article=article, quantite=quantite,
                                             prix_unitaire=article.prix_achat)
        entree.recalculer()
        entree.valider()
