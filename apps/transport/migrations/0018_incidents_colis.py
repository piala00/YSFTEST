import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('transport', '0017_coordonnees_guichet'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='IncidentColis', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('uid', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
        ('colis', models.ForeignKey('transport.Colis', on_delete=models.PROTECT, related_name='incidents_suivi')),
        ('nature', models.CharField(max_length=10, choices=[('PERDU', 'Colis perdu'), ('ENDOMMAGE', 'Colis endommagé'), ('SANS_TRACE', 'Colis sans trace : recherche en cours')])),
        ('lieu', models.CharField(max_length=120)),
        ('description', models.CharField(max_length=250)),
        ('declare_par', models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')),
        ('declare_le', models.DateTimeField(auto_now_add=True)),
        ('resolu', models.BooleanField(default=False)),
        ('resolution', models.CharField(max_length=250, blank=True)),
        ('resolu_le', models.DateTimeField(null=True, blank=True)),
        ('resolu_par', models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')),
        ('montant_autorise', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
        ('autorise_par', models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')),
        ('compte_indemnite', models.ForeignKey('comptabilite.Compte', null=True, blank=True, on_delete=models.PROTECT, related_name='+')),
        ('ecriture', models.OneToOneField('comptabilite.Ecriture', null=True, blank=True, on_delete=models.PROTECT, related_name='+')),
        ('paye_par', models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'))], options={'ordering': ['-declare_le', '-pk'], 'permissions': [('autoriser_indemnite_colis', 'Autoriser une indemnisation de colis'), ('payer_indemnite_colis', 'Payer une indemnisation de colis')]})]
