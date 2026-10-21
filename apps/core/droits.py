"""Autorisations d'accès par menu, comme Fichier › Autorisations d'accès de Sage 100.

Un profil (groupe Django) reçoit, pour chaque menu, élément, sous-élément… de chaque logiciel, l'un des
quatre niveaux ci-dessous. Un élément sans réglage hérite de son parent (le menu Fichier, Structure… est la
racine) ; sans aucun réglage, tout est autorisé. Le super-utilisateur a toujours tous les droits.

Le contrôle est fait côté serveur (middleware) : une page interdite n'est pas affichée, une saisie ou une
suppression refusée n'est pas enregistrée, même si l'on tape l'adresse à la main.
"""
from django.urls import Resolver404, resolve

TOUT = "TOUT"
SANS_SUPPRESSION = "SANS_SUPPRESSION"
LECTURE = "LECTURE"
INTERDIT = "INTERDIT"
NIVEAUX = [
    (TOUT, "Tout autoriser"),
    (SANS_SUPPRESSION, "Interdire la suppression"),
    (LECTURE, "Interdire l'écriture"),
    (INTERDIT, "Tout interdire"),
]
LIBELLES = dict(NIVEAUX)

# Opérations demandées par une requête
CONSULTER, ECRIRE, SUPPRIMER = "consulter", "écrire", "supprimer"
AUTORISE = {
    TOUT: {CONSULTER, ECRIRE, SUPPRIMER},
    SANS_SUPPRESSION: {CONSULTER, ECRIRE},
    LECTURE: {CONSULTER},
    INTERDIT: set(),
}
SUPPRESSIONS = ("supprimer", "annuler", "delettrage")         # noms d'URL qui détruisent ou annulent


# ---------------------------------------------------------------------------
# Arbre des menus d'un logiciel
# ---------------------------------------------------------------------------
def arbre(module):
    """[(onglet, [(element, profondeur)…])…] et {code: code_parent} pour l'héritage."""
    parents, onglets = {}, []

    def parcourir(elements, parent, profondeur, sortie):
        for el in elements:
            if el.separateur:
                continue
            parents[el.code] = parent
            sortie.append((el, profondeur))
            parcourir(el.tous_enfants(), el.code, profondeur + 1, sortie)

    for onglet in module.onglets:
        lignes = []
        parcourir(onglet.elements, onglet.code, 1, lignes)
        onglets.append((onglet, lignes))
    return onglets, parents


def profil_de(utilisateur):
    return utilisateur.groups.order_by("name").first()


class Droits:
    """Droits effectifs d'un utilisateur dans un logiciel (calculés une fois par requête)."""

    def __init__(self, utilisateur, module):
        from .models import DroitAcces

        self.module = module
        self.total = utilisateur.is_superuser
        self.profil = None if self.total else profil_de(utilisateur)
        self.reglages = {}
        if self.profil is not None:
            self.reglages = dict(DroitAcces.objects.filter(groupe=self.profil, module=module.code)
                                 .values_list("code", "niveau"))
        self._parents = None

    @property
    def parents(self):
        if self._parents is None:
            self._parents = arbre(self.module)[1]
        return self._parents

    def niveau(self, code):
        if self.total or not self.reglages:
            return TOUT
        while code:
            if code in self.reglages:
                return self.reglages[code]
            code = self.parents.get(code)
        return TOUT

    def permet(self, code, operation):
        return operation in AUTORISE[self.niveau(code)]


# ---------------------------------------------------------------------------
# Quelle entrée de menu correspond à une page ?
# ---------------------------------------------------------------------------
def _par_nom_url(module):
    index = {}
    for _, lignes in arbre(module)[0]:
        for el, _ in lignes:
            if el.url:
                index.setdefault(el.url, el.code)
    return index


def _code_document(type_document):
    from apps.commercial.models import Document

    domaine = ("ventes" if type_document in Document.TYPES_VENTE else
               "achats" if type_document in Document.TYPES_ACHAT else "stocks")
    return f"{domaine}.{type_document.lower()}"


def element_de_la_page(request, module, element_actif=None):
    """Code de l'entrée de menu dont dépend la page (None si la page n'en dépend d'aucune)."""
    if element_actif:
        return element_actif["code"]
    try:
        match = resolve(request.path_info)
    except Resolver404:
        return None
    nom, kwargs = match.view_name, match.kwargs
    court = nom.split(":")[-1]
    from apps.commercial.models import Document, Tiers

    if court.startswith("document_"):
        if "type_document" in kwargs:
            return _code_document(kwargs["type_document"])
        doc = Document.objects.filter(pk=kwargs.get("pk")).only("type_document").first()
        return _code_document(doc.type_document) if doc else None
    if court.startswith("tiers_"):
        tiers = Tiers.objects.filter(pk=kwargs.get("pk")).only("type_tiers").first() if "pk" in kwargs else None
        type_tiers = tiers.type_tiers if tiers else request.GET.get("type", Tiers.CLIENT)
        return "tiers.clients" if type_tiers == Tiers.CLIENT else "tiers.fournisseurs"
    index = _par_nom_url(module)
    if court.startswith("structure_") and "structure" in kwargs:
        codes = {"taxes": "structure.taux_taxes", "banques": "structure.banques", "sections": "structure.plan_analytique"}
        return codes.get(kwargs["structure"])
    equivalents = {"delettrage": "lettrage", "stock_comptabiliser": "stock", "journal_create": "journaux",
                   "journal_update": "journaux", "article_parametres": "articles"}
    if court in equivalents:
        return index.get(f"{module.code}:{equivalents[court]}")
    for suffixe in ("_create", "_update", "_detail"):
        if court.endswith(suffixe):
            racine = court[: -len(suffixe)]
            for liste in (racine + "s", racine + "x", racine):
                if f"{module.code}:{liste}" in index:
                    return index[f"{module.code}:{liste}"]
    return index.get(nom)


