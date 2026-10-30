"""Incidents des envois : signalement opérationnel distinct du droit à indemnisation et du décaissement."""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class IncidentColis(models.Model):
    PERDU, ENDOMMAGE, SANS_TRACE = 'PERDU', 'ENDOMMAGE', 'SANS_TRACE'
    NATURES = [(PERDU, 'Colis perdu'), (ENDOMMAGE, 'Colis endommagé'), (SANS_TRACE, 'Colis sans trace : recherche en cours')]
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    colis = models.ForeignKey('transport.Colis', on_delete=models.PROTECT, related_name='incidents_suivi')
    nature = models.CharField(max_length=10, choices=NATURES)
    lieu = models.CharField(max_length=120)
    description = models.CharField(max_length=250)
    declare_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    declare_le = models.DateTimeField(auto_now_add=True)
    resolu = models.BooleanField(default=False)
    resolution = models.CharField(max_length=250, blank=True)
    resolu_le = models.DateTimeField(null=True, blank=True)
    resolu_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    montant_autorise = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    autorise_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    compte_indemnite = models.ForeignKey('comptabilite.Compte', null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    ecriture = models.OneToOneField('comptabilite.Ecriture', null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    paye_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-declare_le', '-pk']
        permissions = [('autoriser_indemnite_colis', 'Autoriser une indemnisation de colis'),
                       ('payer_indemnite_colis', 'Payer une indemnisation de colis')]

    @classmethod
    @transaction.atomic
    def declarer(cls, colis, nature, lieu, description, utilisateur):
        from .models import Colis, _proprietaire
        colis = Colis.objects.select_for_update().get(pk=colis.pk)
        _proprietaire(colis, f"L'envoi {colis.numero}")
        if colis.statut in (Colis.LIVRE, Colis.ANNULE):
            raise ValidationError("Ce colis est livré ou annulé : la recherche d'acheminement n'est plus ouverte.")
        if nature not in dict(cls.NATURES) or not lieu.strip() or not description.strip() or len(lieu)>120 or len(description)>250:
            raise ValidationError("Indiquez la nature, le dernier lieu connu et les constatations.")
        precedent = cls.objects.filter(colis=colis, resolu=False).first()
        if precedent:
            if precedent.nature == nature and precedent.lieu == lieu.strip() and precedent.description == description.strip():
                return precedent
            raise ValidationError("Un incident est déjà en cours sur ce colis. Complétez sa résolution avant un nouveau signalement.")
        return cls.objects.create(colis=colis, nature=nature, lieu=lieu.strip(), description=description.strip(), declare_par=utilisateur)

    @transaction.atomic
    def resoudre(self, motif, utilisateur):
        incident = type(self).objects.select_for_update().get(pk=self.pk)
        if not motif.strip() or len(motif)>250:
            raise ValidationError("Indiquez comment le colis a été retrouvé ou le dommage traité.")
        if incident.resolu:
            return incident
        incident.resolu, incident.resolution = True, motif.strip()
        incident.resolu_par, incident.resolu_le = utilisateur, timezone.now()
        incident.save(update_fields=['resolu', 'resolution', 'resolu_par', 'resolu_le'])
        return incident

    @transaction.atomic
    def autoriser(self, montant, compte, utilisateur):
        incident = type(self).objects.select_for_update().get(pk=self.pk)
        if not utilisateur.has_perm('transport.autoriser_indemnite_colis'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        montant = Decimal(montant)
        if not montant.is_finite() or montant <= 0 or montant != montant.quantize(Decimal('1')):
            raise ValidationError("Indiquez un montant entier positif expressément autorisé.")
        if not compte.numero.startswith('6'):
            raise ValidationError("Choisissez le compte de charge d'indemnisation validé par votre comptable.")
        if incident.ecriture_id:
            raise ValidationError("Cette indemnisation est déjà payée.")
        incident.montant_autorise, incident.compte_indemnite, incident.autorise_par = montant, compte, utilisateur
        incident.save(update_fields=['montant_autorise', 'compte_indemnite', 'autorise_par'])
        return incident

    @transaction.atomic
    def payer(self, caisse, utilisateur):
        from apps.comptabilite.services import creer_ecriture
        from .models_caisse import solde_tresorerie
        if not utilisateur.has_perm('transport.payer_indemnite_colis'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        incident = type(self).objects.select_for_update().get(pk=self.pk)
        if incident.ecriture_id:
            return incident
        if not incident.autorise_par_id or not incident.compte_indemnite_id or incident.montant_autorise <= 0:
            raise ValidationError("L'indemnisation doit être autorisée avant son paiement.")
        if not caisse.compte_tresorerie_id or solde_tresorerie(caisse.compte_tresorerie) < incident.montant_autorise:
            raise ValidationError("La caisse ne dispose pas du montant de l'indemnisation.")
        c, montant = incident.colis, incident.montant_autorise
        debit = {'compte': incident.compte_indemnite, 'debit': montant, 'section': c.gare_depart.section}
        if c.depart_id:
            debit['vehicule'] = c.depart.vehicule
        incident.ecriture = creer_ecriture(caisse, timezone.localdate(), f"Indemnisation {c.numero} : {incident.get_nature_display()}",
            [debit, {'compte': caisse.compte_tresorerie, 'credit': montant}], reference=str(incident.uid), origine=c.numero)
        incident.paye_par = utilisateur
        incident.save(update_fields=['ecriture', 'paye_par'])
        return incident
