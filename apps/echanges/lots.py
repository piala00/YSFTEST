"""Lots d'échange : fabrication, contrôle, import idempotent, adhésion d'une agence.

Un lot est un fichier .erpx (archive ZIP) qui contient exactement :
  manifest.json  description signée (protocole, société, source, destination, plage, empreintes des fichiers)
  events.jsonl   un fait par ligne
  auth.json      HMAC-SHA256 du manifeste avec la clé d'échange de l'agence (partagée avec le siège)
et, pour l'installation d'une agence seulement, adhesion.json (identité et clé : à transmettre en main propre).
Le ZIP est compressé mais pas chiffré : il circule par un canal maîtrisé par la société.
"""
import hashlib
import hmac
import io
import json
import secrets
import uuid
import zipfile
import zlib
from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from . import contrats
from .models import Evenement, EvenementRecu, LotEmis, LotRecu, Relais
from .publication import import_en_cours, publier_objet, site_local

PROTOCOLE = "erp-ohada-agency-exchange"
SCHEMA = 1
PREFIXE = b"ERP-OHADA-EXCHANGE-V1\x00"
FICHIERS = {"manifest.json", "events.jsonl", "auth.json"}
TAILLE_MAX = 60 * 1024 * 1024            # fichier reçu
DECOMPRESSE_MAX = 400 * 1024 * 1024      # contenu décompressé
EVENEMENTS_MAX = 500_000


class LotInvalide(Exception):
    pass


def _json(octets):
    def interdit(valeur):
        raise LotInvalide(f"valeur numérique interdite : {valeur}")

    try:
        return json.loads(octets.decode("utf-8"), parse_constant=interdit)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LotInvalide(f"JSON illisible : {exc}")


def _mac(cle, manifeste):
    return hmac.new(bytes.fromhex(cle), PREFIXE + manifeste, hashlib.sha256).hexdigest()


def _sha(octets):
    return hashlib.sha256(octets).hexdigest()


def cle_du_lien(local, autre):
    """Chaque agence a sa clé, connue d'elle et du siège seulement."""
    cle = autre.cle_echange if local.role == local.SIEGE else local.cle_echange
    if not cle:
        raise LotInvalide(f"aucune clé d'échange entre {local.code} et {autre.code}")
    return cle, (autre.code if local.role == local.SIEGE else local.code)


def _evenement_dict(e, origine):
    return {"event_uuid": str(e.uid), "origine_uid": str(origine.uid), "origine_code": origine.code, "sequence": e.sequence,
            "type": e.type, "objet_uid": str(e.objet_uid), "revision": e.revision, "operation": e.operation,
            "date_metier": e.date_metier.isoformat() if e.date_metier else None, "auteur": e.auteur,
            "payload_version": contrats.VERSION, "payload": e.payload}


# ---------------------------------------------------------------- Pertinence des relais (au siège)
def _gares_de(evt):
    """Gares concernées par un fait relayé (None : utile à toutes les agences)."""
    from apps.transport.models import Colis, Depart, Gare, Ligne, Troncon

    p = evt.payload
    if evt.type == "billet":                       # correspondances : gares de changement
        return list(Gare.objects.filter(uid__in=[t["gare_depart"] for t in p.get("troncons", []) if t.get("ordre", 1) > 1]))
    if evt.type in ("troncon_affecte", "troncon_effectue"):
        t = Troncon.objects.filter(uid=p.get("troncon")).select_related("billet__gare").first()
        return [t.billet.gare] if t and t.billet.gare else []
    if evt.type == "depart":
        ligne = Ligne.objects.filter(uid=p.get("ligne")).first()
        return [ligne.gare_depart, ligne.gare_arrivee] if ligne else []
    if evt.type == "colis":
        return list(Gare.objects.filter(uid__in=[p.get("gare_depart"), p.get("gare_arrivee")]))
    if evt.type == "colis_livraison":
        c = Colis.objects.filter(uid=p.get("colis")).first()
        return [c.gare_depart, c.gare_arrivee] if c else []
    if evt.type == "depart_arrivee":
        d = Depart.objects.filter(uid=p.get("depart")).select_related("ligne").first()
        return [d.ligne.gare_depart, d.ligne.gare_arrivee] if d else []
    return None                                                     # référentiel : utile à tous


