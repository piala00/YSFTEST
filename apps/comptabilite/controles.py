"""Contrôles de clôture et anomalies : une seule liste, chaque contrôle avec son résultat, son chiffre et son lien.

Statuts : « ok » ; « a_voir » (situation à expliquer, pas forcément une erreur) ; « anomalie » (à corriger avant de
clôturer) ; « info » (renseignement) ; « erreur » (le contrôle n'a pas pu être fait : jamais masqué).
Un contrôle n'écrit rien. Les seuils et règles fiscales ne sont pas inventés : on signale, l'expert-comptable décide.
"""
from decimal import Decimal

from django.db.models import Sum
from django.urls import reverse

from .models import Ecriture, LigneEcriture

ZERO = Decimal("0")


def _validees(fin, debut=None):
    qs = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE, ecriture__date__lte=fin)
    return qs.filter(ecriture__date__gte=debut) if debut else qs


def _solde(fin, prefixe):
    a = _validees(fin).filter(compte__numero__startswith=prefixe).aggregate(d=Sum("debit"), c=Sum("credit"))
    return (a["d"] or ZERO) - (a["c"] or ZERO)


def _soldes_par(fin, prefixe, champ):
    return {r[champ]: (r["d"] or ZERO) - (r["c"] or ZERO)
            for r in _validees(fin).filter(compte__numero__startswith=prefixe).values(champ)
            .annotate(d=Sum("debit"), c=Sum("credit"))}


def _f(montant):
    return f"{montant:,.0f}".replace(",", " ")


def controle(titre, statut, valeur="", detail="", url=""):
    return {"titre": titre, "statut": statut, "valeur": valeur, "detail": detail, "url": url}


def _brouillard(debut, fin):
    n = Ecriture.objects.filter(statut=Ecriture.STATUT_BROUILLARD, date__range=(debut, fin)).count()
    return controle("Écritures au brouillard", "anomalie" if n else "ok", n,
                    "à valider ou supprimer : elles n'entrent dans aucun état" if n else "",
                    reverse("comptabilite:ecritures") + "?statut=BROUILLARD")


def _equilibre(debut, fin):
    a = _validees(fin).aggregate(d=Sum("debit"), c=Sum("credit"))
    ecart = (a["d"] or ZERO) - (a["c"] or ZERO)
    return controle("Total des débits = total des crédits", "anomalie" if ecart else "ok", _f(ecart),
                    "écart à rechercher immédiatement" if ecart else "", reverse("comptabilite:balance"))


def _caisses(debut, fin):
    negatives = {n: s for n, s in _soldes_par(fin, "57", "compte__numero").items() if s < 0}
    return controle("Caisses jamais créditrices", "anomalie" if negatives else "ok", len(negatives),
                    ", ".join(f"{n} : {_f(s)}" for n, s in sorted(negatives.items())),
                    reverse("comptabilite:balance") + "?compte_debut=57&compte_fin=57")


def _compte(titre, prefixe, consigne, statut="a_voir"):
    def verifier(debut, fin):
        s = _solde(fin, prefixe)
        return controle(titre, statut if s else "ok", _f(s), consigne if s else "",
                        reverse("comptabilite:balance") + f"?compte_debut={prefixe}&compte_fin={prefixe}")
    return verifier


def _tiers(titre, prefixe, sens, consigne):
    def verifier(debut, fin):
        soldes = _soldes_par(fin, prefixe, "tiers_id")
        n = sum(1 for t, s in soldes.items() if t and (s < 0 if sens == "crediteur" else s > 0))
        return controle(titre, "a_voir" if n else "ok", n, consigne if n else "",
                        reverse("comptabilite:balance") + f"?compte_debut={prefixe}&compte_fin={prefixe}")
    return verifier


def _liaisons_siege(debut, fin):
    from apps.echanges.publication import site_local

    local = site_local()
    if local is None or local.role != local.SIEGE:
        return controle("Comptes de liaison entre agences (185) soldés au siège", "info", "—",
                        "sans objet : ce dossier n'est pas le siège")
    s = _solde(fin, "185")
    return controle("Comptes de liaison entre agences (185) soldés au siège", "anomalie" if s else "ok", _f(s),
                    "un fichier d'agence manque peut-être, ou une opération n'a qu'un côté" if s else "",
                    reverse("comptabilite:balance") + "?compte_debut=185&compte_fin=185")


