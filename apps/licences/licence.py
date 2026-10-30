"""Licences de l'ERP OHADA (docs/CONCEPTION_LICENCES.md) : fichier signé Ed25519, vérifié hors ligne.

Choix retenus : postes = comptes utilisateurs actifs ; licence annuelle ou définitive (champ « valable_jusqu_au »
vide) ; essai de 30 ouvertures (connexions) dans la limite de 15 jours, 3 postes ; rappel 30 jours avant l'échéance ;
15 jours de grâce puis lecture seule ; une licence par serveur (direction, chaque agence, site unique).
Parcours : clé d'installation remise par l'éditeur → demande de licence produite ici (nom de la machine, société,
identifiant matériel, clé d'installation) → l'éditeur renvoie le fichier .erplic et la clé d'activation (l'un ou
l'autre suffit). Formats : format_cles.py.
Une licence absente ou expirée ne bloque jamais la lecture, les exports ni les sauvegardes.
"""
import base64
import datetime
import hashlib
import hmac
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from . import format_cles as fc

ENTETE = fc.ENTETE_LICENCE
ESSAI_OUVERTURES = 30
ESSAI_JOURS = 15
ESSAI_POSTES = 3
RAPPEL_JOURS = 30
GRACE_JOURS = 15
EDITIONS = {"transport": {"TRANSPORT"}, "commerce": {"COMMERCE"}, "toutes": {"TRANSPORT", "COMMERCE", "MIXTE"}}
ROLES = {"seul": "Site unique", "siege": "Direction (siège)", "agence": "Agence"}


class LicenceInvalide(Exception):
    pass


# ---------------------------------------------------------------- Clés et format
def cles_publiques():
    """Clés de vérification. Autorité : celles gravées dans le module compilé cle_editeur (non remplaçables).
    À défaut (développement, version d'essai sans clé gravée), le fichier texte cle_publique.txt sert de secours ;
    comme il est remplaçable, il n'est JAMAIS utilisé quand une clé est gravée."""
    try:
        from . import cle_editeur

        gravees = [c.strip() for c in getattr(cle_editeur, "CLES", []) if isinstance(c, str) and c.strip()]
    except Exception:
        gravees = []
    if gravees:
        return gravees
    if getattr(sys, "frozen", False):
        # Une clé remplaçable ne peut pas établir l'autorité d'un programme client.
        # Sans identité intégrée, le binaire reste en essai jusqu'à sa recompilation.
        return []
    # Repli quand aucune identité n'est intégrée : fichier binaire public, jamais le coffre privé.
    dossiers = [Path(__file__).parent]
    if getattr(sys, "frozen", False):
        dossiers.append(Path(sys.executable).parent)
    for dossier_identite in dict.fromkeys(dossiers):
        fichier = dossier_identite / "parametres.dat"
        if fichier.is_file():
            brut = fichier.read_bytes()
            if len(brut) == 38 and brut.startswith(b"ERPID\x01"):
                return [base64.b64encode(brut[6:]).decode()]
    cles, dossier = [], Path(__file__).parent        # les deux orthographes du fichier sont acceptées (tiret ou tiret bas)
    for nom in ("cle_publique.txt", "cle-publique.txt"):
        fichier = dossier / nom
        if fichier.exists():
            cles += [l.strip() for l in fichier.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.lstrip().startswith("#")]
    return cles


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
    return verifier_octets(canonique(donnees), signature)


def verifier_octets(message, signature, quoi="fichier"):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    for cle in cles_publiques():
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(cle)).verify(signature, message)
            return True
        except (InvalidSignature, ValueError):
            continue
    if not cles_publiques():
        raise LicenceInvalide("aucune clé de vérification n'est installée dans ce logiciel (version d'essai)")
    raise LicenceInvalide(f"signature incorrecte : {quoi} modifié ou non émis par l'éditeur")


# ---------------------------------------------------------------- Empreinte du serveur
def _identifiant_machine():
    if os.environ.get("ERP_MACHINE_ID") and not getattr(sys, "frozen", False):  # essais automatiques hors binaire
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


