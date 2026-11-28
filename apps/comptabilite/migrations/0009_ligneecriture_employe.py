import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comptabilite", "0008_previsions_tresorerie"),
        ("personnel", "0003_employe_uid_site_origine"),
    ]

    operations = [
        migrations.AddField(
            model_name="ligneecriture",
            name="employe",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="lignes_ecriture",
                to="personnel.employe",
                verbose_name="Employé",
            ),
        ),
    ]
