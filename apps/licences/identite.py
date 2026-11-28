"""Lecture des seules identités publiques et contrôle des distributions, sans Django."""
import base64
import hashlib


def lire_publique(contenu):
    """Ancien texte base64 ou parametres.dat ; jamais un coffre privé ni une licence."""
    if not isinstance(contenu, bytes) or len(contenu) > 8192:
        raise ValueError("Fichier public absent ou trop volumineux.")
    if contenu.startswith(b"ERPID\x01") and len(contenu) == 38:
        return contenu[6:]
    try:
        lignes = [x.strip() for x in contenu.decode("utf-8-sig").splitlines()
                  if x.strip() and not x.lstrip().startswith("#")]
        if len(lignes) != 1:
            raise ValueError
        brut = base64.b64decode(lignes[0], validate=True)
        if len(brut) != 32:
            raise ValueError
        return brut
    except (ValueError, UnicodeError):
        raise ValueError("Choisissez uniquement la clé publique de vérification (parametres.dat ou ancien texte).") from None


def empreinte(brut):
    return hashlib.sha256(brut).hexdigest().upper()


def verifier_distribution(cles, *, version_essai=False):
    """Une compilation commerciale sans identité est une erreur, jamais un essai implicite."""
    if not isinstance(cles, (list, tuple)):
        raise ValueError("Liste d'identités publiques invalide.")
    identites = [lire_publique(c.encode("ascii")) for c in cles]
    if not identites and not version_essai:
        raise ValueError("Compilation commerciale refusée : l'identité publique autorisée n'est pas intégrée.")
    if identites and version_essai:
        raise ValueError("Une identité est intégrée : ne pas présenter cette compilation comme un essai sans éditeur.")
    return {"mode": "personnalisee" if identites else "essai-sans-editeur",
            "empreintes_sha256": [empreinte(c) for c in identites]}
