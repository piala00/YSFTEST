"""Contrats des faits échangés : sérialisation (version 1) et intégration chez le destinataire.

Les montants sont des chaînes décimales, les dates au format ISO. L'intégration crée ou met à jour une copie
identifiée par son uid ; elle ne rejoue jamais l'opération (pas de vente, pas d'écriture recalculée).
"""
import datetime
from decimal import Decimal

from django.utils.dateparse import parse_datetime

VERSION = 1


class Attente(Exception):
    """Une dépendance (départ, gare, exercice…) n'est pas encore connue : réessayer au prochain lot."""


class SansObjet(Exception):
    """Fait qui ne concerne pas ce site."""


class Conflit(Exception):
    """Contradiction à examiner (code déjà pris, période clôturée…)."""


def _d(v):
    return None if v is None else str(v)


def _date(v):
    return v.isoformat() if v else None


def _uid(o):
    return str(o.uid) if o is not None else None


# ---------------------------------------------------------------- Sérialisation
def ecriture(e):
    j = e.journal
    return {"v": VERSION, "uid": str(e.uid), "numero": e.numero, "date": _date(e.date), "libelle": e.libelle,
            "reference": e.reference, "origine": e.origine,
            "journal": {"code": j.code, "intitule": j.intitule, "type": j.type_journal,
                        "tresorerie": j.compte_tresorerie.numero if j.compte_tresorerie_id else None},
            "lignes": [{"compte": l.compte.numero, "intitule": l.compte.intitule,
                        "tiers": ({"code": l.tiers.code, "nom": l.tiers.nom, "type": l.tiers.type_tiers} if l.tiers_id else None),
                        "section": ({"code": l.section.code, "intitule": l.section.intitule, "plan": l.section.plan}
                                    if l.section_id else None),
                        "vehicule": str(l.vehicule.uid) if l.vehicule_id else None,
                        "libelle": l.libelle, "debit": _d(l.debit), "credit": _d(l.credit), "lettrage": l.lettrage}
                       for l in e.lignes.select_related("compte", "tiers", "section", "vehicule").order_by("pk")]}


