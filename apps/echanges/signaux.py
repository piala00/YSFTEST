"""Publication automatique des fiches et opérations du transport, et des agences déclarées au siège."""
from django.db.models.signals import post_save

LIENS = {"ecriture", "ecriture_annulation", "ecriture_livraison", "ecriture_reversement"}


def _apres_enregistrement(sender, instance, created, update_fields=None, **kwargs):
    if update_fields and set(update_fields) <= LIENS:            # simple rattachement de l'écriture : déjà publié
        return
    from .publication import publier_objet, site_local

    if sender.__name__ == "Agence":
        local = site_local()
        if local is None or local.role != local.SIEGE or not instance.uid:
            return
    publier_objet(instance)


def connecter():
    from apps.core.models import Agence
    from apps.transport.models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, Vehicule

    for modele in (Agence, Gare, Ligne, Vehicule, Chauffeur, Depart, Billet, Colis, DepenseVehicule):
        post_save.connect(_apres_enregistrement, sender=modele, dispatch_uid=f"echanges-{modele.__name__}")
