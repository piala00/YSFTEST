"""Publication automatique des fiches et opérations du transport, et des agences déclarées au siège."""
from django.db.models.signals import post_save

LIENS = {"ecriture", "ecriture_annulation", "ecriture_remboursement", "embarque", "embarque_le", "embarque_par",
         "embarquement_valide_le", "embarquement_valide_par", "ecriture_livraison", "ecriture_reversement", "ecriture_recettes",
         "sequence_integree", "derniere_reception"}          # rattachements et compteurs de réception : rien à publier


def _apres_enregistrement(sender, instance, created, update_fields=None, **kwargs):
    if update_fields and set(update_fields) <= LIENS:            # simple rattachement de l'écriture : déjà publié
        return
    from .publication import publier_objet, site_local

    if sender.__name__ == "Billet" and created:                 # publié par Billet.vendre, avec ses tronçons
        return
    if sender.__name__ == "Troncon":                            # un tronçon change : on republie son billet
        if created or instance.billet.site_origine:
            return
        instance = instance.billet
    if sender.__name__ == "Agence":
        local = site_local()
        if local is None or local.role != local.SIEGE or not instance.uid:
            return
    publier_objet(instance)


def connecter():
    from apps.core.models import Agence
    from apps.transport.models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, Troncon, Vehicule

    from apps.garage.models import OrdreReparation, PleinCarburant

    from apps.transport.models import DemandeDepense

    for modele in (Agence, Gare, Ligne, Vehicule, Chauffeur, Depart, Billet, Troncon, Colis, DepenseVehicule, PleinCarburant,
                   OrdreReparation, DemandeDepense):
        post_save.connect(_apres_enregistrement, sender=modele, dispatch_uid=f"echanges-{modele.__name__}")
