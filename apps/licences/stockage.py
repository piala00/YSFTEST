"""Codes locaux authentifiés et liés à la machine ; protection Windows DPAPI en complément.

Le chiffrement n'autorise aucune licence. La signature de l'éditeur et l'empreinte
matérielle restent vérifiées séparément. Aucun coffre privé n'est accepté ici.
"""
import base64
import ctypes
import hashlib
import os

PREFIXE = "ERPS1:"
DOMAINE = b"ERP-OHADA/installation/stockage/v1"


def _dpapi(brut, proteger):
    if os.name != "nt":
        raise ValueError("Ce code protégé appartient à un poste Windows.")
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    tampon = (ctypes.c_ubyte * len(brut)).from_buffer_copy(brut)
    entree, sortie = Blob(len(brut), tampon), Blob()
    api = ctypes.WinDLL("crypt32", use_last_error=True)
    noyau = ctypes.WinDLL("kernel32", use_last_error=True)
    noyau.LocalFree.argtypes = [ctypes.c_void_p]
    noyau.LocalFree.restype = ctypes.c_void_p
    fonction = api.CryptProtectData if proteger else api.CryptUnprotectData
    fonction.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fonction.restype = wintypes.BOOL
    # Sans interaction ; la portée machine permet le service Windows et le mode fenêtre.
    if not fonction(ctypes.byref(entree), None, None, None, None, 5 if proteger else 1, ctypes.byref(sortie)):
        raise ValueError("La protection Windows de ce poste n'est pas disponible.")
    try:
        return ctypes.string_at(sortie.pbData, sortie.cbData)
    finally:
        noyau.LocalFree(sortie.pbData)


def _cle(secret, machine):
    if not secret or not machine:
        raise ValueError("Identité locale absente : impossible de protéger le code.")
    return hashlib.sha256(DOMAINE + b"\0" + secret.encode() + b"\0" + machine.encode()).digest()


def sceller(texte, secret, machine):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    chiffre = nonce + AESGCM(_cle(secret, machine)).encrypt(nonce, texte.encode("utf-8"), DOMAINE)
    mode = b"W" if os.name == "nt" else b"A"
    if mode == b"W":
        chiffre = _dpapi(chiffre, True)
    return PREFIXE + base64.b64encode(mode + chiffre).decode("ascii")


def ouvrir(texte, secret, machine):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not texte.startswith(PREFIXE):
        raise ValueError("Ce contenu n'est pas un code local protégé.")
    try:
        brut = base64.b64decode(texte[len(PREFIXE):], validate=True)
        if brut[:1] == b"W":
            brut = _dpapi(brut[1:], False)
        elif brut[:1] == b"A":
            brut = brut[1:]
        else:
            raise ValueError
        if len(brut) < 28:
            raise ValueError
        return AESGCM(_cle(secret, machine)).decrypt(brut[:12], brut[12:], DOMAINE).decode("utf-8")
    except (ValueError, InvalidTag, UnicodeDecodeError):
        raise ValueError("Code illisible, modifié ou provenant d'une autre installation.") from None
