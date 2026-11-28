"""Menu Fichier de la Comptabilité aligné sur le découpage S02 V12 : les droits réglés gardent leur entrée."""
from django.db import migrations

RENOMMAGES = {
    "fichier.societe": "fichier.parametres",
    "fichier.societe.identification": "fichier.parametres.identification.identification",
    "fichier.societe.exercices": "fichier.parametres.identification.exercices",
    "fichier.societe.comptes": "fichier.parametres.comptes",
    "fichier.societe.tiers": "fichier.parametres.tiers",
    "fichier.societe.taxes": "fichier.parametres.tva",
    "fichier.societe.analytique": "fichier.parametres.analytique",
    "fichier.societe.banques": "fichier.parametres.banque",
}


def renommer(apps, schema_editor, sens=1):
    DroitAcces = apps.get_model("core", "DroitAcces")
    for ancien, nouveau in RENOMMAGES.items():
        if sens < 0:
            ancien, nouveau = nouveau, ancien
        DroitAcces.objects.using(schema_editor.connection.alias).filter(module="comptabilite", code=ancien).update(code=nouveau)


class Migration(migrations.Migration):
    dependencies = [("core", "0009_acces_logiciels")]
    operations = [migrations.RunPython(renommer, lambda a, s: renommer(a, s, -1))]
