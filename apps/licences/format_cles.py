"""Clés de l'ERP OHADA, communes au logiciel et à l'outil du propriétaire (aucune dépendance à Django).

Clé d'installation : remise par l'éditeur à la société AVANT l'installation ; elle porte la société et l'édition,
signée Ed25519 par l'éditeur. Sans elle, le premier démarrage ne va pas plus loin (dès que le logiciel contient
la clé publique de l'éditeur).
Demande de licence (.erpdem) : produite par le logiciel du client (nom de la machine, société, identifiant matériel,
clé d'installation, rôle et site) ; envoyée à l'éditeur.
Licence : l'outil du propriétaire en produit DEUX formes, au choix du client :
  - le fichier .erplic (texte signé, lisible) ;
  - la clé d'activation (à copier-coller) : les conditions de la licence + la même signature ; le logiciel reconstitue
    la licence avec sa propre demande et vérifie la signature.
Texte des clés : base 32 (A-Z, 2-7) par groupes de 5, sans ambiguïté à la dictée ou au copier-coller.
"""
import base64
import datetime
import json
import re
import struct
import unicodedata

ENTETE_LICENCE = "ERP-OHADA-LICENCE-V1"
ENTETE_DEMANDE = "ERP-OHADA-DEMANDE-V1"
DOMAINE_INSTALLATION = b"ERP-OHADA-INSTALLATION|"
EDITIONS = ("transport", "commerce", "toutes")
ROLES = ("seul", "siege", "agence")
ORIGINE = datetime.date(2020, 1, 1)
TYPE_INSTALLATION, TYPE_ACTIVATION = 0x49, 0x41          # « I », « A »


class CleInvalide(ValueError):
    pass


