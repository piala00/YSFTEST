from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('partenaires', '0006_libelle_compte_du_vehicule')]
    operations = [
        migrations.AddField(model_name='contratpartenaire', name='assiette_commission', field=models.CharField(
            choices=[('A_CONFIRMER', 'À confirmer avec le propriétaire du véhicule'), ('RECETTES', 'Recettes du véhicule'),
                     ('MARGE', 'Résultat : recettes moins dépenses contractuelles (signé)')],
            default='RECETTES', max_length=12, verbose_name='Base du pourcentage société',
            help_text='Les contrats historiques conservent leur calcul. Pour un nouveau contrat, confirmer explicitement la base.')),
        migrations.AlterField(model_name='contratpartenaire', name='taux_commission', field=models.DecimalField(
            decimal_places=2, default=0, max_digits=5, verbose_name='Pourcentage de la société (%)')),
        migrations.AlterField(model_name='contratpartenaire', name='partenaire', field=models.ForeignKey(
            to='commercial.tiers', on_delete=django.db.models.deletion.PROTECT, related_name='contrats_partenaire',
            help_text='Tiers propriétaire de véhicule, sans participation au capital ; compte auxiliaire propriétaire séparé')),
    ]