def _a_relayer(destination):
    deja = Relais.objects.filter(destination=destination).values_list("evenement_id", flat=True)
    candidats = (EvenementRecu.objects.filter(statut=EvenementRecu.INTEGRE, type__in=contrats.RELAYES)
                 .exclude(site_origine=destination).exclude(pk__in=deja).select_related("site_origine")
                 .order_by("site_origine_id", "sequence"))
    retenus = []
    for evt in candidats:
        if evt.payload.get("pour_agence"):                  # fait adressé à une seule agence
            if evt.payload["pour_agence"] == destination.code:
                retenus.append(evt)
            continue
        gares = _gares_de(evt)
        if gares is None or any(g.agence_id == destination.pk for g in gares):
            retenus.append(evt)
    return retenus


# ---------------------------------------------------------------- Fabrication
@transaction.atomic
def exporter(destination, utilisateur=None, depuis=None, adhesion=None):
    """Fabrique le lot pour ce destinataire. Renvoie (nom de fichier, octets)."""
    local = site_local()
    if local is None:
        raise LotInvalide("Ce poste n'est pas encore configuré pour les échanges (siège ou agence).")
    if destination.pk == local.pk:
        raise LotInvalide("Choisissez un autre site que celui-ci.")
    if local.role == local.AGENCE and destination.role != destination.SIEGE:
        raise LotInvalide("Une agence envoie ses lots au siège, qui les relaie aux agences concernées.")
    from apps.core.models import Societe

    cle, key_id = cle_du_lien(local, destination)
    dernier = LotEmis.objects.filter(destination=destination).aggregate(m=Max("sequence_a"))["m"] or 0
    debut = depuis if depuis is not None else dernier + 1
    propres = list(Evenement.objects.filter(sequence__gte=debut))
    relayes = _a_relayer(destination) if local.role == local.SIEGE else []
    lignes = [_evenement_dict(e, local) for e in propres]
    for r in relayes:
        d = _evenement_dict(r, r.site_origine)
        d["relaye"] = True
        lignes.append(d)
    evenements = "".join(json.dumps(l, ensure_ascii=False, separators=(",", ":")) + "\n" for l in lignes).encode("utf-8")
    sequence_a = propres[-1].sequence if propres else max(debut - 1, dernier)
    paquet = uuid.uuid4()
    manifeste = json.dumps({
        "protocol": PROTOCOLE, "schema_version": SCHEMA, "package_uuid": str(paquet),
        "societe_uuid": str(Societe.get().uid), "source_site_uuid": str(local.uid), "source_code": local.code,
        "destination_site_uuid": str(destination.uid), "destination_code": destination.code,
        "created_at_utc": timezone.now().astimezone(datetime_timezone_utc()).isoformat(),
        "business_timezone": "Africa/Douala", "sequence_from": debut, "sequence_to": sequence_a,
        "event_count": len(lignes), "relayed_count": len(relayes),
        "files": [{"name": "events.jsonl", "bytes": len(evenements), "sha256": _sha(evenements)}],
    }, ensure_ascii=False, indent=1).encode("utf-8")
    auth = json.dumps({"algorithm": "HMAC-SHA256", "key_id": key_id, "mac": _mac(cle, manifeste)}).encode("utf-8")
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("manifest.json", manifeste)
        z.writestr("events.jsonl", evenements)
        z.writestr("auth.json", auth)
        if adhesion is not None:
            z.writestr("adhesion.json", json.dumps(adhesion, ensure_ascii=False, indent=1))
    octets = tampon.getvalue()
    horodatage = timezone.localtime().strftime("%Y%m%d-%H%M")
    nom = (f"ERP-{'INSTALLATION' if adhesion else 'LOT'}-{local.code}-vers-{destination.code}-{horodatage}"
           f"-{debut}-{sequence_a}.erpx")
    lot = LotEmis.objects.create(destination=destination, sequence_de=debut, sequence_a=sequence_a, nombre=len(lignes),
                                 relayes=len(relayes), nom_fichier=nom[:120], empreinte=_sha(octets), taille=len(octets),
                                 cree_par=utilisateur, uid=paquet)
    Relais.objects.bulk_create([Relais(evenement=r, destination=destination, lot=lot) for r in relayes])
    return nom, octets


