"""Licences de l'ERP OHADA (docs/CONCEPTION_LICENCES.md) : fichier signé Ed25519, vérifié hors ligne.

Choix retenus : postes = comptes utilisateurs actifs ; licence annuelle ou définitive (champ « valable_jusqu_au »
vide) ; essai de 30 jours et 3 postes ; rappel 30 jours avant l'échéance ; 15 jours de grâce puis lecture seule ;
une licence par serveur (direction, chaque agence, site unique).
Une licence absente ou expirée ne bloque jamais la lecture, les exports ni les sauvegardes.
"""
import base64
import datetime
import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

ENTETE = "ERP-OHADA-LICENCE-V1"
ESSAI_JOURS = 30
ESSAI_POSTES = 3
RAPPEL_JOURS = 30
GRACE_JOURS = 15
EDITIONS = {"transport": {"TRANSPORT"}, "commerce": {"COMMERCE"}, "toutes": {"TRANSPORT", "COMMERCE", "MIXTE"}}
ROLES = {"seul": "Site unique", "siege": "Direction (siège)", "agence": "Agence"}


class LicenceInvalide(Exception):
    pass


# ---------------------------------------------------------------- Clés et format
def cles_publiques():
    fichier = Path(__file__).with_name("cle_publique.txt")
    lignes = fichier.read_text(encoding="utf-8").splitlines() if fichier.exists() else []
    return [l.strip() for l in lignes if l.strip() and not l.lstrip().startswith("#")]


def canonique(donnees):
    return json.dumps(donnees, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def lire(contenu):
    """Texte du fichier .erplic → (données, signature). Aucune confiance avant verifier_signature()."""
    try:
        texte = contenu.decode("utf-8-sig") if isinstance(contenu, bytes) else contenu
        lignes = [l.strip() for l in texte.strip().splitlines() if l.strip()]
        if len(lignes) != 3 or lignes[0] != ENTETE:
            raise ValueError
        donnees = json.loads(base64.b64decode(lignes[1], validate=True))
        signature = base64.b64decode(lignes[2], validate=True)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise LicenceInvalide("ce n'est pas un fichier de licence de l'ERP")
    if not isinstance(donnees, dict):
        raise LicenceInvalide("ce n'est pas un fichier de licence de l'ERP")
    return donnees, signature


def ecrire(donnees, signature):
    return "\n".join([ENTETE, base64.b64encode(canonique(donnees)).decode(), base64.b64encode(signature).decode(), ""])


def verifier_signature(donnees, signature):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    for cle in cles_publiques():
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(cle)).verify(signature, canonique(donnees))
            return True
        except (InvalidSignature, ValueError):
            continue
    if not cles_publiques():
        raise LicenceInvalide("aucune clé de vérification n'est installée dans ce logiciel (version d'essai)")
    raise LicenceInvalide("signature incorrecte : fichier modifié ou non émis par l'éditeur")


# ---------------------------------------------------------------- Empreinte du serveur
def _identifiant_machine():
    if os.environ.get("ERP_MACHINE_ID"):                          # essais automatiques
        return os.environ["ERP_MACHINE_ID"]
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as cle:
                return winreg.QueryValueEx(cle, "MachineGuid")[0]
        except OSError:
            pass
    for chemin in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            valeur = Path(chemin).read_text().strip()
            if valeur:
                return valeur
        except OSError:
            pass
    return f"{uuid.getnode():012x}"


def empreinte_machine():
    brut = hashlib.sha256(f"ERP-OHADA|{_identifiant_machine()}".encode()).digest()[:10]
    texte = base64.b32encode(brut).decode()                       # 16 caractères A-Z2-7
    return "-".join(texte[i:i + 4] for i in range(0, 16, 4))


def code_activation():
    """À envoyer à l'éditeur : édition + empreinte du serveur (rien de personnel)."""
    from apps.core.models import Societe

    return f"{Societe.get().activite[:1]}-{empreinte_machine()}"


# ---------------------------------------------------------------- Contrôle d'une licence pour ce serveur
def _date(texte):
    try:
        return datetime.date.fromisoformat(texte) if texte else None
    except (TypeError, ValueError):
        raise LicenceInvalide("date illisible dans la licence")


