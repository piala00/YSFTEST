"""Sauvegarde de fin de journée d'une agence, remise à la direction (siège).

L'agence produit une sauvegarde complète (même format que Fichier › Sauvegarde) et la
remet à la direction par l'Import/Export : si une boîte aux lettres est configurée, le
fichier chiffré est déposé dans la boîte du siège ; sinon il est téléchargé pour être
transmis par le canal habituel (clé USB, WhatsApp…). La direction récupère et déchiffre
chaque sauvegarde reçue pour l'archiver (jamais de restauration automatique).
"""
import datetime

from apps.core import sauvegarde as _sauvegarde
from apps.core.models import Agence

from . import lots
from .models import SauvegardeJournaliere
from .publication import site_local
from .synchro import boite_configuree, chiffrer, dechiffrer

SUFFIXE = ".sauvegarde.chiffre"


def _siege():
    return Agence.objects.filter(role=Agence.SIEGE, uid__isnull=False).first()


def nom_fichier(code, jour=None):
    jour = jour or datetime.date.today()
    return f"sauvegarde-{code}-{jour:%Y%m%d}"


def produire():
    """Contenu texte de la sauvegarde complète et nom de fichier lisible."""
    local = site_local()
    code = local.code if local else "local"
    texte = _sauvegarde.sauvegarder()
    return texte, f"{nom_fichier(code)}.json"


def remettre(utilisateur, jour=None):
    """Produit la sauvegarde du jour et la remet à la direction.
    Retourne (enregistrement, texte, nom_telechargement)."""
    jour = jour or datetime.date.today()
    local = site_local()
    if local is None:
        raise ValueError("ce poste n'est pas encore déclaré comme agence ou siège (menu Échanges).")
    texte = _sauvegarde.sauvegarder()
    octets = texte.encode("utf-8")
    nom_dl = f"{nom_fichier(local.code, jour)}.json"
    siege = _siege()
    moyen = SauvegardeJournaliere.TELECHARGEMENT
    destination = ""
    if siege is not None and siege.pk != local.pk:
        destination = siege.code
        boite = boite_configuree()
        if boite is not None:
            cle, _source = lots.cle_du_lien(local, siege)
            chiffre = chiffrer(octets, cle, local.code, siege.code)
            boite.deposer(siege.code, f"{nom_fichier(local.code, jour)}{SUFFIXE}", chiffre)
            moyen = SauvegardeJournaliere.BOITE
    enreg = SauvegardeJournaliere.objects.create(
        date=jour, site_code=local.code, destination_code=destination, taille=len(octets),
        nom_fichier=nom_dl, moyen=moyen,
        auteur=utilisateur.get_username() if utilisateur and getattr(utilisateur, "pk", None) else "")
    return enreg, texte, nom_dl


# ---------------------------------------------------------------- Côté direction (siège)
def _agence_du_nom(nom):
    reste = nom[len("sauvegarde-"):-len(SUFFIXE)] if nom.startswith("sauvegarde-") and nom.endswith(SUFFIXE) else ""
    code, _, jour = reste.rpartition("-")
    return code, jour


def recues():
    """Liste des sauvegardes d'agences déposées dans la boîte du siège (pour archivage)."""
    local = site_local()
    boite = boite_configuree()
    if local is None or local.role != Agence.SIEGE or boite is None:
        return []
    out = []
    for nom in boite.lister_sauvegardes(local.code):
        code, jour = _agence_du_nom(nom)
        agence = Agence.objects.filter(code=code).first()
        try:
            date = datetime.datetime.strptime(jour, "%Y%m%d").date()
        except ValueError:
            date = None
        out.append({"nom": nom, "agence_code": code, "agence": agence, "date": date})
    return out


def recuperer(nom, utilisateur=None):
    """Déchiffre une sauvegarde reçue et retourne (contenu_texte, nom_telechargement)."""
    local = site_local()
    boite = boite_configuree()
    if local is None or local.role != Agence.SIEGE or boite is None:
        raise ValueError("réservé au siège, avec une boîte aux lettres configurée.")
    code, _jour = _agence_du_nom(nom)
    agence = Agence.objects.filter(code=code).first()
    if agence is None:
        raise ValueError(f"agence inconnue pour {nom}.")
    cle, _ = lots.cle_du_lien(local, agence)
    clair = dechiffrer(boite.lire(local.code, nom), cle, agence.code, local.code)
    return clair.decode("utf-8"), nom.replace(SUFFIXE, ".json")