def canonique(donnees):
    return json.dumps(donnees, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------- Texte des clés
def en_texte(brut):
    texte = base64.b32encode(brut).decode().rstrip("=")
    return "-".join(texte[i:i + 5] for i in range(0, len(texte), 5))


def depuis_texte(texte):
    propre = re.sub(r"[\s\-]", "", texte or "").upper().replace("0", "O").replace("1", "I").replace("8", "B")
    if not propre or not re.fullmatch(r"[A-Z2-7]+", propre):
        raise CleInvalide("clé illisible : seulement des lettres et les chiffres 2 à 7")
    try:
        return base64.b32decode(propre + "=" * (-len(propre) % 8))
    except ValueError:
        raise CleInvalide("clé incomplète : recopiez-la en entier")


def _jours(date):
    return 0 if date is None else (date - ORIGINE).days


def _date(jours):
    return None if jours == 0 else ORIGINE + datetime.timedelta(days=jours)


def numero_entier(numero):
    """« INS-2026-0001 » ou « LIC-2026-0001 » → 20260001."""
    m = re.fullmatch(r"[A-Z]{3}-(\d{4})-(\d{1,4})", numero or "")
    if not m:
        raise CleInvalide(f"numéro attendu comme LIC-2026-0001 : {numero}")
    return int(m[1]) * 10000 + int(m[2])


def numero_texte(prefixe, entier):
    return f"{prefixe}-{entier // 10000}-{entier % 10000:04d}"


# ---------------------------------------------------------------- Clé d'installation
def installation_donnees(numero, societe, edition, emise_le):
    """Partie signée de la clé d'installation (octets)."""
    nom = societe.strip().encode("utf-8")[:120]
    if edition not in EDITIONS:
        raise CleInvalide(f"édition inconnue : {edition}")
    if not nom:
        raise CleInvalide("nom de la société absent")
    return struct.pack(">BIBHB", TYPE_INSTALLATION, numero_entier(numero), EDITIONS.index(edition),
                       _jours(emise_le), len(nom)) + nom


def installation_creer(cle_privee, numero, societe, edition, emise_le=None):
    donnees = installation_donnees(numero, societe, edition, emise_le or datetime.date.today())
    return en_texte(donnees + cle_privee.sign(DOMAINE_INSTALLATION + donnees))


def installation_lire(texte):
    """Clé d'installation → (données, partie signée, signature). Aucune confiance avant la vérification."""
    brut = depuis_texte(texte)
    if len(brut) < 9 + 64 or brut[0] != TYPE_INSTALLATION:
        raise CleInvalide("ce n'est pas une clé d'installation de l'ERP")
    _, numero, edition, emise, longueur = struct.unpack(">BIBHB", brut[:9])
    signe, signature = brut[:9 + longueur], brut[9 + longueur:]
    if len(signature) != 64 or edition >= len(EDITIONS):
        raise CleInvalide("clé d'installation incomplète ou altérée")
    try:
        societe = brut[9:9 + longueur].decode("utf-8")
    except UnicodeDecodeError:
        raise CleInvalide("clé d'installation altérée")
    return ({"numero": numero_texte("INS", numero), "societe": societe, "edition": EDITIONS[edition],
             "emise_le": _date(emise).isoformat() if emise else ""}, DOMAINE_INSTALLATION + signe, signature)


# ---------------------------------------------------------------- Demande de licence
def demande_ecrire(donnees):
    return "\n".join([ENTETE_DEMANDE, json.dumps(donnees, ensure_ascii=False, indent=1, sort_keys=True), ""])


def demande_lire(texte):
    texte = texte.decode("utf-8-sig") if isinstance(texte, bytes) else texte.lstrip("﻿")
    entete, _, reste = texte.strip().partition("\n")
    try:
        donnees = json.loads(reste) if entete.strip() == ENTETE_DEMANDE else None
    except json.JSONDecodeError:
        donnees = None
    if not isinstance(donnees, dict) or not donnees.get("materiel") or not donnees.get("societe"):
        raise CleInvalide("ce n'est pas une demande de licence de l'ERP")
    return donnees


# ---------------------------------------------------------------- Licence (fichier .erplic et clé d'activation)
def licence_donnees(demande, conditions):
    """Données signées de la licence : identité tirée de la demande, conditions choisies par l'éditeur.
    conditions : numero, edition, role, postes, emise_le, valable_jusqu_au (None = définitive), maj_jusqu_au."""
    return {"version": 2, "numero": conditions["numero"], "client": demande["societe"], "niu": demande.get("niu", ""),
            "edition": conditions["edition"], "role": conditions["role"], "site": demande.get("site", ""),
            "postes": conditions["postes"], "machine": demande["materiel"], "machine_nom": demande.get("machine_nom", ""),
            "installation": demande.get("installation", ""), "emise_le": conditions["emise_le"],
            "valable_jusqu_au": conditions["valable_jusqu_au"], "maj_jusqu_au": conditions["maj_jusqu_au"]}


def _iso(jours):
    d = _date(jours)
    return d.isoformat() if d else None


def activation_creer(conditions, signature):
    def jours(texte):
        return _jours(datetime.date.fromisoformat(texte)) if texte else 0

    brut = struct.pack(">BIHHHHBB", TYPE_ACTIVATION, numero_entier(conditions["numero"]), conditions["postes"],
                       jours(conditions["emise_le"]), jours(conditions["valable_jusqu_au"]),
                       jours(conditions["maj_jusqu_au"]), EDITIONS.index(conditions["edition"]),
                       ROLES.index(conditions["role"]))
    return en_texte(brut + signature)


def activation_lire(texte):
    """Clé d'activation → (conditions, signature)."""
    brut = depuis_texte(texte)
    taille = struct.calcsize(">BIHHHHBB")
    if len(brut) != taille + 64 or brut[0] != TYPE_ACTIVATION:
        raise CleInvalide("ce n'est pas une clé d'activation de l'ERP (ou elle est incomplète)")
    _, numero, postes, emise, jusqu, maj, edition, role = struct.unpack(">BIHHHHBB", brut[:taille])
    if edition >= len(EDITIONS) or role >= len(ROLES):
        raise CleInvalide("clé d'activation altérée")
    return ({"numero": numero_texte("LIC", numero), "postes": postes, "emise_le": _iso(emise),
             "valable_jusqu_au": _iso(jusqu), "maj_jusqu_au": _iso(maj), "edition": EDITIONS[edition],
             "role": ROLES[role]}, brut[taille:])


def licence_texte(donnees, signature):
    return "\n".join([ENTETE_LICENCE, base64.b64encode(canonique(donnees)).decode(),
                      base64.b64encode(signature).decode(), ""])


def nom_simple(texte):
    """Pour comparer deux noms de société sans se soucier des accents, majuscules ni ponctuation."""
    sans_accents = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", sans_accents.upper())
