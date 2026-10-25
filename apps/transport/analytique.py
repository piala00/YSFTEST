"""Comptabilité analytique : deux rubriques de restitution, Véhicules et Propriétaires (skills comptabilité
générale/analytique et « source unique »).

Règle : tout montant vient d'une ligne d'écriture GÉNÉRALE VALIDÉE qui porte le véhicule. Aucun montant n'est créé
ici ; on regroupe et on rapproche. Les lignes de charges et produits sans véhicule restent « non affectées » et sont
montrées. Les kilomètres, voyages et voyageurs sont des données d'exploitation, affichées à part.
"""
from collections import OrderedDict
from decimal import Decimal

ZERO = Decimal("0")

PRODUITS = [("billetterie", "Billetterie (voyageurs transportés)"), ("bagages", "Bagages payants"),
            ("colis", "Colis, courrier et fret transportés"), ("autres_produits", "Autres produits")]
CHARGES = [("carburant", "Carburant"), ("route", "Péages et frais de route"), ("garage", "Garage : pièces et réparations"),
           ("personnel", "Personnel affecté"), ("charges_vehicule", "Assurance et autres charges du véhicule")]


def _lignes(debut, fin, site=None):
    """Lignes de charges (6) et produits (7) des écritures validées de la période."""
    from django.db.models import Q

    from apps.comptabilite.models import Ecriture, LigneEcriture

    qs = (LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE, ecriture__date__range=(debut, fin))
          .filter(Q(compte__numero__startswith="6") | Q(compte__numero__startswith="7"))
          .select_related("compte", "ecriture", "vehicule"))
    if site is not None:
        qs = qs.filter(ecriture__site_origine=site)
    return qs


def _rubrique(numero, p, remuneration):
    """Rubrique analytique d'un compte de charge ou de produit (comptes paramétrés du transport)."""
    n = lambda c: getattr(c, "numero", None)                      # noqa: E731
    if numero.startswith("7"):
        if numero == n(p.compte_billets):
            return "billetterie"
        if numero in (n(p.compte_colis), n(p.compte_fret)):
            return "colis"
        return "autres_produits"
    if numero == remuneration:
        return "proprietaire"
    if numero == n(p.compte_carburant) or numero.startswith("605"):
        return "carburant"
    if numero.startswith(("638", "618")):
        return "route"
    if numero in (n(p.compte_pieces), n(p.compte_main_oeuvre)) or numero.startswith("624"):
        return "garage"
    if numero.startswith("66"):
        return "personnel"
    return "charges_vehicule"


def _vide():
    return {**{k: ZERO for k, _ in PRODUITS + CHARGES}, "proprietaire": ZERO}


def _totaliser(g):
    g["produits"] = sum((g[k] for k, _ in PRODUITS), ZERO)
    g["charges"] = sum((g[k] for k, _ in CHARGES), ZERO)
    g["resultat"] = g["produits"] - g["charges"]                  # résultat d'exploitation du véhicule
    g["resultat_societe"] = g["resultat"] - g["proprietaire"]     # après la part du propriétaire (622)
    return g


class _Gammes:
    """Flotte d'un véhicule à une date, avec cache de l'historique."""

    def __init__(self):
        self.cache = {}

    def __call__(self, vehicule, jour):
        cle = (vehicule.pk, jour)
        if cle not in self.cache:
            self.cache[cle] = vehicule.gamme_le(jour)
        return self.cache[cle]


def _contrats_par_vehicule(debut, fin):
    from apps.partenaires.models import ContratPartenaire

    contrats = {}
    for c in (ContratPartenaire.objects.exclude(statut=ContratPartenaire.BROUILLON).filter(debut__lte=fin)
              .select_related("partenaire").order_by("debut")):
        if c.fin is None or c.fin >= debut:
            contrats.setdefault(c.vehicule_id, []).append(c)
    return contrats


def _contrat_le(contrats, vehicule_id, jour):
    for c in contrats.get(vehicule_id, []):
        if c.debut <= jour and (c.fin is None or c.fin >= jour):
            return c
    return None