def serialiser(o):
    """(type, payload, date métier, auteur) d'un objet du transport ou d'une agence."""
    from apps.core.models import Agence
    from apps.transport.models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, Vehicule

    if isinstance(o, Agence):
        return "agence", {"v": VERSION, "uid": str(o.uid), "code": o.code, "nom": o.nom, "ville": o.ville, "role": o.role,
                          "rang": o.rang, "actif": o.actif}, None, ""
    if isinstance(o, Gare):
        return "gare", {"v": VERSION, "uid": str(o.uid), "code": o.code, "nom": o.nom, "ville": o.ville,
                        "agence": _uid(o.agence), "actif": o.actif}, None, ""
    if isinstance(o, Ligne):
        return "ligne", {"v": VERSION, "uid": str(o.uid), "code": o.code, "gare_depart": _uid(o.gare_depart),
                         "gare_arrivee": _uid(o.gare_arrivee), "distance_km": o.distance_km, "duree": o.duree,
                         "prix_billet": _d(o.prix_billet), "colis_forfait": _d(o.colis_forfait),
                         "colis_prix_kg": _d(o.colis_prix_kg), "actif": o.actif}, None, ""
    if isinstance(o, Vehicule):
        return "vehicule", {"v": VERSION, "uid": str(o.uid), "immatriculation": o.immatriculation, "designation": o.designation,
                            "type": o.type_vehicule, "places": o.nombre_places, "actif": o.actif,
                            "carte_grise": o.carte_grise, "mise_en_service": _date(o.mise_en_service),
                            "assurance_echeance": _date(o.assurance_echeance),
                            "visite_technique_echeance": _date(o.visite_technique_echeance)}, None, ""
    if isinstance(o, Chauffeur):
        return "chauffeur", {"v": VERSION, "uid": str(o.uid), "nom": o.nom, "telephone": o.telephone, "permis": o.permis,
                             "actif": o.actif}, None, ""
    if isinstance(o, Depart):
        return "depart", {"v": VERSION, "uid": str(o.uid), "numero": o.numero, "ligne": _uid(o.ligne), "date": _date(o.date),
                          "heure": o.heure.strftime("%H:%M") if o.heure else None, "vehicule": _uid(o.vehicule),
                          "chauffeur": _uid(o.chauffeur), "places": o.places, "statut": o.statut,
                          "parti_le": _date(o.parti_le), "arrive_le": _date(o.arrive_le)}, o.date, o.cree_par or ""
    if isinstance(o, Billet):
        return "billet", {"v": VERSION, "uid": str(o.uid), "numero": o.numero, "date_vente": _date(o.date_vente),
                          "gare": _uid(o.gare), "depart": _uid(o.depart), "voyageur": o.voyageur, "telephone": o.telephone,
                          "piece_identite": o.piece_identite, "siege": o.siege, "prix": _d(o.prix), "paiement": o.paiement,
                          "client": o.client.code if o.client_id else None, "statut": o.statut, "retenue": _d(o.retenue),
                          "vendu_par": str(o.vendu_par or ""), "annule_le": _date(o.annule_le),
                          "gare_arrivee": _uid(o.gare_arrivee),
                          "troncons": [{"uid": str(t.uid), "ordre": t.ordre, "gare_depart": _uid(t.gare_depart),
                                        "gare_arrivee": _uid(t.gare_arrivee), "depart": _uid(t.depart), "siege": t.siege,
                                        "part": _d(t.part), "statut": t.statut, "vehicule": _uid(t.vehicule),
                                        "site_effectue": t.site_effectue, "effectue_le": _date(t.effectue_le)}
                                       for t in o.troncons.order_by("ordre")]}, o.date_vente, o.vendu_par or ""
    if isinstance(o, Colis):
        return "colis", {"v": VERSION, "uid": str(o.uid), "numero": o.numero, "nature": o.nature, "date": _date(o.date),
                         "gare_depart": _uid(o.gare_depart), "gare_arrivee": _uid(o.gare_arrivee), "expediteur": o.expediteur,
                         "tel_expediteur": o.tel_expediteur, "destinataire": o.destinataire,
                         "tel_destinataire": o.tel_destinataire, "description": o.description, "nombre": o.nombre,
                         "poids": _d(o.poids), "valeur_declaree": _d(o.valeur_declaree), "prix": _d(o.prix), "port": o.port,
                         "contre_remboursement": _d(o.contre_remboursement), "depart": _uid(o.depart), "statut": o.statut,
                         "code_retrait": o.code_retrait, "livre_le": _date(o.livre_le), "retire_par": o.retire_par,
                         "livre_site": o.livre_site, "cr_reverse_le": _date(o.cr_reverse_le)}, o.date, o.cree_par or ""
    if isinstance(o, DepenseVehicule):
        return "depense", {"v": VERSION, "uid": str(o.uid), "numero": o.numero, "date": _date(o.date),
                           "vehicule": _uid(o.vehicule), "depart": _uid(o.depart), "nature": o.nature, "libelle": o.libelle,
                           "montant": _d(o.montant), "compte": o.compte.numero if o.compte_id else None}, o.date, o.cree_par or ""
    raise TypeError(f"Objet non échangeable : {o!r}")


# ---------------------------------------------------------------- Intégration
def _par_uid(modele, uid, quoi, obligatoire=True):
    if not uid:
        return None
    objet = modele.objects.filter(uid=uid).first()
    if objet is None and obligatoire:
        raise Attente(f"{quoi} {uid} pas encore reçu")
    return objet


def _copie(modele, uid, origine):
    """Copie existante (ou nouvelle) ; un objet créé ici n'est jamais écrasé par un lot."""
    objet = modele.objects.filter(uid=uid).first()
    if objet is not None and not objet.site_origine:
        raise SansObjet("objet créé dans ce dossier")
    return objet or modele(uid=uid, site_origine=origine.code)