def datetime_timezone_utc():
    import datetime

    return datetime.timezone.utc


# ---------------------------------------------------------------- Lecture et contrôle
def _ouvrir(contenu, avec_adhesion=False):
    if len(contenu) > TAILLE_MAX:
        raise LotInvalide("fichier trop volumineux")
    try:
        z = zipfile.ZipFile(io.BytesIO(contenu))
    except (zipfile.BadZipFile, zlib.error, ValueError):
        raise LotInvalide("ce n'est pas un lot d'échange (archive illisible ou incomplète : renvoyez-le)")
    noms = {i.filename for i in z.infolist()}
    attendus = FICHIERS | ({"adhesion.json"} if "adhesion.json" in noms else set())
    if noms != attendus or len(z.infolist()) != len(attendus):
        raise LotInvalide(f"contenu inattendu dans le lot : {', '.join(sorted(noms))}")
    if "adhesion.json" in noms and not avec_adhesion:
        raise LotInvalide("ce fichier est un fichier d'installation d'agence : utilisez « Installer cette agence »")
    if sum(i.file_size for i in z.infolist()) > DECOMPRESSE_MAX:
        raise LotInvalide("contenu décompressé trop volumineux")
    try:
        return {n: z.read(n) for n in noms}
    except (zipfile.BadZipFile, zlib.error, OSError, EOFError, ValueError):
        raise LotInvalide("fichier abîmé pendant la transmission : demandez qu'on vous le renvoie")


def lire_adhesion(contenu):
    fichiers = _ouvrir(contenu, avec_adhesion=True)
    if "adhesion.json" not in fichiers:
        raise LotInvalide("ce lot n'est pas un fichier d'installation d'agence")
    return _json(fichiers["adhesion.json"])


@dataclass
class Rapport:
    lot: str = ""
    source: str = ""
    recus: int = 0
    nouveaux: int = 0
    doublons: int = 0
    integres: int = 0
    ignores: int = 0
    attente: int = 0
    conflits: int = 0
    rejets: int = 0
    manques: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    deja_recu: bool = False

    def texte(self):
        if self.deja_recu:
            return f"Lot {self.lot} déjà reçu et intégré : rien à refaire."
        lignes = [f"Lot {self.lot} de {self.source} : {self.recus} fait(s) reçu(s), {self.nouveaux} nouveau(x), "
                  f"{self.doublons} déjà connu(s).",
                  f"Intégrés : {self.integres} · sans objet ici : {self.ignores} · en attente : {self.attente} · "
                  f"conflits : {self.conflits} · rejetés : {self.rejets}"]
        if self.manques:
            lignes.append("Lots manquants : faits n° " + ", ".join(self.manques) + " pas encore reçus (demandez le renvoi).")
        lignes += self.messages[:30]
        return "\n".join(lignes)


