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


@register.filter
def cellule(ligne, colonne):
    """Valeur formatée d'une colonne d'état : colonne = (clé, libellé, genre)."""
    cle, _, genre = colonne
    valeur = ligne.get(cle) if isinstance(ligne, dict) else None
    if valeur is None or valeur == "":
        return ""
    if genre == "montant":
        return montant(valeur)
    if genre == "quantite":
        return f"{Decimal(valeur).normalize():f}".replace(".", ",")
    if genre == "pourcent":
        return f"{Decimal(valeur):.1f} %".replace(".", ",")
    if genre == "date":
        return valeur.strftime("%d/%m/%Y")
    return valeur


@register.filter
def valeur(dictionnaire, cle):
    return dictionnaire.get(cle) if isinstance(dictionnaire, dict) else None