def _enregistrer(objet, cle, valeur):
    from django.db import IntegrityError, transaction

    try:
        with transaction.atomic():
            objet.save()
    except IntegrityError:
        raise Conflit(f"{cle} « {valeur} » déjà utilisé dans ce dossier par une autre fiche")


def _agence(p, origine, local):
    from apps.core.models import Agence

    if p["uid"] == str(local.uid):
        raise SansObjet("ce site")
    a = Agence.objects.filter(uid=p["uid"]).first() or Agence.objects.filter(code=p["code"], uid__isnull=True).first() \
        or Agence(uid=p["uid"])
    a.uid, a.code, a.nom, a.ville, a.role, a.rang, a.actif, a.locale = (p["uid"], p["code"], p["nom"], p.get("ville", ""),
                                                                         p["role"], p.get("rang"), p.get("actif", True), False)
    _enregistrer(a, "Code d'agence", p["code"])


def _gare(p, origine, local):
    from apps.core.models import Agence
    from apps.transport.models import Gare

    g = _copie(Gare, p["uid"], origine)
    g.code, g.nom, g.ville, g.actif = p["code"], p["nom"], p["ville"], p.get("actif", True)
    g.agence = Agence.objects.filter(uid=p["agence"]).first() if p.get("agence") else None
    _enregistrer(g, "Code de gare", p["code"])


def _ligne(p, origine, local):
    from apps.transport.models import Gare, Ligne

    l = _copie(Ligne, p["uid"], origine)
    l.code, l.distance_km, l.duree, l.actif = p["code"], p.get("distance_km"), p.get("duree", ""), p.get("actif", True)
    l.gare_depart, l.gare_arrivee = _par_uid(Gare, p["gare_depart"], "gare"), _par_uid(Gare, p["gare_arrivee"], "gare")
    l.prix_billet, l.colis_forfait, l.colis_prix_kg = Decimal(p["prix_billet"]), Decimal(p["colis_forfait"]), Decimal(p["colis_prix_kg"])
    _enregistrer(l, "Code de ligne", p["code"])


def _vehicule(p, origine, local):
    from apps.transport.models import Vehicule

    v = _copie(Vehicule, p["uid"], origine)
    v.immatriculation, v.designation, v.type_vehicule, v.nombre_places, v.actif = (
        p["immatriculation"], p.get("designation", ""), p.get("type", "CAR"), p.get("places") or 0, p.get("actif", True))
    v.carte_grise = p.get("carte_grise", "")
    for champ in ("mise_en_service", "assurance_echeance", "visite_technique_echeance"):
        setattr(v, champ, datetime.date.fromisoformat(p[champ]) if p.get(champ) else None)
    _enregistrer(v, "Immatriculation", p["immatriculation"])


def _chauffeur(p, origine, local):
    from apps.transport.models import Chauffeur

    c = _copie(Chauffeur, p["uid"], origine)
    c.nom, c.telephone, c.permis, c.actif = p["nom"], p.get("telephone", ""), p.get("permis", ""), p.get("actif", True)
    c.save()


def _concerne(local, *gares):
    """Au siège tout est utile ; dans une agence, seulement ce qui touche ses gares."""
    if local.role == local.SIEGE:
        return True
    return any(g is not None and g.agence_id == local.pk for g in gares)


def _suivre_statut_depart(d, statut):
    """Reproduit chez le destinataire les effets d'un départ ou d'une arrivée sur les billets et les colis copiés."""
    from apps.transport.models import Billet, Colis, Depart

    if statut in (Depart.PARTI, Depart.ARRIVE):
        d.billets.filter(statut=Billet.VENDU).update(statut=Billet.EMBARQUE)
        d.colis.filter(statut=Colis.CHARGE).update(statut=Colis.EN_ROUTE)
    if statut == Depart.ARRIVE:
        d.colis.filter(statut=Colis.EN_ROUTE).update(statut=Colis.ARRIVE)


ORDRE_DEPART = {"PROGRAMME": 0, "PARTI": 1, "ARRIVE": 2, "ANNULE": 3}