def vehicules(debut, fin, gamme="", site=None):
    """Compte d'exploitation analytique de chaque véhicule, et rapprochement avec la comptabilité générale."""
    from apps.partenaires.models import compte_remuneration

    from .models import ParametresTransport, Vehicule

    p, remuneration = ParametresTransport.get(), compte_remuneration().numero
    gammes = _Gammes()
    lignes = OrderedDict()
    controle = {"produits_gl": ZERO, "charges_gl": ZERO, "produits_affectes": ZERO, "charges_affectees": ZERO,
                "nb_non_affectees": 0}
    for l in _lignes(debut, fin, site):
        montant = l.credit - l.debit if l.compte.numero.startswith("7") else l.debit - l.credit
        cle_gl = "produits_gl" if l.compte.numero.startswith("7") else "charges_gl"
        controle[cle_gl] += montant
        if l.vehicule_id is None:
            controle["nb_non_affectees"] += 1
            continue
        controle["produits_affectes" if cle_gl == "produits_gl" else "charges_affectees"] += montant
        g_veh = gammes(l.vehicule, l.ecriture.date)
        if gamme and g_veh != gamme:
            continue
        g = lignes.setdefault(l.vehicule_id, {"vehicule": l.vehicule, "gamme": g_veh, **_vide()})
        g[_rubrique(l.compte.numero, p, remuneration)] += montant
    for v in Vehicule.objects.filter(actif=True).exclude(pk__in=lignes):
        if not gamme or gammes(v, fin) == gamme:
            lignes[v.pk] = {"vehicule": v, "gamme": gammes(v, fin), **_vide()}
    resultat = sorted((_totaliser(g) for g in lignes.values()), key=lambda g: g["vehicule"].immatriculation)
    total = _totaliser({k: sum((g[k] for g in resultat), ZERO) for k in _vide()})
    controle["produits_non_affectes"] = controle["produits_gl"] - controle["produits_affectes"]
    controle["charges_non_affectees"] = controle["charges_gl"] - controle["charges_affectees"]
    return {"lignes": resultat, "total": total, "controle": controle}


def compte_vehicule(vehicule, debut, fin):
    """Compte d'exploitation d'un véhicule par rubrique, avec les pièces sources (drill-down)."""
    from apps.partenaires.models import compte_remuneration

    from .models import ParametresTransport

    p, remuneration = ParametresTransport.get(), compte_remuneration().numero
    g, details = _vide(), {}
    for l in _lignes(debut, fin).filter(vehicule=vehicule).order_by("ecriture__date", "ecriture__numero", "pk"):
        montant = l.credit - l.debit if l.compte.numero.startswith("7") else l.debit - l.credit
        r = _rubrique(l.compte.numero, p, remuneration)
        g[r] += montant
        details.setdefault(r, []).append({"ligne": l, "montant": montant})
    return {"totaux": _totaliser(g), "details": details}


def proprietaires(debut, fin, gamme=""):
    """Par propriétaire : portefeuille de véhicules et résultats sur les seuls jours où le contrat les lui attribue
    (jamais d'après le propriétaire actuel), puis la situation financière, séparée : droits calculés (décomptes),
    sommes comptabilisées à son compte, règlements, solde du compte."""
    from apps.partenaires.models import Decompte, ReglementPartenaire, compte_remuneration, solde_partenaire

    from .models import ParametresTransport

    p, remuneration = ParametresTransport.get(), compte_remuneration().numero
    contrats, gammes = _contrats_par_vehicule(debut, fin), _Gammes()
    portefeuilles = OrderedDict()
    for l in _lignes(debut, fin).filter(vehicule__isnull=False):
        c = _contrat_le(contrats, l.vehicule_id, l.ecriture.date)
        g_veh = gammes(l.vehicule, l.ecriture.date)
        if gamme and g_veh != gamme:
            continue
        cle = c.partenaire_id if c else None
        pf = portefeuilles.setdefault(cle, {"partenaire": c.partenaire if c else None, "vehicules": OrderedDict()})
        v = pf["vehicules"].setdefault(l.vehicule_id, {"vehicule": l.vehicule, "gamme": g_veh, "contrats": set(), **_vide()})
        if c:
            v["contrats"].add(f"{c.numero} v{c.version}")
        montant = l.credit - l.debit if l.compte.numero.startswith("7") else l.debit - l.credit
        v[_rubrique(l.compte.numero, p, remuneration)] += montant
    resultat = []
    for cle, pf in portefeuilles.items():
        vehicules = sorted((_totaliser(v) for v in pf["vehicules"].values()), key=lambda v: v["vehicule"].immatriculation)
        for v in vehicules:
            v["contrats"] = ", ".join(sorted(v["contrats"]))
        total = _totaliser({k: sum((v[k] for v in vehicules), ZERO) for k in _vide()})
        finance = None
        if pf["partenaire"] is not None:
            t = pf["partenaire"]
            decomptes = Decompte.objects.filter(contrat__partenaire=t, fin__range=(debut, fin))
            finance = {
                "droits_provisoires": sum((d.montant_du for d in decomptes if d.statut == Decompte.BROUILLON), ZERO),
                "comptabilise": sum((d.montant_du for d in decomptes if d.statut == Decompte.APPROUVE), ZERO),
                "reglements": sum((r.montant for r in ReglementPartenaire.objects.filter(partenaire=t, date__range=(debut, fin))),
                                  ZERO),
                "solde": solde_partenaire(t, jusqua=fin)}
        resultat.append({"partenaire": pf["partenaire"], "vehicules": vehicules, "total": total, "finance": finance})
    resultat.sort(key=lambda r: (r["partenaire"] is None, r["partenaire"].nom if r["partenaire"] else ""))
    return resultat
