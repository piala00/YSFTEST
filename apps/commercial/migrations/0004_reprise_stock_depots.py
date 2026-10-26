"""Reprise des données existantes : dépôt principal, stock par dépôt et CMUP initial."""
from django.db import migrations
from django.db.models import F


def reprendre(apps, schema_editor):
    Article = apps.get_model("commercial", "Article")
    Depot = apps.get_model("commercial", "Depot")
    StockDepot = apps.get_model("commercial", "StockDepot")
    Document = apps.get_model("commercial", "Document")
    MouvementStock = apps.get_model("commercial", "MouvementStock")
    if not Article.objects.using(schema_editor.connection.alias).exists() and not Document.objects.using(schema_editor.connection.alias).exists():
        return
    depot = Depot.objects.using(schema_editor.connection.alias).filter(principal=True).first() or Depot.objects.using(schema_editor.connection.alias).create(
        code="DP", intitule="Dépôt principal", principal=True)
    for article in Article.objects.using(schema_editor.connection.alias).filter(suivi_stock=True):
        if article.stock:
            StockDepot.objects.using(schema_editor.connection.alias).get_or_create(article=article, depot=depot, defaults={"quantite": article.stock})
    Article.objects.using(schema_editor.connection.alias).filter(cmup=0).update(cmup=F("prix_achat"))
    Document.objects.using(schema_editor.connection.alias).filter(depot__isnull=True).exclude(
        type_document__in=["DEVIS", "COMMANDE", "ACHAT_COMMANDE"]).update(depot=depot)
    MouvementStock.objects.using(schema_editor.connection.alias).filter(depot__isnull=True).update(depot=depot)


class Migration(migrations.Migration):
    dependencies = [("commercial", "0003_stocks_depots_documents_sage")]
    operations = [migrations.RunPython(reprendre, migrations.RunPython.noop)]