def _depart(p, origine, local):
    from apps.transport.models import Chauffeur, Depart, Ligne, Vehicule

    ligne = _par_uid(Ligne, p["ligne"], "ligne")
    if not _concerne(local, ligne.gare_depart, ligne.gare_arrivee):
        raise SansObjet("départ d'une autre agence")
    d = _copie(Depart, p["uid"], origine)
    statut = p["statut"] if ORDRE_DEPART[p["statut"]] >= ORDRE_DEPART.get(d.statut or "PROGRAMME", 0) else d.statut
    d.numero, d.ligne, d.date, d.places = p["numero"], ligne, datetime.date.fromisoformat(p["date"]), p.get("places") or 0
    d.heure = datetime.time.fromisoformat(p["heure"])
    d.vehicule = _par_uid(Vehicule, p.get("vehicule"), "véhicule", obligatoire=False)
    d.chauffeur = _par_uid(Chauffeur, p.get("chauffeur"), "chauffeur", obligatoire=False)
    d.statut = statut
    d.parti_le = parse_datetime(p["parti_le"]) if p.get("parti_le") else d.parti_le
    d.arrive_le = parse_datetime(p["arrive_le"]) if p.get("arrive_le") else d.arrive_le
    _enregistrer(d, "N° de départ", p["numero"])
    _suivre_statut_depart(d, statut)


ORDRE_TRONCON = {"A_VOYAGER": 0, "EFFECTUE": 1, "ANNULE": 2}


def _billet(p, origine, local):
    """Au siège : tous les billets (états consolidés). Dans une agence : ceux dont un tronçon part de ses gares
    (voyageur en correspondance à placer sur un de ses véhicules)."""
    from apps.commercial.models import Tiers
    from apps.transport.models import Billet, Depart, Gare, Troncon, Vehicule

    troncons = p.get("troncons") or []
    if local.role != local.SIEGE:
        gares = [Gare.objects.filter(uid=t["gare_depart"]).first() for t in troncons if t.get("ordre", 1) > 1]
        if not _concerne(local, *gares):
            raise SansObjet("billet sans correspondance dans cette agence")
    b = _copie(Billet, p["uid"], origine)
    b.gare_arrivee = _par_uid(Gare, p.get("gare_arrivee"), "gare", obligatoire=False)
    b.depart, b.gare = _par_uid(Depart, p["depart"], "départ"), _par_uid(Gare, p.get("gare"), "gare", obligatoire=False)
    for champ in ("numero", "voyageur", "telephone", "piece_identite", "siege", "paiement", "statut"):
        setattr(b, champ, p.get(champ) if p.get(champ) is not None else ("" if champ not in ("siege",) else None))
    b.date_vente, b.prix, b.retenue = datetime.date.fromisoformat(p["date_vente"]), Decimal(p["prix"]), Decimal(p["retenue"])
    b.client = Tiers.objects.filter(code=f"{origine.code}.{p['client']}"[:20]).first() if p.get("client") else None
    b.annule_le = parse_datetime(p["annule_le"]) if p.get("annule_le") else None
    _enregistrer(b, "N° de billet", p["numero"])
    for t in troncons:
        tr = Troncon.objects.filter(uid=t["uid"]).first() or Troncon(uid=t["uid"], billet=b, site_origine=origine.code)
        tr.billet, tr.ordre, tr.part = b, t["ordre"], Decimal(t["part"])
        tr.gare_depart, tr.gare_arrivee = _par_uid(Gare, t["gare_depart"], "gare"), _par_uid(Gare, t["gare_arrivee"], "gare")
        if t.get("depart") and (tr.depart_id is None or tr.statut == Troncon.A_VOYAGER):
            tr.depart, tr.siege = _par_uid(Depart, t["depart"], "départ", obligatoire=False) or tr.depart, t.get("siege")
        if ORDRE_TRONCON[t["statut"]] >= ORDRE_TRONCON.get(tr.statut or "A_VOYAGER", 0):
            tr.statut = t["statut"]
            tr.vehicule = _par_uid(Vehicule, t.get("vehicule"), "véhicule", obligatoire=False) or tr.vehicule
            tr.site_effectue = t.get("site_effectue") or tr.site_effectue
            tr.effectue_le = parse_datetime(t["effectue_le"]) if t.get("effectue_le") else tr.effectue_le
        tr.save()


