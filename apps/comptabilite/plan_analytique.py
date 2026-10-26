"""Plan analytique complet : axes, éléments et états détaillés de la Comptabilité analytique.

Source unique : chaque montant est une ligne de charge (classe 6) ou de produit (classe 7) d'une écriture GÉNÉRALE
VALIDÉE. On ne crée aucun montant ; on attribue chaque ligne aux éléments de chaque axe, puis on regroupe. Ce qui ne
peut pas être attribué reste visible en « Non affecté », et chaque axe se rapproche de la comptabilité générale :
total des éléments + non affecté = produits et charges de la période.

Axes du transport (plan analytique du skill « erp-transport-plan-analytique ») :
  gares (agences de voyage), véhicules, propriétaires, gammes (Classique / VIP), lignes, voyages (départs),
  activités, contrats des propriétaires ; puis chaque plan de sections créé dans Structure › Plan analytique
  (services, projets…). Une société de commerce n'a que ses plans de sections.

Comment une ligne est attribuée :
  véhicule  : porté par la ligne d'écriture ;
  voyage    : la pièce de l'écriture est celle d'un départ, d'un colis, d'un plein, d'une dépense, d'une avance de
              mission ou d'un imprévu rattachés au départ ;
  ligne, gamme : celles du voyage (à défaut, la flotte du véhicule à la date) ;
  gare      : section de gare portée par la ligne, sinon la gare de départ du voyage, sinon l'agence (section AG-)
              quand elle n'a qu'une gare ;
  propriétaire, contrat : contrat du véhicule EN VIGUEUR À LA DATE de l'écriture (jamais le propriétaire actuel) ;
  activité  : produits selon leur compte (voyageurs, bagages, colis…) ; charges des véhicules ou de structure.
"""
import calendar
import datetime
from collections import OrderedDict
from decimal import Decimal

from django.db.models import Q
from django.utils.text import slugify

ZERO = Decimal("0")
NON_AFFECTE = "aucun"

AXES_TRANSPORT = [
    ("gares", "Agences (gares)", "Recettes et charges de chaque gare : ventes constatées au départ, colis, loyers, frais"),
    ("vehicules", "Véhicules", "Compte d'exploitation de chaque car et camion"),
    ("proprietaires", "Propriétaires", "Véhicules des partenaires selon le contrat en vigueur à la date"),
    ("services", "Services", "Billetterie, colis, conduite, garage, administration : produits et coûts de chaque service"),
    ("activites", "Activités", "Voyageurs, bagages, colis et fret, autres produits ; charges des véhicules et de structure"),
    ("gammes", "Gammes (Classique / VIP)", "Flottes distinctes Classique et VIP"),
    ("lignes", "Lignes (itinéraires)", "Résultat de chaque itinéraire"),
    ("voyages", "Voyages (départs)", "Résultat de chaque départ"),
    ("contrats", "Contrats des propriétaires", "Résultat sous chaque contrat"),
]

ETATS = [
    ("exploitation", "Compte d'exploitation"),
    ("comptes", "Détail par compte"),
    ("grand_livre", "Grand-livre analytique"),
    ("evolution", "Évolution"),
    ("croise", "Ventilation croisée"),
    ("comparaison", "Comparaison de périodes"),
    ("journal", "Journal des imputations"),
]

SERVICES_RUBRIQUES = {"billetterie": "BILLETTERIE", "bagages": "BILLETTERIE", "colis": "COLIS", "carburant": "CONDUITE",
                      "route": "CONDUITE", "garage": "GARAGE", "personnel": "CONDUITE"}

ACTIVITES = OrderedDict([
    ("voyageurs", "Transport de voyageurs"), ("bagages", "Bagages payants"), ("colis", "Colis, courrier et fret"),
    ("autres_produits", "Autres produits"), ("exploitation", "Charges d'exploitation des véhicules"),
    ("structure", "Charges de structure (siège, gares, frais généraux)"),
])


# ---------------------------------------------------------------- Période
def lire_periode(params, aujourdhui=None):
    """Période demandée : {du, au, code, erreur}. Du > Au est refusé (message), la période par défaut est gardée."""
    du, au, code = periode(params, aujourdhui)
    erreur = ""
    if not params.get("periode") and not params.get("mois") and params.get("du") and params.get("au") \
            and params.get("du") > params.get("au"):
        erreur = "La date de début est après la date de fin : période non prise en compte."
    return {"du": du, "au": au, "code": code, "erreur": erreur}


