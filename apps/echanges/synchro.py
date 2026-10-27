"""Synchronisation automatique des sites par une boîte aux lettres : chaque site y dépose les lots destinés aux autres
et retire les siens, dès qu'il y a une connexion. Les lots restent ceux des échanges par fichiers (signés, intégrés une
seule fois, dans n'importe quel ordre) ; ils sont en plus CHIFFRÉS avant de partir : la boîte ne peut pas les lire.

Deux boîtes possibles :
  - DossierPartage : un dossier commun (réseau, disque synchronisé, clé USB) ; un sous-dossier par site ;
  - RelaisHTTP : le relais Internet (apps.relais) sur un petit serveur en ligne, avec un jeton par site.

Chiffrement : AES-256-GCM ; clé tirée (HKDF-SHA256) de la clé d'échange que l'agence et le siège partagent déjà ;
les codes de l'expéditeur et du destinataire sont authentifiés avec le contenu.
"""
import json
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction
from django.db.models import Max

from . import lots
from .publication import site_local

ENTETE = b"ERP-OHADA-CHIFFRE-V1\x00"
MODELE_NOM = re.compile(r"^(?P<lot>ERP-LOT-(?P<source>[A-Z0-9_-]+?)-vers-(?P<destination>[A-Z0-9_-]+?)-\d{8}-\d{4}-\d+-\d+)"
                        r"(?:-[0-9a-f]{8})?\.erpx\.chiffre$")
LOCAUX = {"localhost", "127.0.0.1", "::1"}


# ---------------------------------------------------------------- Chiffrement
def _cle_aes(cle_echange):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    return HKDF(algorithm=hashes.SHA256(), length=32, salt=b"erp-ohada-boite-aux-lettres",
                info=b"chiffrement des lots v1").derive(cle_echange.encode("utf-8"))


def chiffrer(octets, cle_echange, source, destination):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    return ENTETE + nonce + AESGCM(_cle_aes(cle_echange)).encrypt(nonce, octets, f"{source}>{destination}".encode())


def dechiffrer(octets, cle_echange, source, destination):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not octets.startswith(ENTETE) or len(octets) < len(ENTETE) + 28:
        raise lots.LotInvalide("ce n'est pas un lot chiffré de l'ERP")
    corps = octets[len(ENTETE):]
    try:
        return AESGCM(_cle_aes(cle_echange)).decrypt(corps[:12], corps[12:], f"{source}>{destination}".encode())
    except InvalidTag:
        raise lots.LotInvalide("lot chiffré illisible : mauvaise clé, autre site ou fichier abîmé")


# ---------------------------------------------------------------- Boîtes aux lettres
class DossierPartage:
    """Un sous-dossier par destinataire ; écriture en deux temps (pas de fichier à moitié copié lu par l'autre site)."""

    def __init__(self, racine):
        self.racine = Path(racine)

    def deposer(self, destination, nom, octets):
        dossier = self.racine / destination
        dossier.mkdir(parents=True, exist_ok=True)
        final = dossier / nom
        if final.exists():
            raise FileExistsError(f"{nom} existe déjà dans la boîte : jamais écrasé")
        provisoire = dossier / f".{nom}.{secrets.token_hex(4)}.part"
        provisoire.write_bytes(octets)
        try:
            os.link(provisoire, final)                            # échoue si le nom a été pris entre-temps
        finally:
            provisoire.unlink(missing_ok=True)

    def lister(self, code):
        dossier = self.racine / code
        return sorted(f.name for f in dossier.glob("*.erpx.chiffre")) if dossier.exists() else []

    def lire(self, code, nom):
        return (self.racine / code / nom).read_bytes()

    def retirer(self, code, nom):
        (self.racine / code / nom).unlink(missing_ok=True)

    def __str__(self):
        return f"dossier partagé {self.racine}"


class _SansRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None                                               # le jeton ne suit jamais une redirection


class RelaisHTTP:
    """Client du relais Internet : POST pour déposer, GET pour lister et lire, DELETE pour retirer.
    HTTPS obligatoire (certificat vérifié), sauf sur ce poste même (essais) ; jamais de redirection."""

    def __init__(self, url, jeton, delai=60):
        self.url, self.jeton, self.delai = url.rstrip("/"), jeton, delai

    def _appel(self, methode, chemin, octets=None, entetes=None):
        adresse = urllib.parse.urlsplit(self.url)
        if adresse.scheme != "https" and not (adresse.scheme == "http" and adresse.hostname in LOCAUX):
            raise ConnectionError("relais refusé : adresse en https:// obligatoire (le jeton ne part jamais en clair)")
        requete = urllib.request.Request(f"{self.url}/relais/v1/{chemin}", data=octets, method=methode,
                                         headers={"Authorization": f"Bearer {self.jeton}", **(entetes or {})})
        try:
            with urllib.request.build_opener(_SansRedirection).open(requete, timeout=self.delai) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            raise ConnectionError(f"relais : {exc.code} {(exc.read() or b'')[:200].decode('utf-8', 'replace')}")
        except (urllib.error.URLError, OSError) as exc:
            raise ConnectionError(f"relais injoignable : {exc}")

    def deposer(self, destination, nom, octets):
        self._appel("POST", f"boites/{destination}/", octets,
                    {"Content-Type": "application/octet-stream", "X-Nom-Lot": nom})

    def lister(self, code):
        return json.loads(self._appel("GET", f"boites/{code}/"))["lots"]

    def lire(self, code, nom):
        return self._appel("GET", f"boites/{code}/{urllib.parse.quote(nom)}")

    def retirer(self, code, nom):
        self._appel("DELETE", f"boites/{code}/{urllib.parse.quote(nom)}")

    def __str__(self):
        return f"relais {self.url}"