ORDRE_COLIS = {"ENREGISTRE": 0, "CHARGE": 1, "EN_ROUTE": 2, "ARRIVE": 3, "LIVRE": 4, "ANNULE": 5}


def _colis(p, origine, local):
    from apps.transport.models import Colis, Depart, Gare

    gd, ga = _par_uid(Gare, p["gare_depart"], "gare"), _par_uid(Gare, p["gare_arrivee"], "gare")
    if not _concerne(local, gd, ga):
        raise SansObjet("envoi d'une autre agence")
    c = _copie(Colis, p["uid"], origine)
    actuel = c.statut if c.pk else "ENREGISTRE"
    for champ in ("numero", "nature", "expediteur", "tel_expediteur", "destinataire", "tel_destinataire", "description",
                  "port", "code_retrait"):
        setattr(c, champ, p.get(champ) or "")
    c.gare_depart, c.gare_arrivee, c.nombre = gd, ga, p.get("nombre") or 1
    c.date = datetime.date.fromisoformat(p["date"])
    c.poids, c.valeur_declaree = Decimal(p["poids"]), Decimal(p["valeur_declaree"])
    c.prix, c.contre_remboursement = Decimal(p["prix"]), Decimal(p["contre_remboursement"])
    c.depart = _par_uid(Depart, p.get("depart"), "départ") if p.get("depart") else None
    c.statut = p["statut"] if p["statut"] == "ANNULE" or ORDRE_COLIS[p["statut"]] >= ORDRE_COLIS[actuel] else actuel
    if p.get("livre_le"):
        c.livre_le, c.retire_par, c.livre_site = parse_datetime(p["livre_le"]), p.get("retire_par", ""), p.get("livre_site", "")
    if p.get("cr_reverse_le"):
        c.cr_reverse_le = parse_datetime(p["cr_reverse_le"])
    _enregistrer(c, "N° d'envoi", p["numero"])
    if c.depart_id:                                   # le départ a pu partir ou arriver depuis (mise à jour groupée)
        _suivre_statut_depart(c.depart, c.depart.statut)


def _colis_livraison(p, origine, local):
    """Remise d'un envoi faite dans une autre agence : l'envoi est livré partout (et le contre-remboursement peut
    être reversé par l'agence d'expédition, sur le compte de liaison de l'agence qui l'a encaissé)."""
    from apps.transport.models import Colis

    c = Colis.objects.filter(uid=p["colis"]).first()
    if c is None:
        if local.role == local.SIEGE:
            raise Attente(f"envoi {p['colis']} pas encore reçu")
        raise SansObjet("envoi inconnu ici")
    c.statut, c.livre_le, c.retire_par, c.livre_site = (Colis.LIVRE, parse_datetime(p["livre_le"]), p.get("retire_par", ""),
                                                        p["site"])
    c.save(update_fields=["statut", "livre_le", "retire_par", "livre_site"])


def _depart_arrivee(p, origine, local):
    from apps.transport.models import Depart

    d = Depart.objects.filter(uid=p["depart"]).first()
    if d is None:
        if local.role == local.SIEGE:
            raise Attente(f"départ {p['depart']} pas encore reçu")
        raise SansObjet("départ inconnu ici")
    if d.statut != Depart.ANNULE:
        d.statut, d.arrive_le = Depart.ARRIVE, parse_datetime(p["arrive_le"])
        d.save(update_fields=["statut", "arrive_le"])
        _suivre_statut_depart(d, Depart.ARRIVE)


def _troncon_affecte(p, origine, local):
    """Voyageur placé sur un véhicule de correspondance par l'agence de changement."""
    from apps.transport.models import Depart, Troncon

    t = Troncon.objects.filter(uid=p["troncon"]).first()
    if t is None:
        if local.role == local.SIEGE:
            raise Attente(f"billet du tronçon {p['troncon']} pas encore reçu")
        raise SansObjet("tronçon inconnu ici")
    if t.statut == Troncon.A_VOYAGER:
        t.depart = Depart.objects.filter(uid=p["depart"]).first() or t.depart
        t.siege = p.get("siege")
        t.save(update_fields=["depart", "siege"])