@transaction.atomic
def importer(contenu, nom_fichier="", utilisateur=None, avec_adhesion=False):
    from apps.core.models import Agence, Societe

    local = site_local()
    if local is None:
        raise LotInvalide("Ce poste n'est pas encore configuré pour les échanges.")
    fichiers = _ouvrir(contenu, avec_adhesion)
    manifeste_octets = fichiers["manifest.json"]
    m, auth = _json(manifeste_octets), _json(fichiers["auth.json"])
    if m.get("protocol") != PROTOCOLE or m.get("schema_version") != SCHEMA:
        raise LotInvalide("version de lot inconnue : mettez le logiciel à jour")
    if m.get("societe_uuid") != str(Societe.get().uid):
        raise LotInvalide("ce lot vient d'une autre société")
    if m.get("destination_site_uuid") != str(local.uid):
        raise LotInvalide(f"ce lot est destiné à {m.get('destination_code')}, pas à ce site ({local.code})")
    source = Agence.objects.filter(uid=m.get("source_site_uuid"), actif=True).first()
    if source is None:
        raise LotInvalide(f"site émetteur inconnu ou désactivé ({m.get('source_code')})")
    if local.role == local.AGENCE and source.role != source.SIEGE:
        raise LotInvalide("une agence ne reçoit que les lots du siège")
    cle, key_id = cle_du_lien(local, source)
    if auth.get("algorithm") != "HMAC-SHA256" or auth.get("key_id") != key_id \
            or not hmac.compare_digest(str(auth.get("mac", "")), _mac(cle, manifeste_octets)):
        raise LotInvalide("signature invalide : lot modifié, ou clé d'échange différente")
    for f in m.get("files", []):
        octets = fichiers.get(f.get("name"))
        if octets is None or len(octets) != f.get("bytes") or _sha(octets) != f.get("sha256"):
            raise LotInvalide(f"fichier {f.get('name')} altéré")
    rapport = Rapport(lot=str(m["package_uuid"])[:8], source=source.code)
    empreinte = _sha(contenu)
    deja = LotRecu.objects.filter(uid=m["package_uuid"]).first()
    if deja is not None:
        if deja.empreinte != empreinte and deja.empreinte != _sha(manifeste_octets):
            raise LotInvalide("un autre lot porte déjà ce numéro (conflit) : rien n'est remplacé")
        rapport.deja_recu = True
        return rapport
    lignes = [l for l in fichiers["events.jsonl"].decode("utf-8").splitlines() if l.strip()]
    if len(lignes) != m.get("event_count") or len(lignes) > EVENEMENTS_MAX:
        raise LotInvalide("nombre de faits incohérent")
    lot = LotRecu.objects.create(uid=m["package_uuid"], source=source, empreinte=_sha(manifeste_octets),
                                 nom_fichier=nom_fichier[:200], nombre=len(lignes), recu_par=utilisateur)
    rapport.recus = len(lignes)
    evenements = sorted((_json(l.encode("utf-8")) for l in lignes),
                        key=lambda e: (contrats.PRIORITE.get(e.get("type"), 9), e.get("sequence", 0)))
    for e in evenements:
        _recevoir(e, lot, source, local, rapport)
    _integrer_en_attente(local, rapport)
    _avancer_curseur(source, rapport)
    lot.rapport = rapport.texte()
    lot.save(update_fields=["rapport"])
    return rapport


def _recevoir(e, lot, source, local, rapport):
    from apps.core.models import Agence

    for champ in ("event_uuid", "origine_uid", "sequence", "type", "objet_uid", "payload"):
        if e.get(champ) in (None, ""):
            rapport.rejets += 1
            rapport.messages.append(f"fait sans {champ} : ignoré")
            return
    if e["type"] not in contrats.INTEGRATIONS:
        rapport.rejets += 1
        rapport.messages.append(f"type de fait inconnu « {e['type']} » : mettez le logiciel à jour")
        return
    if e["origine_uid"] == str(local.uid):
        rapport.doublons += 1                                           # fait de ce site revenu par le siège
        return
    origine = Agence.objects.filter(uid=e["origine_uid"]).first()
    if origine is None and e["type"] == "agence" and e["payload"].get("uid") == e["origine_uid"]:
        with import_en_cours():
            contrats._agence(e["payload"], source, local)                # le siège se présente lui-même
        origine = Agence.objects.filter(uid=e["origine_uid"]).first()
    if origine is None:
        if e["type"] == "agence":
            origine = source
        else:
            rapport.attente += 1
            rapport.messages.append(f"site d'origine {e.get('origine_code')} inconnu : fait mis de côté")
            return
    if not e.get("relaye") and origine.pk != source.pk:
        rapport.rejets += 1
        rapport.messages.append("fait attribué à un autre site sans relais : rejeté")
        return
    empreinte = _sha(json.dumps(e["payload"], sort_keys=True).encode("utf-8"))
    existant = EvenementRecu.objects.filter(site_origine=origine, uid=e["event_uuid"]).first()
    if existant is not None:
        if existant.empreinte != empreinte:
            rapport.conflits += 1
            rapport.messages.append(f"fait {e['type']} n° {e['sequence']} de {origine.code} reçu deux fois avec un contenu différent")
        else:
            rapport.doublons += 1
        return
    EvenementRecu.objects.create(site_origine=origine, uid=e["event_uuid"], sequence=e["sequence"], type=e["type"],
                                 objet_uid=e["objet_uid"], revision=e.get("revision") or 1, operation=e.get("operation") or "",
                                 date_metier=e.get("date_metier"), auteur=(e.get("auteur") or "")[:150], payload=e["payload"],
                                 empreinte=empreinte, relaye=bool(e.get("relaye")), lot=lot)
    rapport.nouveaux += 1