def _liaison_commerciale(debut, fin):
    from .services import controle_liaison

    n = len(controle_liaison(debut, fin)["anomalies"])
    return controle("Factures et règlements bien comptabilisés", "anomalie" if n else "ok", n,
                    "pièce sans écriture, écriture non validée ou montant différent" if n else "",
                    reverse("comptabilite:controle_liaison"))


def _corrections(debut, fin):
    from apps.echanges.corrections import ouvertes

    demandes = list(ouvertes())
    retard = sum(1 for d in demandes if d.en_retard)
    statut = "anomalie" if retard else ("a_voir" if demandes else "ok")
    return controle("Demandes de correction direction / agences ouvertes", statut, len(demandes),
                    f"dont {retard} en retard" if retard else "", reverse("comptabilite:corrections"))


def _sessions_caisse(debut, fin):
    from apps.transport.models_caisse import SessionCaisse

    n = SessionCaisse.objects.filter(statut__in=(SessionCaisse.OUVERTE, SessionCaisse.FERMEE), ouverte_le__date__lte=fin).count()
    return controle("Sessions de caisse fermées et approuvées", "a_voir" if n else "ok", n,
                    "sessions encore ouvertes ou non approuvées" if n else "", reverse("transport:sessions_caisse"))


def _analytique(debut, fin):
    from . import plan_analytique as pa

    if not pa._transport():
        return controle("Charges affectées aux véhicules", "info", "—", "sans objet : dossier sans véhicules")
    b = pa.balance_axe("vehicules", debut, fin)
    part = round(100 * b["non_affecte"]["charges"] / b["gl"]["charges"]) if b["gl"]["charges"] else 0
    return controle("Charges affectées aux véhicules", "info", f"{100 - part} %",
                    f"non affecté (charges du siège, structure…) : {_f(b['non_affecte']['charges'])}",
                    reverse("analytique:axe", args=["vehicules"]) + f"?du={debut:%Y-%m-%d}&au={fin:%Y-%m-%d}")


CONTROLES = [
    ("Écritures", [_brouillard, _equilibre]),
    ("Trésorerie", [_caisses, _compte("Virements internes et fonds en transit (58) soldés", "58",
                                      "versements partis mais pas encore arrivés, ou mouvement à un seul côté")]),
    ("Tiers", [_tiers("Clients créditeurs", "411", "crediteur", "avances, avoirs ou règlements en trop à justifier"),
               _tiers("Fournisseurs débiteurs", "401", "debiteur", "acomptes ou avoirs à recevoir à justifier"),
               _compte("Compte d'attente (471) soldé", "471", "opérations à reclasser avant la clôture", "anomalie"),
               _compte("Salaires nets à payer (422)", "422", "salaires restant à verser", "info")]),
    ("Liaisons", [_liaison_commerciale, _liaisons_siege, _corrections]),
    ("Exploitation", [_sessions_caisse, _analytique]),
]


def executer(debut, fin):
    groupes = []
    for groupe, verifs in CONTROLES:
        lignes = []
        for v in verifs:
            try:
                lignes.append(v(debut, fin))
            except Exception as exc:                                   # un contrôle impossible n'est jamais masqué
                lignes.append(controle(getattr(v, "__name__", "Contrôle").strip("_").replace("_", " ").capitalize(),
                                       "erreur", "", f"contrôle impossible : {exc}"[:200]))
        groupes.append({"groupe": groupe, "lignes": lignes})
    toutes = [l for g in groupes for l in g["lignes"]]
    return {"groupes": groupes, "anomalies": sum(1 for l in toutes if l["statut"] in ("anomalie", "erreur")),
            "a_voir": sum(1 for l in toutes if l["statut"] == "a_voir"), "ok": sum(1 for l in toutes if l["statut"] == "ok")}
