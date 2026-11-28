"""Sauvegarde chiffrée (anti-vol) : enveloppe AES-256-GCM autour de la sauvegarde JSON.

But (demandé par le propriétaire) : pouvoir sortir une sauvegarde complète du logiciel et des
données, **chiffrée automatiquement** et **protégée par un mot de passe**, transportable sur clé
USB. Une clé volée ou copiée est **inexploitable sans le mot de passe** ; la restauration exige ce
mot de passe (déchiffrement), donc reste verrouillée par les identifiants de l'administrateur.

Format du fichier ``.erpcoffre`` : ``MAGIC (10 o) | sel scrypt (16 o) | nonce (12 o) | jeton
AES-GCM``. La dérivation de clé (scrypt) rend l'essai de mots de passe coûteux ; GCM détecte toute
altération. Le contenu en clair reste la sauvegarde JSON existante (apps.core.sauvegarde), donc la
restauration réutilise les mêmes contrôles d'intégrité et de périmètre.
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import os

MAGIC = b"ERPCOFFRE1"
FORMAT = "erp-ohada-coffre"
SEL_OCTETS = 16
NONCE_OCTETS = 12
# Paramètres scrypt : coûteux pour l'attaque par dictionnaire, tenables sur un poste bureautique.
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1


def _derive_cle(mot_de_passe, sel):
    kdf = Scrypt(salt=sel, length=32, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(mot_de_passe.encode("utf-8"))


def chiffrer(texte, mot_de_passe):
    """Chiffre le texte de la sauvegarde ; renvoie les octets du fichier .erpcoffre."""
    if not mot_de_passe:
        raise ValueError("Un mot de passe est obligatoire pour chiffrer la sauvegarde.")
    sel = os.urandom(SEL_OCTETS)
    nonce = os.urandom(NONCE_OCTETS)
    cle = _derive_cle(mot_de_passe, sel)
    # MAGIC sert aussi de données authentifiées associées (il ne peut être trafiqué sans rejet).
    jeton = AESGCM(cle).encrypt(nonce, texte.encode("utf-8"), MAGIC)
    return MAGIC + sel + nonce + jeton


def est_coffre(octets):
    """Vrai si ces octets ressemblent à un fichier de sauvegarde chiffrée de l'ERP."""
    return isinstance(octets, (bytes, bytearray)) and bytes(octets[:len(MAGIC)]) == MAGIC


def dechiffrer(octets, mot_de_passe):
    """Déchiffre un fichier .erpcoffre ; renvoie le texte JSON de la sauvegarde.

    Lève ``ValueError`` si le fichier n'est pas un coffre, si le mot de passe est incorrect ou si
    le contenu a été altéré (aucune de ces causes n'est distinguée, pour ne rien révéler).
    """
    octets = bytes(octets)
    if not est_coffre(octets):
        raise ValueError("Ce fichier n'est pas une sauvegarde chiffrée de l'ERP OHADA.")
    corps = octets[len(MAGIC):]
    if len(corps) < SEL_OCTETS + NONCE_OCTETS + 16:   # +16 : étiquette GCM minimale
        raise ValueError("Sauvegarde chiffrée incomplète ou corrompue.")
    sel = corps[:SEL_OCTETS]
    nonce = corps[SEL_OCTETS:SEL_OCTETS + NONCE_OCTETS]
    jeton = corps[SEL_OCTETS + NONCE_OCTETS:]
    cle = _derive_cle(mot_de_passe or "", sel)
    try:
        clair = AESGCM(cle).decrypt(nonce, jeton, MAGIC)
    except Exception:
        raise ValueError("Mot de passe incorrect ou fichier altéré : restauration impossible.")
    return clair.decode("utf-8")
