"""Transition depuis l'ancien logiciel : copie synchronisée, puis bascule.

Pendant la transition (mode « copie synchronisée »), on saisit dans l'ancien logiciel et l'ERP en reçoit les données
à chaque synchronisation. Pour éviter les doubles saisies, l'ERP refuse alors les opérations qui créent des pièces,
des règlements, des écritures ou des mouvements de stock — sauf pendant la synchronisation elle-même. Après la
bascule, la synchronisation est arrêtée définitivement et l'ERP devient le seul logiciel de saisie.
"""
import contextvars
from contextlib import contextmanager

from django.core.exceptions import ValidationError

_en_cours = contextvars.ContextVar("synchronisation_en_cours", default=False)


@contextmanager
def synchronisation():
    """Contexte de la synchronisation : seules ses écritures sont admises en mode copie synchronisée."""
    jeton = _en_cours.set(True)
    try:
        yield
    finally:
        _en_cours.reset(jeton)


def copie_synchronisee():
    from .models import Societe

    return Societe.objects.filter(source_mode=Societe.SYNCHRO_MIROIR).exists()


def verifier_saisie(operation="cette opération"):
    """Refuse une saisie dans l'ERP tant que la bascule n'est pas faite (copie synchronisée)."""
    if not _en_cours.get() and copie_synchronisee():
        raise ValidationError(
            f"Synchronisation en cours avec l'ancien logiciel : {operation} se fait encore dans l'ancien logiciel. "
            "L'ERP en reçoit une copie à chaque synchronisation ; la saisie s'ouvrira ici à la bascule "
            "(Fichier › Reprise d'un dossier existant).")
