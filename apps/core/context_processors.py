from .models import Exercice, Societe
from .navigation import MODULES, chemin_vers_actif, module_pour_chemin, structure_module


def societe(request):
    if not request.user.is_authenticated:
        return {}
    contexte = {"societe": Societe.get(), "exercice_courant": Exercice.courant(), "modules": MODULES}
    module = module_pour_chemin(request.path)
    if module is None:
        return contexte

    onglets, element_actif = structure_module(module, request.path, request.GET)
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
    contexte.update(module=module, onglets=onglets, onglet_actif=actif, element_actif=element_actif,
                    fil_ariane=chemin_vers_actif(actif["elements"]))
    return contexte