def operation_demandee(request):
    try:
        court = resolve(request.path_info).url_name or ""
    except Resolver404:
        court = ""
    if any(mot in court for mot in SUPPRESSIONS) and request.method == "POST":
        return SUPPRIMER
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        return ECRIRE
    if court.endswith(("_create", "_update")) or court in ("article_parametres",):
        return ECRIRE              # ouvrir un formulaire de saisie, c'est déjà écrire
    return CONSULTER


def url_permise(droits, url):
    """La page d'une URL du logiciel est-elle accessible (en saisie s'il s'agit d'un formulaire) ?"""
    from types import SimpleNamespace
    from urllib.parse import urlsplit

    from django.http import QueryDict

    from .navigation import structure_module

    morceaux = urlsplit(url)
    requete = SimpleNamespace(path_info=morceaux.path, path=morceaux.path, GET=QueryDict(morceaux.query), method="GET")
    if module_de(morceaux.path) is not droits.module:
        return True
    _, actif = structure_module(droits.module, morceaux.path, requete.GET)
    code = element_de_la_page(requete, droits.module, actif)
    return code is None or droits.permet(code, operation_demandee(requete))


def module_de(chemin):
    from .navigation import module_pour_chemin

    return module_pour_chemin(chemin)


def annoter(noeuds, droits):
    """Marque les entrées interdites dans l'arbre des menus (grisées, cadenas, sans lien)."""
    for n in noeuds:
        if n.get("separateur"):
            continue
        niveau = droits.niveau(n["code"])
        n["droit"] = niveau
        if niveau == INTERDIT and not n.get("action"):
            n.update(url=None, disponible=False, interdit=True)
        annoter(n["enfants"], droits)


# ---------------------------------------------------------------------------
# API REST (client bureau) : mêmes droits que la version web
# ---------------------------------------------------------------------------
from rest_framework.permissions import SAFE_METHODS, BasePermission  # noqa: E402


class DroitsMenusAPI(BasePermission):
    message = "Opération refusée par vos autorisations d'accès."
    # ressource → (logiciel, nom d'URL de la liste correspondante dans les menus)
    RESSOURCES = {"tiers": ("commercial", None), "article": ("commercial", "commercial:articles"),
                  "documents": ("commercial", None), "reglement": ("commercial", "commercial:reglements"),
                  "compte": ("comptabilite", "comptabilite:comptes"), "journal": ("comptabilite", "comptabilite:journaux"),
                  "ecriture": ("comptabilite", "comptabilite:ecritures")}

    def _operation(self, request, view):
        if request.method in SAFE_METHODS:
            return CONSULTER
        if request.method == "DELETE" or "annuler" in (getattr(view, "action", "") or ""):
            return SUPPRIMER
        return ECRIRE

    def _code(self, request, view, obj=None):
        from apps.commercial.models import Tiers
        from .navigation import MODULES_PAR_CODE

        ressource = getattr(view, "basename", None)
        logiciel, liste = self.RESSOURCES.get(ressource, (None, None))
        if logiciel is None:
            return None, None
        module = MODULES_PAR_CODE[logiciel]
        if ressource == "documents":
            if obj is not None:
                type_document = obj.type_document
            elif request.method in SAFE_METHODS:
                type_document = request.query_params.get("type")
            else:
                type_document = request.data.get("type_document")
            if type_document:
                return module, _code_document(type_document)
            domaine = request.query_params.get("domaine")
            return module, (f"{domaine}.tous" if domaine else None)
        if ressource == "tiers":
            type_tiers = getattr(obj, "type_tiers", None) or request.data.get("type_tiers") or request.query_params.get("type")
            if not type_tiers:
                return module, None
            return module, "tiers.clients" if type_tiers == Tiers.CLIENT else "tiers.fournisseurs"
        return module, _par_nom_url(module).get(liste)

    def _verifier(self, request, view, obj=None):
        module, code = self._code(request, view, obj)
        if module is None or code is None:
            return True
        return Droits(request.user, module).permet(code, self._operation(request, view))

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return self._verifier(request, view)

    def has_object_permission(self, request, view, obj):
        return self._verifier(request, view, obj)
