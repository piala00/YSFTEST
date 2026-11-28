"""Publication des faits de ce site dans le journal sortant (même transaction que l'opération)."""
import contextvars
from contextlib import contextmanager

from django.db import transaction

_import = contextvars.ContextVar("echanges_import", default=False)
_site_local_cache = contextvars.ContextVar("echanges_site_local_cache", default=None)


@contextmanager
def import_en_cours():
    """Pendant l'intégration d'un lot : les copies reçues ne sont pas republiées."""
    jeton = _import.set(True)
    try:
        yield
    finally:
        _import.reset(jeton)


def en_import():
    return _import.get()


@contextmanager
def hors_import():
    """Fait propre à ce site, créé pendant l'intégration d'un lot (ex. écriture de clôture d'un tronçon) : il est publié."""
    jeton = _import.set(False)
    try:
        yield
    finally:
        _import.reset(jeton)


@contextmanager
def cache_site_local():
    """Réutilise la gare locale pendant une opération composée sans cache global périmé."""
    cache = _site_local_cache.get()
    if cache is not None:
        yield
        return
    jeton = _site_local_cache.set({})
    try:
        yield
    finally:
        _site_local_cache.reset(jeton)


def site_local(using='default'):
    cache = _site_local_cache.get()
    if cache is not None and using in cache:
        return cache[using]
    from apps.core.models import Agence

    site = Agence.objects.using(using).filter(locale=True, uid__isnull=False).first()
    if cache is not None:
        cache[using] = site
    return site


def _sequence_suivante(using='default'):
    from apps.core.models import Sequence

    seq, _ = Sequence.objects.using(using).select_for_update().get_or_create(code="ECHANGES", annee=0)
    seq.dernier_numero += 1
    seq.save(using=using,update_fields=["dernier_numero"])
    return seq.dernier_numero


def publier(type_, objet_uid, payload, operation="ENREGISTRE", date_metier=None, auteur="", using='default'):
    if en_import() or site_local(using=using) is None:
        return None
    from .models import Evenement

    with transaction.atomic(using=using):
        revision = Evenement.objects.using(using).filter(type=type_, objet_uid=objet_uid).count() + 1
        return Evenement.objects.using(using).create(sequence=_sequence_suivante(using=using), type=type_, objet_uid=objet_uid, revision=revision,
                                        operation=operation, date_metier=date_metier, auteur=str(auteur or "")[:150],
                                        payload=payload)


def publier_ecriture(ecriture):
    """Écriture validée de ce dossier (pas une copie reçue d'un autre site)."""
    if ecriture.site_origine or en_import():
        return
    from . import contrats

    publier("ecriture", ecriture.uid, contrats.ecriture(ecriture), "VALIDE", ecriture.date, ecriture.cree_par or "",
            using=ecriture._state.db or 'default')


def publier_objet(objet, operation="ENREGISTRE"):
    """Gare, ligne, véhicule, chauffeur, départ, billet, colis, dépense : seulement ceux créés dans ce dossier."""
    if getattr(objet, "site_origine", "") or en_import():
        return
    from . import contrats

    type_, payload, date_metier, auteur = contrats.serialiser(objet)
    publier(type_, objet.uid, payload, operation, date_metier, auteur)
