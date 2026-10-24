"""Journal des événements : qui a créé, modifié, validé, annulé ou supprimé quoi, et quand.

Les enregistrements sont captés par les signaux de Django sur les fiches et pièces importantes, que la
modification vienne de la version web, du client bureau (API) ou d'une commande. L'utilisateur est celui
de la requête en cours (vide pour une commande lancée sur le serveur).
"""
import contextvars
import datetime
from decimal import Decimal

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save

_requete = contextvars.ContextVar("requete_erp", default=None)

# Champs recalculés par le logiciel : leur changement n'est pas une action de l'utilisateur
IGNORES = {"stock", "cmup", "total_ht", "total_tva", "total_ttc", "ecriture", "password", "last_login", "cree_le",
           "modifie_le", "date_joined"}


class RequeteCouranteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        jeton = _requete.set(request)
        try:
            return self.get_response(request)
        finally:
            _requete.reset(jeton)


def _utilisateur():
    requete = _requete.get()
    utilisateur = getattr(requete, "user", None)       # DRF recopie l'utilisateur authentifié par jeton
    return utilisateur if getattr(utilisateur, "is_authenticated", False) else None


def _logiciel():
    requete = _requete.get()
    if requete is None:
        return "serveur"
    chemin = requete.path
    if chemin.startswith("/api/"):
        return "bureau (API)"
    from .navigation import module_pour_chemin

    module = module_pour_chemin(chemin)
    return module.titre if module else "web"


def _valeur(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v.normalize()) if v == v.to_integral() else str(v)
    return "" if v is None else str(v)


def _photo(objet):
    return {f.attname: _valeur(getattr(objet, f.attname)) for f in objet._meta.concrete_fields
            if f.attname not in IGNORES and not f.primary_key}


def enregistrer(action, objet=None, details=None, libelle=""):
    from .models import JournalEvenement

    JournalEvenement.objects.create(
        utilisateur=_utilisateur(), logiciel=_logiciel()[:30], action=action,
        objet_type=objet._meta.verbose_name.capitalize()[:60] if objet is not None else "",
        objet_id=str(objet.pk) if objet is not None else "",
        objet_libelle=(libelle or (str(objet) if objet is not None else ""))[:200], details=details or {})


def _avant(sender, instance, raw=False, **kwargs):
    if raw:                                  # chargement d'une sauvegarde : pas une action d'utilisateur
        return
    # Auteur d'origine : l'utilisateur connecté, enregistré côté serveur (jamais choisi dans une liste)
    if instance._state.adding and hasattr(instance, "cree_par_id") and instance.cree_par_id is None:
        instance.cree_par = _utilisateur()
    if instance.pk:
        ancien = sender.objects.filter(pk=instance.pk).first()
        instance._journal_avant = _photo(ancien) if ancien else None


def _apres(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    if created:
        enregistrer("CREATION", instance)
        return
    avant = getattr(instance, "_journal_avant", None)
    if avant is None:
        return
    apres = _photo(instance)
    changes = {k: [avant.get(k), v] for k, v in apres.items() if avant.get(k) != v}
    if not changes:
        return
    action = "MODIFICATION"
    statut = changes.get("statut")
    if statut:
        action = {"VALIDE": "VALIDATION", "VALIDEE": "VALIDATION", "ANNULE": "ANNULATION"}.get(statut[1], action)
    if "cloture" in changes and changes["cloture"][1] == "True":
        action = "CLOTURE"
    enregistrer(action, instance, {"champs": changes})


def _suppression(sender, instance, **kwargs):
    enregistrer("SUPPRESSION", instance, {"fiche": _photo(instance)})


def suivre(*modeles):
    for modele in modeles:
        pre_save.connect(_avant, sender=modele, dispatch_uid=f"journal_avant_{modele.__name__}")
        post_save.connect(_apres, sender=modele, dispatch_uid=f"journal_apres_{modele.__name__}")
        post_delete.connect(_suppression, sender=modele, dispatch_uid=f"journal_suppr_{modele.__name__}")


def connecter():
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    from apps.commercial import models as c
    from apps.comptabilite import models as k

    from .models import Agence, DroitAcces, Exercice, Societe

    suivre(Societe, Exercice, DroitAcces, get_user_model(), Group,
           c.Tiers, c.Article, c.FamilleArticle, c.Depot, c.CategorieTarifaire, c.Document, c.Reglement, c.Inventaire,
           c.OperationCaisse, c.PointageFiche, Agence, k.Compte, k.Journal, k.Ecriture, k.Taxe, k.Banque, k.SectionAnalytique)
    user_logged_in.connect(lambda sender, request, user, **kw: enregistrer("CONNEXION", user, libelle=user.username),
                           dispatch_uid="journal_connexion", weak=False)
    user_login_failed.connect(
        lambda sender, credentials, request=None, **kw: enregistrer(
            "ECHEC_CONNEXION", libelle=str(credentials.get("username", ""))),
        dispatch_uid="journal_echec", weak=False)
