"""Décider sur une pièce persistée relue sous verrou, dans la transaction appelante."""
from django.core.exceptions import ValidationError


def relire_piece(objet, quoi, requis=False):
    from apps.core.synchronisation import verifier_saisie
    from apps.transport.models import _proprietaire

    if objet._state.db not in (None, "default"):
        raise ValidationError("Cette copie du dossier est réservée à la lecture. Ouvrez le dossier de saisie.")
    verifier_saisie("la saisie du garage")
    if objet.pk is None:
        if requis:
            raise ValidationError("Enregistrez la pièce avant cette opération.")
    else:
        try:
            objet.refresh_from_db(from_queryset=type(objet).objects.select_for_update())
        except type(objet).DoesNotExist:
            raise ValidationError(f"{quoi} n'existe plus. Actualisez la liste.") from None
    if hasattr(objet, "site_origine"):
        _proprietaire(objet, f"{quoi} {objet.numero}")
