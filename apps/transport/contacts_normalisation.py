"""Normalisation des coordonnées du guichet, sans dépendance au serveur."""
import re
import unicodedata


def telephone_normalise(valeur):
    texte = (valeur or "").strip()
    if not texte or re.search(r"[^0-9+\s().-]", texte):
        return ""
    texte = re.sub(r"[\s().-]", "", texte)
    if texte.startswith("00"):
        texte = "+" + texte[2:]
    international = texte.startswith("+")
    chiffres = texte[1:] if international else texte
    if not re.fullmatch(r"[0-9]{7,15}", chiffres):
        return ""
    if international:
        return "+" + chiffres
    if len(chiffres) == 12 and chiffres.startswith("237"):
        return "+" + chiffres
    if len(chiffres) == 9 and chiffres[0] in "26":
        return "+237" + chiffres
    # Ne pas attribuer arbitrairement un autre pays aux numéros ambigus.
    return chiffres


def nom_normalise(valeur):
    nom = "".join(c for c in unicodedata.normalize("NFKD", valeur or "").casefold()
                  if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() else " " for c in nom).split())[:240]
