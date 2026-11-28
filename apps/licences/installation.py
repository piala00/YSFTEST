"""Autorisation de copie du programme, distincte du dépôt et de l'état d'une licence en base."""
import datetime

from . import licence as l


def autoriser(contenu, edition, *, machine=None, jour=None):
    """Une autorisation .erpinst distincte, sans lire une ancienne base/cache ni accepter un .erplic.

    Aucune activation ni consommation d'essai ici. La vérification métier complète sera répétée par l'ERP.
    Le client compilé utilise exclusivement l'autorité intégrée et sa vraie identité matérielle.
    """
    if edition not in ("transport", "commerce"):
        raise l.LicenceInvalide("édition d'installation inconnue")
    if not isinstance(contenu, bytes) or len(contenu) > 65536:
        raise l.LicenceInvalide("choisissez l'autorisation .erpinst signée, au maximum 64 Ko")
    try:
        d, signature = l.fc.autorisation_lire(contenu)
    except l.fc.CleInvalide as exc:
        raise l.LicenceInvalide(str(exc)) from None
    key_id = d.get("key_id")
    if not isinstance(key_id, str) or len(key_id) != 64 or any(c not in "0123456789ABCDEF" for c in key_id):
        raise l.LicenceInvalide("identifiant de clé publique absent ou invalide")
    # L'identité intégrée à l'installateur doit correspondre à celle du coffre
    # qui a signé l'autorisation. Aucun secours avec une clé remplaçable.
    identites = l.empreintes_publiques()
    if not identites:
        raise l.LicenceInvalide(
            "aucune identité d'éditeur intégrée à cet installateur d'essai ; "
            "utilisez un installateur personnalisé avec la clé publique du propriétaire"
        )
    if key_id not in identites:
        raise l.LicenceInvalide(
            "identité de signature incompatible : l'autorisation provient d'un autre "
            "coffre éditeur que celui intégré à cet installateur. "
            "Utilisez le générateur et l'installateur compilé avec la même identité publique"
        )
    l.verifier_octets(l.fc.DOMAINE_AUTORISATION + l.canonique(d), signature, "autorisation d'installation", key_id=key_id)
    if type(d.get("version")) is not int or d["version"] != 1:
        raise l.LicenceInvalide("version d'autorisation non prise en charge")
    if d.get("machine") != (machine or l.empreinte_machine()):
        raise l.LicenceInvalide("autorisation faite pour un autre serveur")
    if edition.upper() not in l.EDITIONS.get(d.get("edition"), set()):
        raise l.LicenceInvalide("autorisation d'une autre édition")
    fin = l._date(d.get("valable_jusqu_au"))
    if fin is not None and fin < (jour or datetime.date.today()):
        raise l.LicenceInvalide("autorisation d'installation expirée : demandez son renouvellement")
    try:
        l.fc.installation_courte_normaliser(d.get("reference", ""))
    except l.fc.CleInvalide as exc:
        raise l.LicenceInvalide(str(exc)) from None
    return {"numero": d["reference"], "edition": edition, "machine": d["machine"], "key_id": key_id}


