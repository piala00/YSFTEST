"""Demandes de correction : la direction signale une erreur dans la comptabilité d'une agence, l'agence corrige.

  Direction (siège)                              Agence
  demander()  ── fait « correction_demande » ──▶  copie reçue, statut RECUE, accusé de réception
              ◀── fait « correction_suivi » ────  repondre() : CORRIGEE (écritures rattachées) ou CONTESTEE
  la demande passe à CORRIGEE quand les écritures de correction de l'agence sont arrivées au siège.

La direction n'écrit jamais dans les comptes d'une agence ; une écriture validée n'est jamais modifiée (l'agence
corrige par extourne puis bonne écriture, qui remontent comme toutes ses écritures).
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import DemandeCorrection
from .publication import hors_import, publier, site_local


def _numero():
    from apps.core.models import Sequence

    seq, _ = Sequence.objects.select_for_update().get_or_create(code="CORRECTIONS", annee=0)
    seq.dernier_numero += 1
    seq.save(update_fields=["dernier_numero"])
    return f"DC{seq.dernier_numero:05d}"


def charge_demande(d):
    return {"v": 1, "uid": str(d.uid), "numero": d.numero, "pour_agence": d.agence, "ecriture": str(d.ecriture_uid),
            "ecriture_numero": d.ecriture_numero, "ecriture_date": d.ecriture_date.isoformat() if d.ecriture_date else None,
            "ecriture_libelle": d.ecriture_libelle, "motif": d.motif, "correction_attendue": d.correction_attendue,
            "demandee_par": d.demandee_par, "demandee_le": d.demandee_le.isoformat() if d.demandee_le else None,
            "echeance": d.echeance.isoformat() if d.echeance else None, "statut": d.statut,
            "annulee_motif": d.annulee_motif}


def charge_suivi(d):
    return {"v": 1, "demande": str(d.uid), "statut": d.statut, "reponse": d.reponse, "repondu_par": d.repondu_par,
            "repondu_le": d.repondu_le.isoformat() if d.repondu_le else None, "ecritures": list(d.ecritures_correction)}


@transaction.atomic
def demander(ecriture, motif, correction_attendue="", par="", echeance=None):
    """Au siège, sur une écriture reçue d'une agence (consolidation)."""
    local = site_local()
    if local is None or local.role != local.SIEGE:
        raise ValidationError("Seule la direction (siège) demande une correction à une agence.")
    if not ecriture.site_origine:
        raise ValidationError("Cette écriture a été passée à la direction : corrigez-la ici, par extourne.")
    if not (motif or "").strip():
        raise ValidationError("Indiquez l'erreur constatée.")
    numero = ecriture.numero.split("-", 1)[1] if ecriture.numero.startswith(f"{ecriture.site_origine}-") else ecriture.numero
    d = DemandeCorrection.objects.create(
        numero=_numero(), agence=ecriture.site_origine, ecriture_uid=ecriture.uid, ecriture_numero=numero,
        ecriture_date=ecriture.date, ecriture_libelle=ecriture.libelle[:200], motif=motif.strip(),
        correction_attendue=(correction_attendue or "").strip(), demandee_par=str(par or "")[:150],
        demandee_le=timezone.now(), echeance=echeance)
    publier("correction_demande", d.uid, charge_demande(d), "DEMANDE", d.ecriture_date, d.demandee_par)
    return d


@transaction.atomic
def annuler(demande, par="", motif=""):
    """Au siège : la direction retire sa demande (erreur de sa part, ou corrigée autrement)."""
    if demande.site_origine:
        raise ValidationError("Seule la direction qui a fait la demande peut l'annuler.")
    if not demande.ouverte and demande.statut != DemandeCorrection.CONTESTEE:
        raise ValidationError("Cette demande est déjà close.")
    demande.statut = DemandeCorrection.ANNULEE
    demande.annulee_motif = (motif or f"Annulée par {par}")[:200]
    demande.save(update_fields=["statut", "annulee_motif"])
    publier("correction_demande", demande.uid, charge_demande(demande), "ANNULE", demande.ecriture_date, str(par or ""))


@transaction.atomic
def repondre(demande, statut, reponse="", par="", ecritures=()):
    """À l'agence : CORRIGEE (avec ses écritures de correction validées) ou CONTESTEE (avec une réponse)."""
    from apps.comptabilite.models import Ecriture

    if not demande.site_origine:
        raise ValidationError("Répondre à une demande se fait dans l'agence concernée.")
    if not demande.ouverte:
        raise ValidationError("Cette demande n'attend plus de réponse.")
    if statut == DemandeCorrection.CORRIGEE:
        ecritures = list(ecritures)
        if not ecritures:
            raise ValidationError("Choisissez au moins une écriture de correction (extourne et bonne écriture).")
        if any(e.site_origine or e.statut != Ecriture.STATUT_VALIDEE for e in ecritures):
            raise ValidationError("Les écritures de correction doivent être des écritures validées de cette agence.")
    elif statut == DemandeCorrection.CONTESTEE:
        if not (reponse or "").strip():
            raise ValidationError("Expliquez pourquoi l'écriture est juste.")
    else:
        raise ValidationError("Réponse inconnue.")
    demande.statut, demande.reponse = statut, (reponse or "").strip()
    demande.repondu_par, demande.repondu_le = str(par or "")[:150], timezone.now()
    demande.ecritures_correction = [str(e.uid) for e in ecritures] if statut == DemandeCorrection.CORRIGEE else []
    demande.save()
    publier("correction_suivi", demande.uid, charge_suivi(demande), statut, None, demande.repondu_par)
    return demande


def accuser_reception(demande):
    """À l'agence, à l'intégration de la demande : la direction voit qu'elle est arrivée."""
    if demande.statut != DemandeCorrection.DEMANDEE:
        return
    demande.statut = DemandeCorrection.RECUE
    demande.save(update_fields=["statut"])
    with hors_import():
        publier("correction_suivi", demande.uid, charge_suivi(demande), DemandeCorrection.RECUE)


def ouvertes():
    """Demandes qui attendent l'agence (à la direction : toutes les agences ; à l'agence : les siennes)."""
    return DemandeCorrection.objects.filter(statut__in=DemandeCorrection.OUVERTS)
