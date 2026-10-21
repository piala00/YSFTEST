from django.contrib import admin

from .models import Exercice, Sequence, Societe

admin.site.site_header = "ERP OHADA — Administration"
admin.site.register(Societe)
admin.site.register(Sequence)


@admin.register(Exercice)
class ExerciceAdmin(admin.ModelAdmin):
    list_display = ("code", "date_debut", "date_fin", "cloture")
