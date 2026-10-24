from django.urls import reverse

from .droits import Droits, annoter
from .models import Exercice, Societe
from .navigation import MODULES, barre_verticale, chemin_vers_actif, module_pour_chemin, structure_module


def fenetres_a_actualiser(request, *chemins):
    """Après un enregistrement : les fenêtres ouvertes sur ces pages (ex. factures réglées) se rechargent."""
    request.session["erp_actualiser"] = list(dict.fromkeys(request.session.get("erp_actualiser", []) + list(chemins)))


def societe(request):
    if not request.user.is_authenticated:
        return {}
    from .selection import resume

    fiche = Societe.get()
    contexte = {"societe": fiche, "exercice_courant": Exercice.courant(), "modules": MODULES,
                "selection": resume(request), "erp_actualiser": request.session.pop("erp_actualiser", None)}
    if fiche.source_mode == Societe.SYNCHRO_MIROIR:
        from .models import LotSynchronisation

        contexte["derniere_synchro"] = LotSynchronisation.objects.filter(applique=True, conforme=True).first()
    module = module_pour_chemin(request.path)
    if module is None:
        return contexte

    navigation = getattr(request, "navigation", None)
    if navigation and navigation[0] is module:
        onglets, element_actif = navigation[1], navigation[2]
    else:
        onglets, element_actif = structure_module(module, request.path, request.GET)
    droits = getattr(request, "droits", None) or Droits(request.user, module)
    if not droits.libre:
        for o in onglets:
            annoter(o["elements"], droits)
    cle_session = f"onglet_{module.code}"
    actif = next((o for o in onglets if o["contient_actif"]), None)
    if actif is None:
        # Page sans entrée de menu (fiche, détail…) : on reste sur le dernier onglet utilisé
        actif = next((o for o in onglets if o["code"] == request.session.get(cle_session)), None)
        if actif is None and request.GET.get("onglet"):
            actif = next((o for o in onglets if o["code"] == request.GET["onglet"]), None)
    if actif is None:
        # Par défaut, comme dans Sage, on présente le menu Traitement (ou État pour le Reporting)
        actif = next((o for o in onglets if o["code"] in ("traitement", "etat")), onglets[0])
    request.session[cle_session] = actif["code"]
    arbre = actif
    if actif["code"] in ("edition", "fenetre", "aide"):
        # Commandes d'interface (page d'accueil, à propos…) : la barre verticale présente les menus de travail
        arbre = next((o for o in onglets if o["code"] in ("traitement", "etat")), actif)
    match = getattr(request, "resolver_match", None)
    contexte["est_accueil"] = bool(match and match.view_name == module.accueil)
    groupes = barre_verticale(module)
    if groupes and not droits.libre:
        from .droits import url_permise

        for g in groupes:
            g["liens"] = [l for l in g["liens"] if not l["url"] or url_permise(droits, l["url"])]
    contexte["barre_verticale"] = [g for g in groupes if g["liens"]]
    contexte["accueils"] = [reverse(m.accueil) for m in MODULES]
    contexte.update(module=module, onglets=onglets, onglet_actif=actif, onglet_arbre=arbre, element_actif=element_actif,
                    fil_ariane=chemin_vers_actif(actif["elements"]))
    return contexte