def nom_machine():
    import platform

    return (os.environ.get("COMPUTERNAME") or platform.node() or "inconnu")[:60]


def edition_logiciel():
    from apps.core.models import Societe

    return {"TRANSPORT": "transport", "COMMERCE": "commerce"}.get(Societe.get().activite, "toutes")


def code_activation():
    """Ancien code (édition + identifiant matériel), toujours accepté par l'outil de l'éditeur."""
    from apps.core.models import Societe

    return f"{Societe.get().activite[:1]}-{empreinte_machine()}"


# ---------------------------------------------------------------- Clé d'installation
def cle_installation_requise():
    """Programme compilé contenant la clé publique de l'éditeur : la clé d'installation est exigée."""
    from django.conf import settings

    return bool(getattr(settings, "ERP_LICENCE", False) and cles_publiques())


def lire_cle_installation(texte):
    """Clé d'installation vérifiée (signature de l'éditeur, édition de ce logiciel) → ses données."""
    if fc.est_installation_courte(texte):
        from apps.core.models import Societe

        code = fc.installation_courte_normaliser(texte)
        # Une référence courte identifie l'essai. Elle ne prouve aucun droit de licence.
        return {"numero": code, "societe": Societe.get().raison_sociale,
                "edition": edition_logiciel(), "emise_le": "", "courte": True}
    try:
        donnees, signe, signature = fc.installation_lire(texte)
    except fc.CleInvalide as exc:
        raise LicenceInvalide(str(exc))
    verifier_octets(signe, signature, "clé d'installation")
    if edition_logiciel() not in ("toutes",) and donnees["edition"] not in (edition_logiciel(), "toutes"):
        raise LicenceInvalide(f"clé d'installation de l'édition « {donnees['edition']} » : ne convient pas à ce logiciel")
    return donnees


def cle_installation():
    """Clé d'installation enregistrée sur ce serveur (données vérifiées) ou None."""
    from .models import EtatLicence

    etat = EtatLicence.objects.first()
    if etat is None or not etat.cle_installation:
        return None
    try:
        texte = ouvrir_stockage(etat.cle_installation)
        donnees = lire_cle_installation(texte)
        reference = hashlib.sha256(donnees["numero"].encode()).hexdigest()[:10].upper()
        return {**donnees, "texte": texte, "reference": reference}
    except (LicenceInvalide, ValueError):
        return None


def proteger_stockage(texte):
    from django.conf import settings
    from .stockage import sceller

    return sceller(texte, settings.SECRET_KEY, _identifiant_machine())


def ouvrir_stockage(texte):
    from django.conf import settings
    from .stockage import PREFIXE, ouvrir

    # Lecture des anciennes installations, converties au démarrage du programme.
    return ouvrir(texte, settings.SECRET_KEY, _identifiant_machine()) if texte.startswith(PREFIXE) else texte


def proteger_ancienne_installation(dossier):
    """Retire le fichier clair des anciens installateurs ; n'efface rien avant stockage protégé réussi."""
    from .models import EtatLicence
    from .stockage import PREFIXE

    for etat in EtatLicence.objects.exclude(cle_installation=""):
        if not etat.cle_installation.startswith(PREFIXE):
            EtatLicence.objects.filter(pk=etat.pk).update(cle_installation=proteger_stockage(etat.cle_installation))
    clair, protege = Path(dossier) / "cle-installation.txt", Path(dossier) / "installation.dat"
    if clair.is_file():
        if clair.stat().st_size > 64 * 1024:
            raise ValueError("Ancien fichier d'installation trop volumineux : intervention de l'éditeur nécessaire.")
        texte = clair.read_text(encoding="utf-8-sig").strip()
        temporaire = protege.with_suffix(".tmp")
        temporaire.write_text(proteger_stockage(texte), encoding="ascii")
        temporaire.replace(protege)
        clair.unlink()


