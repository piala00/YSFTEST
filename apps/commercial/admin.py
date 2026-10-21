from django.contrib import admin

from .models import Article, Document, FamilleArticle, Imputation, LigneDocument, MouvementStock, Reglement, Tiers


@admin.register(Tiers)
class TiersAdmin(admin.ModelAdmin):
    list_display = ("code", "nom", "type_tiers", "ville", "telephone", "actif")
    list_filter = ("type_tiers", "actif")
    search_fields = ("code", "nom", "niu")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("reference", "designation", "nature", "prix_vente", "stock", "actif")
    list_filter = ("nature", "famille", "actif")
    search_fields = ("reference", "designation")


class LigneDocumentInline(admin.TabularInline):
    model = LigneDocument
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("numero", "type_document", "date", "tiers", "total_ttc", "statut")
    list_filter = ("type_document", "statut")
    search_fields = ("numero", "tiers__nom")
    inlines = [LigneDocumentInline]


admin.site.register(FamilleArticle)
admin.site.register(Reglement)
admin.site.register(Imputation)
admin.site.register(MouvementStock)
