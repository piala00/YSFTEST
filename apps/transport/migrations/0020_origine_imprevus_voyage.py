from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("transport", "0019_origine_incidents_colis")]
    operations = [
        migrations.AddField(model_name="incident", name="site_origine",
                            field=models.CharField("Site d'origine", max_length=10, blank=True, editable=False)),
        migrations.AddField(model_name="incident", name="trace_origine",
                            field=models.JSONField(default=dict, blank=True, editable=False)),
    ]
