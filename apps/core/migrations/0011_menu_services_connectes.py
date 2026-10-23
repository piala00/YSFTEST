"""Menu « Services connectés » (ancien code traitement.sage_connect) : les droits réglés gardent leur entrée."""
from django.db import migrations

RENOMMAGES = {
    "traitement.sage_connect": "traitement.services_connectes",
    "traitement.sage_connect.societe": "traitement.services_connectes.societe",
    "traitement.sage_connect.transmission": "traitement.services_connectes.transmission",
    "traitement.sage_connect.reception": "traitement.services_connectes.reception",
}


def renommer(apps, schema_editor, sens=1):
    DroitAcces = apps.get_model("core", "DroitAcces")
    for ancien, nouveau in RENOMMAGES.items():
        if sens < 0:
            ancien, nouveau = nouveau, ancien
        DroitAcces.objects.filter(module="commercial", code=ancien).update(code=nouveau)


class Migration(migrations.Migration):
    dependencies = [("core", "0010_droits_menu_fichier_comptabilite")]
    operations = [migrations.RunPython(renommer, lambda a, s: renommer(a, s, -1))]
