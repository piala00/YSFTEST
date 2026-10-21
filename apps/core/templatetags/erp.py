from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def montant(value, decimales=0):
    """Formate un montant à la française : 1 234 567 (espaces insécables)."""
    if value in (None, ""):
        return ""
    try:
        value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    texte = f"{value:,.{int(decimales)}f}".replace(",", " ").replace(".", ",")
    return texte


@register.filter
def montant_ou_vide(value):
    if not value:
        return ""
    return montant(value)


@register.filter
def absolu(value):
    try:
        return abs(value)
    except TypeError:
        return value
