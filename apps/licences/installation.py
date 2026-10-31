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