def _troncon_effectue(p, origine, local):
    """Tronçon fait par un véhicule d'une autre agence. Chez l'agence qui a vendu le billet : la somme encaissée
    d'avance revient à l'agence du véhicule (D billets à voyager / C liaison de cette agence)."""
    from apps.comptabilite.models import Journal
    from apps.comptabilite.services import creer_ecriture
    from apps.echanges.publication import hors_import
    from apps.transport.models import Billet, ParametresTransport, Troncon, Vehicule, _compte_liaison

    t = Troncon.objects.filter(uid=p["troncon"]).select_related("billet").first()
    if t is None:
        if local.role == local.SIEGE:
            raise Attente(f"billet du tronçon {p['troncon']} pas encore reçu")
        raise SansObjet("tronçon inconnu ici")
    if t.statut == Troncon.EFFECTUE:
        raise SansObjet("tronçon déjà effectué")
    date = datetime.date.fromisoformat(p["date"])
    if not t.site_origine and t.part:                   # billet vendu ici : on solde l'avance du voyageur
        parametres = ParametresTransport.get()
        with hors_import():
            creer_ecriture(Journal.objects.get(code="OD"), date,
                           f"Billet {t.billet.numero} : tronçon {t.gare_depart.ville} → {t.gare_arrivee.ville} fait par {origine.nom}",
                           [{"compte": parametres.compte_billets_a_voyager, "debit": t.part},
                            {"compte": _compte_liaison(origine.code), "credit": t.part}],
                           reference=t.billet.numero, origine=t.billet.numero)
    t.statut, t.site_effectue = Troncon.EFFECTUE, p.get("site") or origine.code
    t.vehicule = Vehicule.objects.filter(uid=p.get("vehicule")).first()
    t.effectue_le = parse_datetime(f"{p['date']}T12:00:00")
    t.save(update_fields=["statut", "site_effectue", "vehicule", "effectue_le"])
    Billet.objects.filter(pk=t.billet_id, statut=Billet.VENDU).update(statut=Billet.EMBARQUE)


def _depense(p, origine, local):
    from apps.comptabilite.models import Compte, Journal
    from apps.transport.models import Depart, DepenseVehicule, Vehicule

    if local.role != local.SIEGE:
        raise SansObjet("dépenses consolidées au siège seulement")
    dv = _copie(DepenseVehicule, p["uid"], origine)
    dv.numero, dv.nature, dv.libelle = p["numero"], p["nature"], p.get("libelle", "")
    dv.date, dv.montant = datetime.date.fromisoformat(p["date"]), Decimal(p["montant"])
    dv.vehicule = _par_uid(Vehicule, p["vehicule"], "véhicule")
    dv.depart = _par_uid(Depart, p.get("depart"), "départ") if p.get("depart") else None
    dv.compte = Compte.objects.filter(numero=p.get("compte")).first()
    dv.caisse = Journal.objects.filter(type_journal=Journal.TYPE_TRESORERIE).first()
    _enregistrer(dv, "N° de dépense", p["numero"])