def verifier_fichier_public(contenu):
    """Sélection facultative d'une clé publique déjà autorisée, jamais import d'une nouvelle autorité."""
    if len(contenu) > 8192:
        raise LicenceInvalide("fichier de vérification trop volumineux")
    if contenu.startswith(b"ERPID\x01") and len(contenu) == 38:
        candidate = base64.b64encode(contenu[6:]).decode()
    else:
        try:
            lignes = [x.strip() for x in contenu.decode("utf-8-sig").splitlines()
                      if x.strip() and not x.lstrip().startswith("#")]
            if len(lignes) != 1 or len(base64.b64decode(lignes[0], validate=True)) != 32:
                raise ValueError
            candidate = lignes[0]
        except (ValueError, UnicodeDecodeError):
            raise LicenceInvalide("choisissez uniquement le fichier public de vérification ; le coffre privé reste chez l'éditeur")
    autorisees = cles_publiques()
    if not autorisees:
        raise LicenceInvalide("l'identité de votre éditeur doit être intégrée à ce programme : demandez la version personnalisée")
    if candidate not in autorisees:
        raise LicenceInvalide("ce fichier public n'appartient pas à l'éditeur de ce programme")
    return candidate


def enregistrer_cle_installation(texte):
    """Écran de premier démarrage ou écran Licence : la clé est vérifiée puis gardée ; le nom de la société vient
    de la clé (il figure ensuite sur la demande de licence)."""
    from apps.core.models import Societe

    from .models import EtatLicence

    donnees = lire_cle_installation(texte)
    memoire(datetime.date.today())                                 # crée la mémoire de l'essai si besoin
    normalisee = (fc.installation_courte_normaliser(texte) if donnees.get("courte")
                  else fc.en_texte(fc.depuis_texte(texte)))
    EtatLicence.objects.update(cle_installation=proteger_stockage(normalisee))
    societe = Societe.get()
    if fc.nom_simple(societe.raison_sociale) != fc.nom_simple(donnees["societe"]):
        Societe.objects.filter(pk=societe.pk).update(raison_sociale=donnees["societe"][:150])
    oublier()
    return donnees


# ---------------------------------------------------------------- Demande de licence
def demande():
    """Ce que l'éditeur doit savoir pour produire la licence de CE serveur (rien d'autre)."""
    from apps.core.models import Societe
    from apps.echanges.publication import site_local

    societe, local, installation = Societe.get(), site_local(), cle_installation()
    role = {"SIEGE": "siege", "AGENCE": "agence"}.get(getattr(local, "role", ""), "seul") if local else "seul"
    return {"societe": societe.raison_sociale, "niu": getattr(societe, "niu", "") or "", "machine_nom": nom_machine(),
            "materiel": empreinte_machine(), "code": code_activation(), "edition": edition_logiciel(), "role": role,
            "site": local.code if local and role == "agence" else "",
            "installation": installation["numero"] if installation else "",
            "cle_installation": installation["texte"] if installation else "",
            "date": datetime.date.today().isoformat()}


def fichier_demande():
    return fc.demande_ecrire(demande())


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
    if donnees.get("version") == 3:
        installation = cle_installation()
        if installation is None or donnees.get("installation") != installation["numero"]:
            raise LicenceInvalide("ce fichier ne correspond pas au code d'installation de ce serveur")
        if fc.nom_simple(donnees.get("client", "")) != fc.nom_simple(Societe.get().raison_sociale):
            raise LicenceInvalide("ce fichier ne correspond pas à la société de ce serveur")
    local = site_local()
    if donnees.get("version") == 3:
        role = {"SIEGE": "siege", "AGENCE": "agence"}.get(getattr(local, "role", ""), "seul")
        if donnees.get("role") != role or donnees.get("site", "") != (local.code if local and role == "agence" else ""):
            raise LicenceInvalide("ce fichier ne correspond pas au rôle ou au site de ce serveur")
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


def licence_depuis_activation(texte):
    """Clé d'activation → texte du fichier .erplic équivalent, reconstitué avec la demande de CE serveur."""
    try:
        conditions, signature = fc.activation_lire(texte)
    except fc.CleInvalide as exc:
        raise LicenceInvalide(str(exc))
    donnees = fc.licence_donnees(demande(), conditions)
    try:
        verifier_signature(donnees, signature)
    except LicenceInvalide as exc:
        if not cles_publiques():
            raise
        raise LicenceInvalide("clé d'activation refusée : elle a été faite pour un autre serveur, une autre société ou "
                              "une autre clé d'installation (ou elle est mal recopiée)") from exc
    return fc.licence_texte(donnees, signature)