def diagnostiquer(contenu, edition, *, publique, code=None, jour=None):
    """Diagnostique un .erpinst hors ligne sans autoriser l'installation ni modifier l'autorité intégrée."""
    rapport = {
        "mode": "diagnostic-seulement",
        "ok": False,
        "etapes": {},
    }

    def etape(nom, ok, message, **details):
        rapport["etapes"][nom] = {"ok": bool(ok), "message": message, **details}

    try:
        donnees, signature = l.fc.autorisation_lire(contenu)
    except (l.fc.CleInvalide, TypeError) as exc:
        etape("format", False, str(exc))
        return rapport
    etape("format", True, "Structure .erpinst et signature de 64 octets lisibles.")

    version_ok = type(donnees.get("version")) is int and donnees.get("version") == 1
    etape("version", version_ok, "Version 1 prise en charge." if version_ok else "Version d'autorisation inconnue ou invalide.")

    key_id = donnees.get("key_id")
    key_id_ok = (
        isinstance(key_id, str)
        and len(key_id) == 64
        and all(c in "0123456789ABCDEF" for c in key_id)
    )
    etape("key_id", key_id_ok, "Identifiant SHA-256 bien formé." if key_id_ok else "Identifiant de clé publique absent ou mal formé.")

    cle_publique = None
    empreinte_publique = None
    try:
        from .identite import empreinte, lire_publique

        cle_publique = lire_publique(publique)
        empreinte_publique = empreinte(cle_publique)
        identite_ok = key_id_ok and empreinte_publique == key_id
        etape(
            "identite_publique",
            identite_ok,
            "La clé publique fournie correspond au key_id du .erpinst."
            if identite_ok else "La clé publique fournie ne correspond pas au key_id du .erpinst.",
            empreinte_publique=empreinte_publique,
            key_id_autorisation=key_id,
        )
    except (ValueError, TypeError) as exc:
        identite_ok = False
        etape("identite_publique", False, f"Clé publique illisible : {exc}")

    if identite_ok:
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

            Ed25519PublicKey.from_public_bytes(cle_publique).verify(
                signature,
                l.fc.DOMAINE_AUTORISATION + l.fc.canonique(donnees),
            )
            signature_ok = True
            etape("signature", True, "Signature Ed25519 valide sur le domaine d'autorisation .erpinst.")
        except (InvalidSignature, ValueError):
            signature_ok = False
            etape("signature", False, "Le key_id correspond, mais la signature Ed25519 est incorrecte.")
    else:
        signature_ok = False
        etape("signature", False, "Non vérifiée : fournir la clé publique correspondant au key_id.")

    edition = edition.lower() if isinstance(edition, str) else ""
    edition_app_ok = edition in ("transport", "commerce")
    edition_dans_fichier = (
        edition_app_ok
        and edition.upper() in l.EDITIONS.get(donnees.get("edition"), set())
    )

    code_ok = True
    edition_code_ok = True
    if code:
        prefixe, separateur, machine_attendue = code.strip().upper().partition("-")
        editions_code = {
            "T": {"transport"},
            "C": {"commerce"},
            "M": {"transport", "commerce"},
        }
        code_ok = bool(separateur and machine_attendue and prefixe in editions_code)
        edition_code_ok = code_ok and edition in editions_code.get(prefixe, set())
    else:
        machine_attendue = l.empreinte_machine()

    etape(
        "code_machine",
        code_ok and edition_code_ok,
        "Code matériel fourni et préfixe compatibles avec l'édition."
        if code_ok and edition_code_ok else "Code matériel absent, mal formé ou préfixe incompatible avec l'édition.",
    )
    machine_ok = code_ok and bool(machine_attendue) and donnees.get("machine") == machine_attendue
    etape(
        "machine",
        machine_ok,
        "L'autorisation vise le code matériel fourni."
        if machine_ok else "Le code matériel du .erpinst ne correspond pas au code attendu.",
        machine_autorisation=donnees.get("machine"),
        machine_attendue=machine_attendue,
    )

    edition_ok = edition_dans_fichier and edition_code_ok
    etape(
        "edition",
        edition_ok,
        "L'autorisation couvre l'édition demandée."
        if edition_ok else "L'édition du fichier ou le préfixe du code ne correspond pas à l'édition demandée.",
        edition_autorisation=donnees.get("edition"),
        edition_attendue=edition,
    )

    try:
        fin = l._date(donnees.get("valable_jusqu_au"))
        date_ok = fin is None or fin >= (jour or datetime.date.today())
        etape(
            "expiration",
            date_ok,
            "Autorisation non expirée." if date_ok else "Autorisation expirée.",
            valable_jusqu_au=fin.isoformat() if fin else None,
        )
    except l.LicenceInvalide as exc:
        date_ok = False
        etape("expiration", False, str(exc))

    try:
        reference = l.fc.installation_courte_normaliser(donnees.get("reference", ""))
        reference_ok = True
        etape("reference", True, "Référence d'installation valide.", reference=reference)
    except l.fc.CleInvalide as exc:
        reference_ok = False
        etape("reference", False, str(exc))

    rapport["donnees"] = {
        "edition": donnees.get("edition"),
        "machine": donnees.get("machine"),
        "key_id": key_id,
        "valable_jusqu_au": donnees.get("valable_jusqu_au"),
        "reference": donnees.get("reference"),
    }
    rapport["ok"] = all(
        item.get("ok", False) for item in rapport["etapes"].values()
    )
    rapport["avertissement"] = (
        "Ce rapport est diagnostique uniquement. Il ne remplace pas la vérification "
        "de la clé publique intégrée à l'installateur et n'autorise jamais une installation."
    )
    return rapport