def boite_configuree():
    """Boîte d'après la configuration : ECHANGES_RELAIS_URL + ECHANGES_RELAIS_JETON, ou ECHANGES_DOSSIER_PARTAGE."""
    if os.environ.get("ECHANGES_RELAIS_URL"):
        return RelaisHTTP(os.environ["ECHANGES_RELAIS_URL"], os.environ.get("ECHANGES_RELAIS_JETON", ""))
    if os.environ.get("ECHANGES_DOSSIER_PARTAGE"):
        return DossierPartage(os.environ["ECHANGES_DOSSIER_PARTAGE"])
    return None


# ---------------------------------------------------------------- Synchronisation
@dataclass
class Bilan:
    envoyes: list = field(default_factory=list)
    recus: list = field(default_factory=list)
    erreurs: list = field(default_factory=list)

    def texte(self):
        parts = [f"{len(self.envoyes)} lot(s) envoyé(s)", f"{len(self.recus)} lot(s) reçu(s)"]
        if self.erreurs:
            parts.append(f"{len(self.erreurs)} problème(s) : " + " ; ".join(self.erreurs[:5]))
        return " · ".join(parts)


def destinataires(local):
    from apps.core.models import Agence

    if local.role == local.SIEGE:
        return list(Agence.objects.filter(role=Agence.AGENCE, actif=True, uid__isnull=False).exclude(cle_echange=""))
    return list(Agence.objects.filter(role=Agence.SIEGE, uid__isnull=False))


def a_envoyer(local, destination):
    """Y a-t-il des faits nouveaux pour ce destinataire ? (pas de lot vide toutes les cinq minutes)"""
    from .models import Evenement, LotEmis

    dernier = LotEmis.objects.filter(destination=destination).aggregate(m=Max("sequence_a"))["m"] or 0
    if Evenement.objects.filter(sequence__gt=dernier).exists():
        return True
    return local.role == local.SIEGE and bool(lots._a_relayer(destination))


def _recevoir(boite, local, bilan, utilisateur):
    from apps.core.models import Agence

    try:
        noms = boite.lister(local.code)
    except (ConnectionError, OSError) as exc:
        bilan.erreurs.append(f"réception : {exc}")
        return
    for nom in noms:
        m = MODELE_NOM.match(nom)
        source = Agence.objects.filter(code=m["source"], uid__isnull=False).first() if m else None
        if m is None or source is None or m["destination"] != local.code:
            bilan.erreurs.append(f"{nom} : fichier inattendu, laissé dans la boîte")
            continue
        try:
            cle, _ = lots.cle_du_lien(local, source)
            octets = dechiffrer(boite.lire(local.code, nom), cle, source.code, local.code)
            rapport = lots.importer(octets, f"{m['lot']}.erpx", utilisateur)
            bilan.recus.append(f"{nom} : {rapport.texte()}")
            boite.retirer(local.code, nom)
        except (ConnectionError, OSError) as exc:
            bilan.erreurs.append(f"{nom} : {exc}")
        except lots.LotInvalide as exc:
            bilan.erreurs.append(f"{nom} : {exc} (laissé dans la boîte)")


def _envoyer(boite, local, bilan, utilisateur):
    """Le lot n'est noté « émis » que si le dépôt a réussi : un échec annule tout, le passage suivant le refait.
    Si le dépôt a réussi mais que la réponse s'est perdue, le lot refait porte les mêmes faits : le destinataire
    ne les intègre qu'une fois. Le nom reçoit un suffixe aléatoire : deux lots ne portent jamais le même nom."""
    for destination in destinataires(local):
        try:
            if not a_envoyer(local, destination):
                continue
            with transaction.atomic():
                nom, octets = lots.exporter(destination, utilisateur=utilisateur)
                cle, _ = lots.cle_du_lien(local, destination)
                nom_boite = f"{nom.removesuffix('.erpx')}-{secrets.token_hex(4)}.erpx.chiffre"
                boite.deposer(destination.code, nom_boite, chiffrer(octets, cle, local.code, destination.code))
            bilan.envoyes.append(nom)
        except (ConnectionError, OSError, lots.LotInvalide) as exc:
            bilan.erreurs.append(f"envoi vers {destination.code} : {exc}")


def synchroniser(boite, utilisateur=None):
    """Reçoit et intègre ce qui attend dans la boîte de ce site, puis envoie ce qui est nouveau à chaque destinataire
    (les accusés de réception et les faits à relayer partent ainsi dans le même passage).
    Une boîte injoignable n'arrête rien : on réessaiera au passage suivant (rien n'est perdu, rien n'est intégré deux fois)."""
    local = site_local()
    bilan = Bilan()
    if local is None:
        bilan.erreurs.append("ce poste n'est pas configuré pour les échanges (siège ou agence)")
        return bilan
    _recevoir(boite, local, bilan, utilisateur)
    _envoyer(boite, local, bilan, utilisateur)
    return bilan
