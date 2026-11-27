import uuid

from django.db import migrations, models


def remplir_identifiants(apps, schema_editor):
    Employe = apps.get_model("personnel", "Employe")
    alias = schema_editor.connection.alias
    identifiants = list(
        Employe.objects.using(alias).filter(uid__isnull=True).values_list("pk", flat=True)
    )
    for identifiant in identifiants:
        Employe.objects.using(alias).filter(pk=identifiant).update(uid=uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ("personnel", "0002_exploitation"),
    ]

    operations = [
        migrations.AddField(
            model_name="employe",
            name="uid",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name="employe",
            name="site_origine",
            field=models.CharField(blank=True, default="", editable=False, max_length=10),
        ),
        migrations.RunPython(remplir_identifiants, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="employe",
            name="uid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