def activer(texte, utilisateur=None):
    """Clé d'activation collée à l'écran Licence : même effet que le dépôt du fichier .erplic."""
    from .models import LicenceDeposee

    try:
        licence_texte = licence_depuis_activation(texte)
    except LicenceInvalide as exc:
        LicenceDeposee.objects.create(contenu=texte[:2000], valide=False, motif=str(exc)[:200], deposee_par=utilisateur)
        raise
    return deposer(licence_texte, utilisateur)


# ---------------------------------------------------------------- Mémoire de l'essai
# L'essai se compte en OUVERTURES (chaque connexion réussie au logiciel), dans la limite de ESSAI_JOURS jours.
# Le compteur est gardé à trois endroits (base, dossier des données, registre Windows), scellé avec l'identifiant
# matériel : le plus grand l'emporte, et réinstaller le logiciel ou repartir d'une base neuve ne le remet pas à zéro.
def _sceau(*valeurs):
    return hmac.new(empreinte_machine().encode(), "|".join(map(str, valeurs)).encode(), hashlib.sha256).hexdigest()


def _sceau_valide(sceau, debut, derniere, ouvertures):
    if hmac.compare_digest(sceau, _sceau(debut, derniere, ouvertures)):
        return True
    return ouvertures == 0 and hmac.compare_digest(sceau, _sceau(debut, derniere))    # versions précédentes


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


def _externes():
    """Mémoires hors de la base : [(début, ouvertures)] dont le sceau est valide."""
    trouves = []
    fichier = _fichier_essai()
    for valeur in ((fichier.read_text(encoding="utf-8") if fichier and fichier.exists() else None), _registre_lire()):
        parties = (valeur or "").strip().split("|")
        try:
            if len(parties) == 3 and hmac.compare_digest(parties[2], _sceau(parties[0], parties[1])):
                trouves.append((datetime.date.fromisoformat(parties[0]), int(parties[1])))
            elif len(parties) == 2 and hmac.compare_digest(parties[1], _sceau(parties[0], parties[0])):
                trouves.append((datetime.date.fromisoformat(parties[0]), 0))
        except ValueError:
            continue
    return trouves


def _memoriser(debut, ouvertures):
    valeur = f"{debut.isoformat()}|{ouvertures}|{_sceau(debut.isoformat(), ouvertures)}"
    fichier = _fichier_essai()
    if fichier is not None:
        try:
            fichier.write_text(valeur, encoding="utf-8")
        except OSError:
            pass
    _registre_ecrire(valeur)


def memoire(aujourdhui, ouvrir=False):
    """(début de l'essai, date retenue pour aujourd'hui, horloge reculée ?, ouvertures) ; ni la date ni le compteur
    ne reculent jamais. ouvrir=True : une ouverture de plus (connexion réussie)."""
    from .models import EtatLicence

    etat = EtatLicence.objects.first()
    externes = _externes()
    debut_externe = min((d for d, _ in externes), default=None)
    ouvertures_externes = max((n for _, n in externes), default=0)
    if etat is None:
        debut = min(filter(None, [debut_externe, aujourdhui]))
        etat = EtatLicence(debut_essai=debut, derniere_date_vue=aujourdhui, ouvertures=ouvertures_externes)
    elif not _sceau_valide(etat.sceau, etat.debut_essai.isoformat(), etat.derniere_date_vue.isoformat(), etat.ouvertures):
        etat.debut_essai = datetime.date(2000, 1, 1)               # mémoire modifiée à la main : essai terminé
        etat.ouvertures = max(etat.ouvertures, ESSAI_OUVERTURES + 1)
    if debut_externe and debut_externe < etat.debut_essai:
        etat.debut_essai = debut_externe
    etat.ouvertures = max(etat.ouvertures, ouvertures_externes) + (1 if ouvrir else 0)
    recul = aujourdhui < etat.derniere_date_vue - datetime.timedelta(days=1)
    jour = max(aujourdhui, etat.derniere_date_vue)
    etat.derniere_date_vue = jour
    etat.sceau = _sceau(etat.debut_essai.isoformat(), jour.isoformat(), etat.ouvertures)
    etat.save()
    if debut_externe != etat.debut_essai or ouvertures_externes != etat.ouvertures or len(externes) < 2:
        _memoriser(etat.debut_essai, etat.ouvertures)
    return etat.debut_essai, jour, recul, etat.ouvertures


