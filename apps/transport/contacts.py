"""Annuaire local, droits du guichet et enregistrement idempotent des formulaires rapides."""
import hashlib
import json
import uuid

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse

from .contacts_normalisation import nom_normalise, telephone_normalise
from .models_contacts import PersonneGuichet, SaisieGuichet

SEL = "transport.saisie-rapide.v1"


def nouveau_jeton(utilisateur, genre):
    return signing.dumps({"cle": str(uuid.uuid4()), "utilisateur": utilisateur.pk, "genre": genre}, salt=SEL)


def enregistrer_une_fois(request, genre, enregistrer):
    jeton = request.POST.get("cle_saisie", "")
    if not jeton:
        if request.POST.get("interface_rapide"):
            raise ValidationError("Le formulaire a expiré : ouvrez une nouvelle saisie.")
        # Compatibilité des anciens clients ; la nouvelle interface fournit toujours un jeton.
        with transaction.atomic():
            return enregistrer()
    try:
        d = signing.loads(jeton, salt=SEL, max_age=12 * 3600)
        cle = uuid.UUID(d["cle"])
        if d["utilisateur"] != request.user.pk or d["genre"] != genre:
            raise ValueError
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        raise ValidationError("Le formulaire a expiré ou n'appartient pas à cet utilisateur : ouvrez une nouvelle saisie.")
    contenu = {k: v for k, v in request.POST.items() if k not in (
        "cle_saisie", "csrfmiddlewaretoken", "interface_rapide", "imprimer", "suivant")}
    empreinte = hashlib.sha256(json.dumps(contenu, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    with transaction.atomic():
        operation, _ = SaisieGuichet.objects.get_or_create(cle=cle, defaults={
            "genre": genre, "utilisateur": request.user, "empreinte": empreinte})
        operation = SaisieGuichet.objects.select_for_update().get(pk=operation.pk)
        if (operation.utilisateur_id != request.user.pk or operation.genre != genre
                or operation.empreinte != empreinte):
            raise ValidationError("Cette saisie a déjà été enregistrée avec d'autres informations. Ouvrez le passager ou colis suivant.")
        resultat = getattr(operation, genre)
        if resultat is not None:
            return resultat
        resultat = enregistrer()
        setattr(operation, genre, resultat)
        operation.save(update_fields=[genre])
        return resultat


def memoriser(nom, telephone, piece_identite="", utilisateur=None, personne=None):
    tel, n = telephone_normalise(telephone), nom_normalise(nom)
    if not tel or not n:
        return None
    candidats = PersonneGuichet.objects.filter(telephone_normalise=tel, nom_normalise=n)
    if personne is not None:
        personne = candidats.filter(pk=personne.pk).first()
        if personne is None:
            raise ValidationError("Les coordonnées sélectionnées ne correspondent plus au téléphone et au nom saisis.")
    else:
        exacts = candidats.filter(piece_identite=piece_identite) if piece_identite else candidats
        trouves = list(exacts[:2])
        personne = trouves[0] if len(trouves) == 1 else None
    if personne is None:
        personne = PersonneGuichet(nom=nom.strip(), telephone=telephone.strip(), telephone_normalise=tel,
                                   nom_normalise=n, cree_par=utilisateur)
    personne.nom = nom.strip()
    personne.telephone = telephone.strip()
    if piece_identite:
        personne.piece_identite = piece_identite.strip()
    personne.modifie_par = utilisateur
    personne.save()
    return personne


def verifier_droit(utilisateur, service, nature="COLIS"):
    from apps.core import droits as d

    nom_url = "transport:billet_vente" if service == "billetterie" else "transport:colis_create"
    chemin = reverse(nom_url)
    module = d.module_de(chemin)
    if module is None:
        raise PermissionDenied
    droits = d.Droits(utilisateur, module)
    code = ("billetterie.vendre" if service == "billetterie" else
            {"COLIS": "colis.enregistrer", "COURRIER": "colis.courrier", "FRET": "colis.fret"}.get(nature))
    if droits.acces == d.AUCUN or code is None or not droits.permet(code, d.ECRIRE):
        raise PermissionDenied


def rechercher(telephone="", nom="", avec_piece=False):
    tel, n = telephone_normalise(telephone), nom_normalise(nom)
    if telephone.strip() and not tel:
        return {"personnes": [], "limite": False}
    if not tel and len(n) < 3:
        return {"personnes": [], "limite": False}
    qs = PersonneGuichet.objects.all()
    if tel:
        qs = qs.filter(telephone_normalise=tel)
    if n:
        qs = qs.filter(nom_normalise__contains=n)
    personnes = list(qs.order_by("-modifie_le", "nom", "pk")[:11])
    return {"personnes": [{"id": str(p.pk), "nom": p.nom, "telephone": p.telephone,
                           **({"piece_identite": p.piece_identite} if avec_piece else {})} for p in personnes[:10]],
            "limite": len(personnes) > 10}
