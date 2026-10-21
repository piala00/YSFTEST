from django.contrib import admin

from .models import Compte, Ecriture, Journal, LigneEcriture


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ("numero", "intitule", "lettrable", "actif")
    search_fields = ("numero", "intitule")


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("code", "intitule", "type_journal", "compte_tresorerie")


class LigneEcritureInline(admin.TabularInline):
    model = LigneEcriture
    extra = 0
    autocomplete_fields = ("compte",)


@admin.register(Ecriture)
class EcritureAdmin(admin.ModelAdmin):
    list_display = ("numero", "date", "journal", "libelle", "statut")
    list_filter = ("journal", "statut", "exercice")
    search_fields = ("numero", "libelle", "reference")
    inlines = [LigneEcritureInline]