def decaler(debut, fin, sens):
    """Période précédente (sens = -1) ou suivante (+1) de même durée ; mois entiers → mois entiers."""
    if debut.day == 1 and fin.day == calendar.monthrange(fin.year, fin.month)[1]:
        mois = (fin.year - debut.year) * 12 + fin.month - debut.month + 1
        rang = debut.year * 12 + debut.month - 1 + sens * mois
        d = datetime.date(rang // 12, rang % 12 + 1, 1)
        rang_fin = rang + mois - 1
        a, m = rang_fin // 12, rang_fin % 12 + 1
        return d, datetime.date(a, m, calendar.monthrange(a, m)[1])
    jours = (fin - debut).days + 1
    return debut + datetime.timedelta(days=sens * jours), fin + datetime.timedelta(days=sens * jours)


def annee_precedente(debut, fin):
    """Même période l'année précédente (N-1)."""
    def recul(d):
        try:
            return d.replace(year=d.year - 1)
        except ValueError:                                         # 29 février
            return d.replace(year=d.year - 1, day=28)
    return recul(debut), recul(fin)


def periode(params, aujourdhui=None):
    """(début, fin, code) d'après ?du=&au=, ?mois=AAAA-MM ou ?periode=jour|hier|semaine|mois|mois_precedent|trimestre|
    annee|exercice."""
    j = aujourdhui or datetime.date.today()
    code = params.get("periode", "")
    if code == "exercice":
        from apps.core.models import Exercice

        e = Exercice.objects.filter(date_debut__lte=j, date_fin__gte=j).first()
        if e:
            return e.date_debut, e.date_fin, code
        return datetime.date(j.year, 1, 1), datetime.date(j.year, 12, 31), code
    if params.get("mois") and not code:
        try:
            a, m = (int(x) for x in params["mois"].split("-"))
            return datetime.date(a, m, 1), datetime.date(a, m, calendar.monthrange(a, m)[1]), "mois_choisi"
        except (ValueError, TypeError):
            pass
    if code == "jour":
        return j, j, code
    if code == "hier":
        h = j - datetime.timedelta(days=1)
        return h, h, code
    if code == "semaine":
        lundi = j - datetime.timedelta(days=j.weekday())
        return lundi, lundi + datetime.timedelta(days=6), code
    if code == "mois_precedent":
        fin = j.replace(day=1) - datetime.timedelta(days=1)
        return fin.replace(day=1), fin, code
    if code == "trimestre":
        m = 3 * ((j.month - 1) // 3) + 1
        fin = datetime.date(j.year, m + 2, calendar.monthrange(j.year, m + 2)[1])
        return datetime.date(j.year, m, 1), fin, code
    if code == "annee":
        return datetime.date(j.year, 1, 1), datetime.date(j.year, 12, 31), code
    try:
        du = datetime.date.fromisoformat(params.get("du", ""))
        au = datetime.date.fromisoformat(params.get("au", ""))
        if du <= au:
            return du, au, ""
    except ValueError:
        pass
    return j.replace(day=1), j.replace(day=calendar.monthrange(j.year, j.month)[1]), "mois"


def periode_precedente(debut, fin):
    """Période de même longueur juste avant (mois entier → mois précédent)."""
    if debut.day == 1 and fin == fin.replace(day=calendar.monthrange(fin.year, fin.month)[1]):
        mois = (fin.year - debut.year) * 12 + fin.month - debut.month + 1
        d = debut
        for _ in range(mois):
            d = (d - datetime.timedelta(days=1)).replace(day=1)
        f = debut - datetime.timedelta(days=1)
        return d, f
    jours = (fin - debut).days + 1
    return debut - datetime.timedelta(days=jours), debut - datetime.timedelta(days=1)


# ---------------------------------------------------------------- Axes
def _transport():
    from apps.core.models import Societe

    return Societe.get().activite != Societe.ACTIVITE_COMMERCE


def _plans_sections():
    """Plans de sections libres (hors Gares, Véhicules et Agences, déjà portés par les axes du transport)."""
    from .models import SectionAnalytique

    exclus = {"Gares", "Véhicules", "Agences", "Services"} if _transport() else set()
    plans = sorted(set(SectionAnalytique.objects.values_list("plan", flat=True)) - exclus)
    return [(f"plan-{slugify(p)}", p, f"Sections du plan « {p} »") for p in plans]


def axes():
    """[(code, titre, description)] du dossier : axes du transport puis plans de sections."""
    return (AXES_TRANSPORT if _transport() else []) + _plans_sections()


def titre_axe(code):
    return dict((c, t) for c, t, _ in axes()).get(code)


# ---------------------------------------------------------------- Faits : lignes de charges et produits attribuées
class _Contexte:
    """Référentiels chargés une fois pour attribuer rapidement des milliers de lignes."""

    def __init__(self, debut, fin):
        from apps.transport.analytique import _contrats_par_vehicule, _contrat_le
        from apps.transport.etats import _depart_des_pieces
        from apps.transport.models import Depart, Gare, Vehicule

        from .models import SectionAnalytique

        # Attribution du transport dès qu'il existe des gares ou des véhicules (l'affichage, lui, suit l'activité)
        self.transport = Vehicule.objects.exists() or Gare.objects.exists()
        self.sections = {s["id"]: s for s in SectionAnalytique.objects.values("id", "plan", "code", "intitule")}
        self.slug_plan = {p: f"plan-{slugify(p)}" for p in {s["plan"] for s in self.sections.values()}}
        if not self.transport:
            return
        self._contrat_le = _contrat_le
        self.contrats = _contrats_par_vehicule(debut, fin)
        self.vehicules = {v.pk: v for v in Vehicule.objects.all()}
        self.gares = {g.pk: g for g in Gare.objects.select_related("agence")}
        self.gare_de_section = {g.section_id: g.pk for g in self.gares.values() if g.section_id}
        par_agence = {}
        for g in self.gares.values():
            if g.agence_id:
                par_agence.setdefault(g.agence.code, []).append(g.pk)
        self.gare_d_agence = {code: ids[0] for code, ids in par_agence.items() if len(ids) == 1}
        marge = datetime.timedelta(days=31)
        departs = list(Depart.objects.filter(date__range=(debut - marge, fin + marge)).select_related("ligne"))
        self.departs = {d.pk: d for d in departs}
        self.depart_de_piece = _depart_des_pieces(departs)
        self.gammes = {}
        from apps.partenaires.models import compte_remuneration
        from apps.transport.models import ParametresTransport

        self.parametres, self.remuneration = ParametresTransport.get(), compte_remuneration().numero

    def gamme(self, vehicule_id, jour):
        cle = (vehicule_id, jour)
        if cle not in self.gammes:
            self.gammes[cle] = self.vehicules[vehicule_id].gamme_le(jour)
        return self.gammes[cle]

    def service(self, numero, vehicule_id, section):
        """Section du plan Services portée par la ligne (paie hors véhicule…), sinon le service qui produit le fait :
        billetterie, colis ; carburant, route et salaires répartis sur un véhicule : conduite ; garage. Le reste
        (assurances, loyers, frais généraux sans section) reste non affecté."""
        if section and section["plan"] == "Services" and section["code"].startswith("SV-"):
            return section["code"][3:]
        if not self.transport:
            return None
        from apps.transport.analytique import _rubrique

        r = _rubrique(numero, self.parametres, self.remuneration)
        if r == "personnel" and not vehicule_id:
            return None
        return SERVICES_RUBRIQUES.get(r)

    def activite(self, numero, vehicule_id, depart_id):
        if not self.transport:
            return None
        from apps.transport.analytique import _rubrique

        r = _rubrique(numero, self.parametres, self.remuneration)
        if numero.startswith("7"):
            return {"billetterie": "voyageurs", "bagages": "bagages", "colis": "colis"}.get(r, "autres_produits")
        return "exploitation" if (vehicule_id or depart_id) else "structure"


def faits(debut, fin, ctx=None):
    """Lignes de charges et produits validées de la période, chacune avec ses éléments sur tous les axes.

    montant : produit en positif, charge en négatif (résultat = somme)."""
    from .models import Ecriture, LigneEcriture

    ctx = ctx or _Contexte(debut, fin)
    qs = (LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE, ecriture__date__range=(debut, fin))
          .filter(Q(compte__numero__startswith="6") | Q(compte__numero__startswith="7"))
          .values("id", "debit", "credit", "libelle", "vehicule_id", "section_id", "compte__numero", "compte__intitule",
                  "ecriture_id", "ecriture__date", "ecriture__numero", "ecriture__reference", "ecriture__libelle",
                  "ecriture__origine", "ecriture__journal__code", "ecriture__site_origine")
          .order_by("ecriture__date", "ecriture__numero", "id"))
    for l in qs:
        numero = l["compte__numero"]
        f = {"id": l["id"], "date": l["ecriture__date"], "piece": l["ecriture__numero"], "ecriture_id": l["ecriture_id"],
             "journal": l["ecriture__journal__code"], "libelle": l["libelle"] or l["ecriture__libelle"],
             "compte": numero, "compte_intitule": l["compte__intitule"], "produit": numero.startswith("7"),
             "montant": l["credit"] - l["debit"], "site": l["ecriture__site_origine"]}
        section = ctx.sections.get(l["section_id"])
        if section:
            f[ctx.slug_plan[section["plan"]]] = section["id"]
        if ctx.transport:
            v, jour = l["vehicule_id"], l["ecriture__date"]
            dep_id = (ctx.depart_de_piece.get(l["ecriture__reference"]) or ctx.depart_de_piece.get(l["ecriture__origine"])
                      or ctx.depart_de_piece.get(l["ecriture__numero"]))
            depart = ctx.departs.get(dep_id)
            gare = ctx.gare_de_section.get(l["section_id"])
            if gare is None and depart is not None:
                gare = depart.ligne.gare_depart_id
            if gare is None and section and section["code"].startswith("AG-"):
                gare = ctx.gare_d_agence.get(section["code"][3:])
            contrat = ctx._contrat_le(ctx.contrats, v, jour) if v else None
            f.update({
                "vehicules": v, "voyages": dep_id if depart else None, "lignes": depart.ligne_id if depart else None,
                "gammes": (depart.ligne.gamme if depart else None) or (ctx.gamme(v, jour) if v else None),
                "gares": gare, "contrats": contrat.pk if contrat else None,
                "proprietaires": (contrat.partenaire_id if contrat else "societe") if v else None,
                "activites": ctx.activite(numero, v, dep_id), "services": ctx.service(numero, v, section)})
        yield f


# ---------------------------------------------------------------- Libellés des éléments
def libelles(axe, cles):
    """{clé: libellé} des éléments d'un axe."""
    cles = [c for c in cles if c not in (None, NON_AFFECTE)]
    if axe == "gares":
        from apps.transport.models import Gare
        return {g.pk: f"{g.code} — {g.nom}" for g in Gare.objects.filter(pk__in=cles)}
    if axe == "vehicules":
        from apps.transport.models import Vehicule
        return {v.pk: f"{v.immatriculation} — {v.designation}".rstrip(" —") for v in Vehicule.objects.filter(pk__in=cles)}
    if axe == "proprietaires":
        from apps.commercial.models import Tiers
        r = {t.pk: t.nom for t in Tiers.objects.filter(pk__in=[c for c in cles if c != "societe"])}
        if "societe" in cles:
            r["societe"] = "Société (véhicules propres)"
        return r
    if axe == "gammes":
        from apps.transport.models import GAMMES
        return {c: dict(GAMMES).get(c, c) for c in cles}
    if axe == "lignes":
        from apps.transport.models import Ligne
        return {l.pk: f"{l.code} — {l.gare_depart.ville} → {l.gare_arrivee.ville}"
                for l in Ligne.objects.filter(pk__in=cles).select_related("gare_depart", "gare_arrivee")}
    if axe == "voyages":
        from apps.transport.models import Depart
        return {d.pk: f"{d.numero} · {d.date:%d/%m}{d.heure and f' {d.heure:%H:%M}' or ''} · {d.ligne.code} · "
                      f"{getattr(d.vehicule, 'immatriculation', '')}"
                for d in Depart.objects.filter(pk__in=cles).select_related("ligne", "vehicule")}
    if axe == "activites":
        return {c: ACTIVITES.get(c, c) for c in cles}
    if axe == "services":
        from apps.personnel.models import Employe
        return {c: dict(Employe.SERVICES).get(c, c) for c in cles}
    if axe == "contrats":
        from apps.partenaires.models import ContratPartenaire
        return {c.pk: f"{c.numero} v{c.version} — {c.partenaire.nom} — {c.vehicule.immatriculation}"
                for c in ContratPartenaire.objects.filter(pk__in=cles).select_related("partenaire", "vehicule")}
    if axe.startswith("plan-"):
        from .models import SectionAnalytique
        return {s.pk: f"{s.code} — {s.intitule}" for s in SectionAnalytique.objects.filter(pk__in=cles)}
    return {c: str(c) for c in cles}


def cle_depuis_url(axe, valeur):
    """Clé d'élément lue dans l'URL (identifiant numérique, code de gamme ou d'activité, « aucun »)."""
    if valeur == NON_AFFECTE:
        return None
    if axe in ("gammes", "activites", "services") or (axe == "proprietaires" and valeur == "societe"):
        return valeur
    try:
        return int(valeur)
    except (TypeError, ValueError):
        return valeur


# ---------------------------------------------------------------- États
def _somme(lignes):
    p = sum((f["montant"] for f in lignes if f["produit"]), ZERO)
    c = -sum((f["montant"] for f in lignes if not f["produit"]), ZERO)
    return {"produits": p, "charges": c, "resultat": p - c, "lignes": len(lignes)}


def ecritures_provisoires(debut, fin):
    """Écritures encore au brouillard sur la période : exclues des états (vue provisoire à part)."""
    from .models import Ecriture

    return Ecriture.objects.filter(statut=Ecriture.STATUT_BROUILLARD, date__range=(debut, fin)).count()


def synthese_axes(debut, fin):
    """Page d'entrée : pour chaque axe, nombre d'éléments mouvementés, montants affectés et non affectés."""
    liste = axes()
    gl = {"produits": ZERO, "charges": ZERO}
    par_axe = {code: {"elements": set(), "produits": ZERO, "charges": ZERO} for code, _, _ in liste}
    for f in faits(debut, fin):
        sens = "produits" if f["produit"] else "charges"
        gl[sens] += abs(f["montant"])
        for code in par_axe:
            if f.get(code) is not None:
                par_axe[code]["elements"].add(f[code])
                par_axe[code][sens] += abs(f["montant"])
    return {"gl": gl, "axes": [{"code": code, "titre": titre, "description": desc, "elements": len(par_axe[code]["elements"]),
                                "produits": par_axe[code]["produits"], "charges": par_axe[code]["charges"],
                                "produits_non_affectes": gl["produits"] - par_axe[code]["produits"],
                                "charges_non_affectees": gl["charges"] - par_axe[code]["charges"]}
                               for code, titre, desc in liste]}


def balance_axe(axe, debut, fin):
    """Tous les éléments d'un axe : produits, charges, résultat ; non affecté ; rapprochement avec la générale."""
    groupes, tout = OrderedDict(), []
    for f in faits(debut, fin):
        tout.append(f)
        groupes.setdefault(f.get(axe), []).append(f)
    noms = libelles(axe, list(groupes))
    elements = [{"cle": c, "libelle": noms.get(c, str(c)), **_somme(ls)} for c, ls in groupes.items() if c is not None]
    elements.sort(key=lambda e: e["libelle"])
    non_affecte = _somme(groupes.get(None, []))
    total_elements = {k: sum((e[k] for e in elements), ZERO) for k in ("produits", "charges", "resultat")}
    gl = _somme(tout)
    return {"elements": elements, "non_affecte": non_affecte, "total_elements": total_elements, "gl": gl,
            "rapproche": all(total_elements[k] + non_affecte[k] == gl[k] for k in ("produits", "charges", "resultat"))}


def _rubrique_generale(numero, intitules):
    """Commerce, plans de sections : regroupement par compte à 2 chiffres (60 Achats, 70 Ventes…)."""
    from .models import normaliser_numero

    prefixe = numero[:2]
    return prefixe, intitules.get(normaliser_numero(prefixe)) or intitules.get(prefixe) or f"Comptes {prefixe}"


def etat_element(axe, cle, etat, debut, fin, axe2="", comparer="precedente"):
    """État détaillé d'un élément (cle=None : le non affecté de l'axe)."""
    from .models import Compte

    ctx = _Contexte(debut, fin)
    lignes = [f for f in faits(debut, fin, ctx) if f.get(axe) == cle]
    total = _somme(lignes)
    r = {"total": total, "lignes": lignes}
    if etat == "exploitation":
        rubriques = OrderedDict()
        if ctx.transport:
            from apps.transport.analytique import CHARGES, PRODUITS, _rubrique

            noms = dict(PRODUITS + CHARGES + [("proprietaire", "Part du propriétaire (contrat)")])
            for f in lignes:
                k = _rubrique(f["compte"], ctx.parametres, ctx.remuneration)
                g = rubriques.setdefault(k, {"libelle": noms.get(k, k), "produit": f["produit"], "montant": ZERO})
                g["montant"] += f["montant"] if f["produit"] else -f["montant"]
        else:
            intitules = dict(Compte.objects.values_list("numero", "intitule"))
            for f in lignes:
                k, nom = _rubrique_generale(f["compte"], intitules)
                g = rubriques.setdefault(k, {"libelle": f"{k} {nom}", "produit": f["produit"], "montant": ZERO})
                g["montant"] += f["montant"] if f["produit"] else -f["montant"]
        r["produits"] = [g for g in rubriques.values() if g["produit"]]
        r["charges"] = [g for g in rubriques.values() if not g["produit"]]
    elif etat == "comptes":
        comptes = OrderedDict()
        for f in sorted(lignes, key=lambda f: f["compte"]):
            g = comptes.setdefault(f["compte"], {"compte": f["compte"], "intitule": f["compte_intitule"], "debit": ZERO,
                                                 "credit": ZERO, "lignes": 0})
            g["debit" if f["montant"] < 0 else "credit"] += abs(f["montant"])
            g["lignes"] += 1
        r["comptes"] = list(comptes.values())
    elif etat == "evolution":
        par_jour = (fin - debut).days <= 62
        series = OrderedDict()
        for f in lignes:
            k = f["date"] if par_jour else f["date"].replace(day=1)
            g = series.setdefault(k, {"periode": k, "produits": ZERO, "charges": ZERO})
            g["produits" if f["produit"] else "charges"] += abs(f["montant"])
        for g in series.values():
            g["resultat"] = g["produits"] - g["charges"]
        r["series"], r["par_jour"] = sorted(series.values(), key=lambda g: g["periode"]), par_jour
    elif etat == "croise":
        groupes = OrderedDict()
        for f in lignes:
            groupes.setdefault(f.get(axe2), []).append(f)
        noms = libelles(axe2, list(groupes))
        croise = [{"cle": c, "libelle": noms.get(c, str(c)) if c is not None else "Non affecté", **_somme(ls)}
                  for c, ls in groupes.items()]
        r["croise"] = sorted(croise, key=lambda g: (g["cle"] is None, g["libelle"]))
    elif etat == "journal":
        noms = {code: libelles(code, list({f.get(code) for f in lignes})) for code, _, _ in axes() if code != axe}
        r["journal_axes"] = [(code, titre) for code, titre, _ in axes() if code != axe]
        r["journal"] = [{**f, "attributions": [noms[code].get(f.get(code), "—") if f.get(code) is not None else "—"
                                               for code, _ in r["journal_axes"]]} for f in lignes[:1000]]
    elif etat == "comparaison":
        d0, f0 = annee_precedente(debut, fin) if comparer == "n1" else periode_precedente(debut, fin)
        avant = [f for f in faits(d0, f0) if f.get(axe) == cle]
        par_compte = OrderedDict()
        for quand, ls in (("actuel", lignes), ("precedent", avant)):
            for f in ls:
                g = par_compte.setdefault(f["compte"], {"compte": f["compte"], "intitule": f["compte_intitule"],
                                                        "actuel": ZERO, "precedent": ZERO})
                g[quand] += f["montant"]
        for g in par_compte.values():
            g["ecart"] = g["actuel"] - g["precedent"]
        r.update(comparaison=sorted(par_compte.values(), key=lambda g: g["compte"]), periode_precedente=(d0, f0),
                 total_precedent=_somme(avant), ecart_resultat=total["resultat"] - _somme(avant)["resultat"])
    return r
