"""Opérations sur le poste serveur, proposées à l'écran « Administration du poste ».

Elles ne concernent que le programme compilé (ERP-OHADA-<Édition>.exe) : c'est lui qui les enregistre ici au
démarrage (sauvegarde de la base, restauration au prochain démarrage, simulation, démarrage avec Windows…).
Lancé autrement (serveur de développement, tests), le registre est vide et l'écran le dit.
"""
ACTIONS = {}


def disponible():
    return bool(ACTIONS)


def appeler(nom, *args, **kwargs):
    action = ACTIONS.get(nom)
    if action is None:
        raise RuntimeError("opération disponible seulement dans le programme compilé")
    return action(*args, **kwargs)


def local(request):
    """La requête vient-elle du serveur lui-même ? (création du premier compte administrateur)"""
    return request.META.get("REMOTE_ADDR", "") in ("127.0.0.1", "::1")