def _integrer_en_attente(local, rapport):
    """Intègre les faits en attente (y compris ceux des lots précédents) ; plusieurs passes pour les dépendances."""
    for _ in range(4):
        progres = False
        attente = sorted(EvenementRecu.objects.filter(statut=EvenementRecu.ATTENTE).select_related("site_origine"),
                         key=lambda e: (contrats.PRIORITE.get(e.type, 9), e.site_origine_id, e.sequence))
        for evt in attente:
            plus_recent = EvenementRecu.objects.filter(site_origine=evt.site_origine, type=evt.type, objet_uid=evt.objet_uid,
                                                       statut=EvenementRecu.INTEGRE, revision__gt=evt.revision).exists()
            try:
                if plus_recent:
                    raise contrats.SansObjet("version plus récente déjà intégrée")
                with transaction.atomic(), import_en_cours():
                    contrats.INTEGRATIONS[evt.type](evt.payload, evt.site_origine, local)
                evt.statut, evt.message = EvenementRecu.INTEGRE, ""
                rapport.integres += 1
                progres = True
            except contrats.Attente as exc:
                evt.message = str(exc)[:300]
            except contrats.SansObjet as exc:
                evt.statut, evt.message = EvenementRecu.IGNORE, str(exc)[:300]
                rapport.ignores += 1
                progres = True
            except contrats.Conflit as exc:
                evt.statut, evt.message = EvenementRecu.CONFLIT, str(exc)[:300]
                rapport.conflits += 1
                rapport.messages.append(f"{evt.type} {evt.site_origine.code} n° {evt.sequence} : {exc}")
            except Exception as exc:                                   # donnée inattendue : ne bloque pas le reste
                evt.statut, evt.message = EvenementRecu.REJET, f"{type(exc).__name__} : {exc}"[:300]
                rapport.rejets += 1
                rapport.messages.append(f"{evt.type} {evt.site_origine.code} n° {evt.sequence} rejeté : {exc}")
            evt.integre_le = timezone.now() if evt.statut != EvenementRecu.ATTENTE else None
            evt.save(update_fields=["statut", "message", "integre_le"])
        if not progres:
            break
    restants = EvenementRecu.objects.filter(statut=EvenementRecu.ATTENTE)
    rapport.attente = restants.count()
    for evt in restants[:10]:
        rapport.messages.append(f"en attente — {evt.type} {evt.site_origine.code} n° {evt.sequence} : {evt.message}")


def _avancer_curseur(source, rapport):
    """Dernier fait reçu sans trou depuis ce site (les faits relayés n'entrent pas dans ce compte)."""
    recus = set(EvenementRecu.objects.filter(site_origine=source, relaye=False, sequence__gt=source.sequence_integree)
                .values_list("sequence", flat=True))
    curseur = source.sequence_integree
    while curseur + 1 in recus:
        curseur += 1
    plus_haut = max(recus) if recus else curseur
    if plus_haut > curseur:
        manquants = [n for n in range(curseur + 1, plus_haut) if n not in recus]
        rapport.manques.append(f"{manquants[0]}" + (f" à {manquants[-1]}" if len(manquants) > 1 else ""))
    source.sequence_integree, source.derniere_reception = curseur, timezone.now()
    source.save(update_fields=["sequence_integree", "derniere_reception"])


# ---------------------------------------------------------------- Mise en place
@transaction.atomic
def configurer_siege(code, nom):
    """Ce poste devient le siège : identité de la société, site siège (rang 1)."""
    from apps.core.models import Agence, Societe

    societe = Societe.get()
    if not societe.uid:
        societe.uid = uuid.uuid4()
        societe.save(update_fields=["uid"])
    if Agence.objects.filter(locale=True, uid__isnull=False).exclude(role=Agence.SIEGE).exists():
        raise LotInvalide("Ce poste est déjà installé comme agence.")
    siege = Agence.objects.filter(locale=True).first() or Agence(locale=True)
    siege.code, siege.nom, siege.role, siege.rang = code, nom, Agence.SIEGE, 1
    siege.uid = siege.uid or uuid.uuid4()
    siege.save()
    publier_existant()
    return siege


