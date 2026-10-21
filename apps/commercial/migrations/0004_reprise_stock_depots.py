"""Reprise des données existantes : dépôt principal, stock par dépôt et CMUP initial."""
from django.db import migrations
from django.db.models import F


def reprendre(apps, schema_editor):
    Article = apps.get_model("commercial", "Article")
    Depot = apps.get_model("commercial", "Depot")
    StockDepot = apps.get_model("commercial", "StockDepot")
    Document = apps.get_model("commercial", "Document")
    MouvementStock = apps.get_model("commercial", "MouvementStock")
    if not Article.objects.exists() and not Document.objects.exists():
        return
    depot = Depot.objects.filter(principal=True).first() or Depot.objects.create(
        code="DP", intitule="Dépôt principal", principal=True)
    for article in Article.objects.filter(suivi_stock=True):
        if article.stock:
            StockDepot.objects.get_or_create(article=article, depot=depot, defaults={"quantite": article.stock})
    Article.objects.filter(cmup=0).update(cmup=F("prix_achat"))
    Document.objects.filter(depot__isnull=True).exclude(
        type_document__in=["DEVIS", "COMMANDE", "ACHAT_COMMANDE"]).update(depot=depot)
    MouvementStock.objects.filter(depot__isnull=True).update(depot=depot)


class Migration(migrations.Migration):
    dependencies = [("commercial", "0003_stocks_depots_documents_sage")]
    operations = [migrations.RunPython(reprendre, migrations.RunPython.noop)]