def controler(contenu):
    """Licence lue, signée par l'éditeur, faite pour ce serveur et cette édition → ses données."""
    from apps.core.models import Societe
    from apps.echanges.publication import site_local

    donnees, signature = lire(contenu)
    verifier_signature(donnees, signature)
    if donnees.get("machine") != empreinte_machine():
        raise LicenceInvalide("licence faite pour un autre serveur : envoyez le code d'activation de celui-ci")
    if Societe.get().activite not in EDITIONS.get(donnees.get("edition", ""), set()):
        raise LicenceInvalide(f"licence de l'édition « {donnees.get('edition')} » : ne couvre pas ce logiciel")
    local = site_local()
    if donnees.get("site") and local is not None and local.code != donnees["site"]:
        raise LicenceInvalide(f"licence du site {donnees['site']} : ce serveur est {local.code}")
    if not isinstance(donnees.get("postes"), int) or donnees["postes"] < 1:
        raise LicenceInvalide("nombre de postes absent de la licence")
    _date(donnees.get("valable_jusqu_au"))
    _date(donnees.get("maj_jusqu_au"))
    return donnees


def deposer(contenu, utilisateur=None):
    """Écran Licence : le fichier est gardé dans l'historique même refusé (avec le motif)."""
    texte = contenu.decode("utf-8-sig", errors="replace") if isinstance(contenu, bytes) else contenu
    from .models import LicenceDeposee

    try:
        donnees = controler(texte)
    except LicenceInvalide as exc:
        LicenceDeposee.objects.create(contenu=texte[:20000], valide=False, motif=str(exc)[:200], deposee_par=utilisateur)
        raise
    depot = LicenceDeposee.objects.create(contenu=texte, numero=str(donnees.get("numero", ""))[:40],
                                          client=str(donnees.get("client", ""))[:150], valide=True, deposee_par=utilisateur)
    oublier()
    return depot, donnees


# ---------------------------------------------------------------- Mémoire de l'essai
def _sceau(debut, derniere):
    return hmac.new(empreinte_machine().encode(), f"{debut}|{derniere}".encode(), hashlib.sha256).hexdigest()


def _fichier_essai():
    dossier = os.environ.get("ERP_DOSSIER_DONNEES")
    return Path(dossier) / ".erp-essai" if dossier else None


def _registre_lire():
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ERP-OHADA") as cle:
            return winreg.QueryValueEx(cle, "Essai")[0]
    except OSError:
        return None


def _registre_ecrire(valeur):
    if os.name != "nt":
        return
    try:
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ERP-OHADA") as cle:
            winreg.SetValueEx(cle, "Essai", 0, winreg.REG_SZ, valeur)
    except OSError:
        pass


def _debut_externe():
    """Début d'essai gardé hors de la base (dossier des données, registre) : une base neuve ne relance pas l'essai."""
    dates = []
    fichier = _fichier_essai()
    for valeur in ((fichier.read_text(encoding="utf-8") if fichier and fichier.exists() else None), _registre_lire()):
        try:
            debut, sceau = (valeur or "").strip().split("|")
            if hmac.compare_digest(sceau, _sceau(debut, debut)):
                dates.append(datetime.date.fromisoformat(debut))
        except ValueError:
            continue
    return min(dates) if dates else None


def _memoriser_debut(debut):
    valeur = f"{debut.isoformat()}|{_sceau(debut.isoformat(), debut.isoformat())}"
    fichier = _fichier_essai()
    if fichier is not None:
        try:
            fichier.write_text(valeur, encoding="utf-8")
        except OSError:
            pass
    if _registre_lire() is None:
        _registre_ecrire(valeur)


def memoire(aujourdhui):
    """(début de l'essai, date retenue pour aujourd'hui, horloge reculée ?) ; une date ne recule jamais."""
    from .models import EtatLicence

    etat = EtatLicence.objects.first()
    externe = _debut_externe()
    if etat is None:
        debut = min(filter(None, [externe, aujourdhui]))
        etat = EtatLicence.objects.create(debut_essai=debut, derniere_date_vue=aujourdhui,
                                          sceau=_sceau(debut.isoformat(), aujourdhui.isoformat()))
    elif not hmac.compare_digest(etat.sceau, _sceau(etat.debut_essai.isoformat(), etat.derniere_date_vue.isoformat())):
        etat.debut_essai = datetime.date(2000, 1, 1)               # mémoire modifiée à la main : essai terminé
    if externe and externe < etat.debut_essai:
        etat.debut_essai = externe
    recul = aujourdhui < etat.derniere_date_vue - datetime.timedelta(days=1)
    jour = max(aujourdhui, etat.derniere_date_vue)
    etat.derniere_date_vue = jour
    etat.sceau = _sceau(etat.debut_essai.isoformat(), jour.isoformat())
    etat.save()
    if externe is None or externe > etat.debut_essai:
        _memoriser_debut(etat.debut_essai)
    return etat.debut_essai, jour, recul