@transaction.atomic
def ajouter_agence(code, nom, ville=""):
    from apps.core.models import Agence

    local = site_local()
    if local is None or local.role != local.SIEGE:
        raise LotInvalide("Seul le siège déclare les agences.")
    rang = (Agence.objects.aggregate(m=Max("rang"))["m"] or 1) + 1
    agence = Agence.objects.create(code=code, nom=nom, ville=ville, role=Agence.AGENCE, rang=rang, uid=uuid.uuid4(),
                                   cle_echange=secrets.token_hex(32), locale=False)
    return agence


def fichier_installation(agence, utilisateur=None):
    """Au siège : fichier qui installe l'agence (identité, clé, référentiels). À remettre en main propre."""
    from apps.core.models import Societe

    local = site_local()
    if local is None or local.role != local.SIEGE:
        raise LotInvalide("Seul le siège prépare l'installation d'une agence.")
    societe = Societe.get()
    adhesion = {"type": "adhesion", "societe": {"uid": str(societe.uid), "raison_sociale": societe.raison_sociale},
                "siege": {"uid": str(local.uid), "code": local.code, "nom": local.nom, "rang": local.rang},
                "agence": {"uid": str(agence.uid), "code": agence.code, "nom": agence.nom, "ville": agence.ville,
                           "rang": agence.rang, "cle": agence.cle_echange}}
    return exporter(agence, utilisateur, depuis=1, adhesion=adhesion)


@transaction.atomic
def installer_agence(contenu, nom_fichier="", utilisateur=None):
    """Dans l'agence : prend l'identité donnée par le siège, puis intègre les référentiels du fichier."""
    from apps.core.models import Agence, Societe

    a = lire_adhesion(contenu)
    local = site_local()
    if local is not None and str(local.uid) != a["agence"]["uid"]:
        raise LotInvalide(f"Ce poste est déjà installé comme {local.code}.")
    societe = Societe.get()
    if societe.uid and str(societe.uid) != a["societe"]["uid"]:
        raise LotInvalide("Ce dossier appartient à une autre société.")
    societe.uid = a["societe"]["uid"]
    societe.save(update_fields=["uid"])
    ag = a["agence"]
    moi = Agence.objects.filter(locale=True).first() or Agence(locale=True)
    moi.uid, moi.code, moi.nom, moi.ville, moi.role, moi.rang, moi.cle_echange = (
        ag["uid"], ag["code"], ag["nom"], ag.get("ville", ""), Agence.AGENCE, ag["rang"], ag["cle"])
    moi.save()
    s = a["siege"]
    siege = Agence.objects.filter(uid=s["uid"]).first() or Agence(uid=s["uid"])
    siege.code, siege.nom, siege.role, siege.rang, siege.locale, siege.cle_echange = (
        s["code"], s["nom"], Agence.SIEGE, s["rang"], False, ag["cle"])
    siege.save()
    rapport = importer(contenu, nom_fichier, utilisateur, avec_adhesion=True)
    publier_existant()                                     # ce qui a déjà été saisi ici part au prochain lot
    return rapport


def publier_existant():
    """Rattrapage : publie une fois les faits de ce dossier antérieurs à la mise en place des échanges."""
    from apps.comptabilite.models import Ecriture
    from apps.core.models import Agence
    from apps.garage.models import OrdreReparation, PleinCarburant
    from apps.transport.models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, Vehicule

    from .publication import publier_ecriture

    local = site_local()
    connus = set(Evenement.objects.values_list("objet_uid", flat=True))
    n = 0
    if local.role == local.SIEGE:
        for a in Agence.objects.filter(uid__isnull=False):
            if a.uid not in connus:
                publier_objet(a)
                n += 1
    for modele in (Gare, Vehicule, Chauffeur, Ligne, Depart, Billet, Colis, DepenseVehicule, PleinCarburant, OrdreReparation):
        for o in modele.objects.filter(site_origine=""):
            if o.uid not in connus:
                publier_objet(o)
                n += 1
    for e in Ecriture.objects.filter(site_origine="", statut=Ecriture.STATUT_VALIDEE).order_by("date", "pk"):
        if e.uid not in connus:
            publier_ecriture(e)
            n += 1
    return n