def compter_ouverture(**_):
    """Signal user_logged_in (programme compilé) : une ouverture d'essai de plus, tant qu'aucune licence n'est active."""
    from django.conf import settings

    if not getattr(settings, "ERP_LICENCE", False):
        return
    if etat().mode == "essai":
        memoire(datetime.date.today(), ouvrir=True)
        oublier()


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
    ouvertures: int = 0           # essai : ouvertures déjà faites
    sans_cle: bool = False        # essai : clé d'installation exigée mais absente

    @property
    def lecture_seule(self):
        return self.statut == "expiree"

    @property
    def ouvertures_restantes(self):
        return max(0, ESSAI_OUVERTURES - self.ouvertures)

    @property
    def message(self):
        if self.mode == "essai":
            if self.sans_cle:
                return ("Clé d'installation absente : saisissez celle remise par l'éditeur (Fichier › Administration "
                        "du poste › Licence). En attendant, le logiciel est en lecture seule.")
            if self.statut == "expiree":
                return "Période d'essai terminée : logiciel en lecture seule. Déposez une licence pour continuer à saisir."
            return (f"Version d'essai : encore {self.ouvertures_restantes} ouverture(s) sur {ESSAI_OUVERTURES}, "
                    f"au plus tard jusqu'au {self.echeance:%d/%m/%Y}, {self.postes} postes.")
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
    """État calculé une fois par jour (et après chaque dépôt de licence ou ouverture d'essai)."""
    jour = aujourdhui or datetime.date.today()
    if jour in _CACHE:
        return _CACHE[jour]
    from .models import LicenceDeposee

    debut, jour_retenu, recul, ouvertures = memoire(jour)
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
        sans_cle = cle_installation_requise() and cle_installation() is None
        en_cours = jour_retenu <= fin and ouvertures <= ESSAI_OUVERTURES and not sans_cle
        resultat = Etat("essai", "valide" if en_cours else "expiree", jours=max(0, (fin - jour_retenu).days),
                        echeance=fin, probleme=probleme, ouvertures=ouvertures, sans_cle=sans_cle)
    resultat.horloge_reculee = recul
    _CACHE.clear()
    _CACHE[jour] = resultat
    return resultat


def comptes_actifs():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.filter(is_active=True).count()


def fonctions_pro_disponibles():
    """Sauvegarde, restauration et gestion de la base : réservées aux versions sous licence.
    Indisponibles en version d'essai (le propriétaire l'a demandé) ; une licence expirée (lecture seule) les garde,
    pour que le client ne perde jamais l'accès à ses données."""
    from django.conf import settings

    if not getattr(settings, "ERP_LICENCE", False):
        return True, ""
    if etat().mode == "essai":
        return False, ("Fonction réservée à la version sous licence : les sauvegardes, la restauration et la gestion "
                       "de la base de données ne sont pas disponibles en version d'essai. Déposez une licence pour les activer.")
    return True, ""


def peut_activer_un_compte():
    """Un compte de plus dépasserait-il le nombre de postes ? (programme compilé seulement)"""
    from django.conf import settings

    if not getattr(settings, "ERP_LICENCE", False):
        return True, ""
    e = etat()
    if comptes_actifs() >= e.postes:
        source = "version d'essai" if e.mode == "essai" else "licence"
        return False, (f"{e.postes} poste(s) prévus par la {source} "
                       f"et {comptes_actifs()} compte(s) actif(s) : désactivez un compte ou étendez la licence.")
    return True, ""