def _ecriture(p, origine, local):
    """Consolidation au siège : l'écriture de l'agence est reprise telle quelle, dans un journal propre au site."""
    from apps.commercial.models import Tiers
    from apps.comptabilite.models import Compte, Ecriture, Journal, LigneEcriture, SectionAnalytique
    from apps.core.models import Exercice
    from apps.transport.models import Vehicule

    if local.role != local.SIEGE:
        raise SansObjet("écritures consolidées au siège seulement")
    date = datetime.date.fromisoformat(p["date"])
    exercice = Exercice.objects.filter(date_debut__lte=date, date_fin__gte=date).first()
    if exercice is None:
        raise Attente(f"aucun exercice ouvert au {date:%d/%m/%Y} au siège")
    if exercice.cloture:
        raise Conflit(f"exercice clôturé au siège pour une écriture du {date:%d/%m/%Y}")
    j = p["journal"]
    code_journal = f"{j['code']}-{origine.code}"[:10]
    tresorerie = (Compte.objects.get_or_create(numero=j["tresorerie"], defaults={"intitule": j["intitule"][:200]})[0]
                  if j.get("tresorerie") else None)
    journal = Journal.objects.get_or_create(code=code_journal, defaults={
        "intitule": f"{j['intitule']} - {origine.nom}"[:100], "type_journal": j["type"], "compte_tresorerie": tresorerie})[0]
    e = Ecriture.objects.filter(uid=p["uid"]).first()
    if e is not None and not e.site_origine:
        raise SansObjet("écriture créée dans ce dossier")
    if e is None:
        e = Ecriture(uid=p["uid"], site_origine=origine.code)
    e.journal, e.exercice, e.date, e.statut = journal, exercice, date, Ecriture.STATUT_VALIDEE
    e.numero, e.libelle = f"{origine.code}-{p['numero']}"[:30], p["libelle"][:200]
    e.reference, e.origine = (p.get("reference") or "")[:50], (p.get("origine") or "")[:50]
    e.save()
    e.lignes.all().delete()
    section_site = SectionAnalytique.objects.get_or_create(
        code=f"AG-{origine.code}"[:20], defaults={"plan": "Agences", "intitule": f"Agence {origine.nom}"[:100]})[0]
    lignes = []
    for l in p["lignes"]:
        compte = Compte.objects.get_or_create(numero=l["compte"], defaults={"intitule": (l.get("intitule") or l["compte"])[:200]})[0]
        tiers = None
        if l.get("tiers"):
            t = l["tiers"]
            tiers = Tiers.objects.get_or_create(code=f"{origine.code}.{t['code']}"[:20], defaults={
                "nom": f"{t['nom']} ({origine.code})"[:100], "type_tiers": t["type"]})[0]
        section = (SectionAnalytique.objects.get_or_create(code=l["section"]["code"], defaults={
            "plan": l["section"]["plan"], "intitule": l["section"]["intitule"]})[0] if l.get("section") else section_site)
        vehicule = Vehicule.objects.filter(uid=l["vehicule"]).first() if l.get("vehicule") else None
        lignes.append(LigneEcriture(ecriture=e, compte=compte, tiers=tiers, section=section, vehicule=vehicule,
                                    libelle=(l.get("libelle") or "")[:200],
                                    debit=Decimal(l["debit"]), credit=Decimal(l["credit"]), lettrage=l.get("lettrage") or ""))
    LigneEcriture.objects.bulk_create(lignes)
    if sum(l.debit for l in lignes) != sum(l.credit for l in lignes):
        raise Conflit("écriture déséquilibrée")


INTEGRATIONS = {"agence": _agence, "gare": _gare, "ligne": _ligne, "vehicule": _vehicule, "chauffeur": _chauffeur,
                "depart": _depart, "billet": _billet, "colis": _colis, "colis_livraison": _colis_livraison,
                "depart_arrivee": _depart_arrivee, "depense": _depense, "ecriture": _ecriture,
                "troncon_affecte": _troncon_affecte, "troncon_effectue": _troncon_effectue}

# Ordre d'intégration d'un même lot : les référentiels avant les faits qui les utilisent
PRIORITE = {"agence": 0, "gare": 1, "vehicule": 1, "chauffeur": 1, "ligne": 2, "depart": 3, "billet": 4, "colis": 4,
            "depense": 4, "colis_livraison": 5, "depart_arrivee": 5, "troncon_affecte": 5, "troncon_effectue": 5,
            "ecriture": 6}

# Faits qu'une agence doit connaître quand ils viennent d'une autre agence (relais par le siège)
RELAYES = {"agence", "gare", "ligne", "vehicule", "chauffeur", "depart", "colis", "colis_livraison", "depart_arrivee",
           "billet", "troncon_affecte", "troncon_effectue"}
