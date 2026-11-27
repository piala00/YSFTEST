# Generated for the transport sales-channel analytical axis.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transport", "0022_reversement_recette_caisse"),
    ]

    operations = [
        migrations.AddField(
            model_name="billet",
            name="canal_vente",
            field=models.CharField(
                choices=[("GUICHET", "Guichet"), ("WEB", "Web"), ("APP", "Application mobile"), ("REVENDEUR", "Revendeur")],
                default="GUICHET",
                max_length=12,
                verbose_name="Canal de vente",
            ),
        ),
        migrations.AddField(
            model_name="colis",
            name="canal_vente",
            field=models.CharField(
                choices=[("GUICHET", "Guichet"), ("WEB", "Web"), ("APP", "Application mobile"), ("REVENDEUR", "Revendeur")],
                default="GUICHET",
                max_length=12,
                verbose_name="Canal de vente",
            ),
        ),
    ]