# ---------------------------------------------------------------- État du logiciel
@dataclass
class Etat:
    mode: str                     # « licence » ou « essai »
    statut: str                   # valide, rappel, grace, expiree
    jours: int = 0                # jours restants (avant l'échéance, la fin de la grâce ou de l'essai)
    postes: int = ESSAI_POSTES
    licence: dict = field(default_factory=dict)
    probleme: str = ""            # licence déposée mais refusée (ex. autre serveur)
    horloge_reculee: bool = False
    echeance: datetime.date | None = None

    @property
    def lecture_seule(self):
        return self.statut == "expiree"

    @property
    def message(self):
        if self.mode == "essai":
            if self.statut == "expiree":
                return "Période d'essai terminée : logiciel en lecture seule. Déposez une licence pour continuer à saisir."
            return f"Version d'essai : encore {self.jours} jour(s), {self.postes} postes."
        if self.statut == "rappel":
            return f"Licence à renouveler : échéance le {self.echeance:%d/%m/%Y} ({self.jours} jour(s))."
        if self.statut == "grace":
            return (f"Licence échue le {self.echeance:%d/%m/%Y} : encore {self.jours} jour(s) avant le passage en "
                    "lecture seule. Renouvelez-la.")
        if self.statut == "expiree":
            return "Licence expirée : logiciel en lecture seule (consultation, états, exports et sauvegardes restent possibles)."
        return ""


_CACHE = {}


def oublier():
    _CACHE.clear()


def etat(aujourdhui=None):
    """État calculé une fois par jour (et après chaque dépôt de licence)."""
    jour = aujourdhui or datetime.date.today()
    if jour in _CACHE:
        return _CACHE[jour]
    from .models import LicenceDeposee

    debut, jour_retenu, recul = memoire(jour)
    resultat, probleme = None, ""
    for depot in LicenceDeposee.objects.filter(valide=True)[:5]:   # la plus récente encore valable ici
        try:
            donnees = controler(depot.contenu)
        except LicenceInvalide as exc:
            probleme = probleme or str(exc)
            continue
        fin = _date(donnees.get("valable_jusqu_au"))
        e = Etat("licence", "valide", postes=donnees["postes"], licence=donnees, echeance=fin)
        if fin is not None:
            if jour_retenu <= fin:
                e.jours = (fin - jour_retenu).days
                e.statut = "rappel" if e.jours <= RAPPEL_JOURS else "valide"
            elif jour_retenu <= fin + datetime.timedelta(days=GRACE_JOURS):
                e.statut, e.jours = "grace", (fin + datetime.timedelta(days=GRACE_JOURS) - jour_retenu).days
            else:
                e.statut = "expiree"
        resultat = e
        break
    if resultat is None:
        fin = debut + datetime.timedelta(days=ESSAI_JOURS)
        resultat = Etat("essai", "valide" if jour_retenu <= fin else "expiree", jours=max(0, (fin - jour_retenu).days),
                        echeance=fin, probleme=probleme)
    resultat.horloge_reculee = recul
    _CACHE.clear()
    _CACHE[jour] = resultat
    return resultat


def comptes_actifs():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.filter(is_active=True).count()


def peut_activer_un_compte():
    """Un compte de plus dépasserait-il le nombre de postes ? (programme compilé seulement)"""
    from django.conf import settings

    if not getattr(settings, "ERP_LICENCE", False):
        return True, ""
    e = etat()
    if comptes_actifs() >= e.postes:
        return False, (f"{e.postes} poste(s) prévus par la {"version d'essai" if e.mode == "essai" else "licence"} "
                       f"et {comptes_actifs()} compte(s) actif(s) : désactivez un compte ou étendez la licence.")
    return True, ""
