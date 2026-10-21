"""Génération automatique des écritures et calculs comptables (SYSCOHADA)."""
from collections import OrderedDict, defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum

from apps.core.models import Exercice, Sequence

from .models import Compte, Ecriture, Journal, LigneEcriture

ZERO = Decimal("0")

COMPTE_TVA_COLLECTEE = "4431"
COMPTE_TVA_DEDUCTIBLE = "4452"


def _journal(code):
    try:
        return Journal.objects.get(code=code)
    except Journal.DoesNotExist:
        raise ValidationError(f"Le journal {code} n'existe pas. Lancez « python manage.py init_erp ».")


@transaction.atomic
def creer_ecriture(journal, date, libelle, lignes, reference="", origine="", valider=True):
    """Crée une pièce comptable.

    `lignes` : liste de dicts {compte, debit, credit, libelle?, tiers?}.
    Les lignes de même compte / tiers / sens sont regroupées.
    """
    exercice = Exercice.pour_date(date)
    regroupees = OrderedDict()
    for ligne in lignes:
        debit = Decimal(ligne.get("debit") or 0)
        credit = Decimal(ligne.get("credit") or 0)
        if debit < 0:
            debit, credit = ZERO, credit - debit
        if credit < 0:
            debit, credit = debit - credit, ZERO
        if not debit and not credit:
            continue
        cle = (ligne["compte"].pk, getattr(ligne.get("tiers"), "pk", None), "D" if debit else "C")
        if cle in regroupees:
            regroupees[cle]["debit"] += debit
            regroupees[cle]["credit"] += credit
        else:
            regroupees[cle] = {**ligne, "debit": debit, "credit": credit}

    total_d = sum(l["debit"] for l in regroupees.values())
    total_c = sum(l["credit"] for l in regroupees.values())
    if total_d != total_c:
        raise ValidationError(f"Écriture déséquilibrée : débit {total_d} ≠ crédit {total_c}.")

    ecriture = Ecriture.objects.create(
        journal=journal, exercice=exercice, date=date, libelle=libelle[:200], reference=reference,
        origine=origine, numero=Sequence.suivant(journal.code, date.year, largeur=6),
    )
    LigneEcriture.objects.bulk_create([
        LigneEcriture(
            ecriture=ecriture, compte=l["compte"], tiers=l.get("tiers"),
            libelle=(l.get("libelle") or libelle)[:200], debit=l["debit"], credit=l["credit"],
        )
        for l in regroupees.values()
    ])
    if valider:
        ecriture.valider()
    return ecriture


def comptabiliser_document(document):
    """Facture / avoir client ou fournisseur → journal des ventes ou des achats.

    Facture client      : D 411 (TTC)  / C 70x (HT) / C 4431 (TVA)
    Facture fournisseur : D 60x (HT) / D 4452 (TVA) / C 401 (TTC)
    Les avoirs sont passés en sens inverse.
    """
    if document.ecriture_id:
        return document.ecriture
    tiers = document.tiers
    compte_tiers = tiers.get_compte_collectif()
    sens = -1 if document.est_avoir else 1
    libelle = f"{document.get_type_document_display()} {document.numero} - {tiers.nom}"

    lignes = []
    if document.est_vente:
        journal = _journal("VT")
        tva = Compte.par_numero(COMPTE_TVA_COLLECTEE)
        lignes.append({"compte": compte_tiers, "tiers": tiers, "debit": sens * document.total_ttc})
        for ligne in document.lignes.select_related("article"):
            compte = ligne.article.get_compte_vente() if ligne.article else Compte.par_numero("706")
            lignes.append({"compte": compte, "credit": sens * ligne.montant_ht})
            lignes.append({"compte": tva, "credit": sens * ligne.montant_tva})
    else:
        journal = _journal("AC")
        tva = Compte.par_numero(COMPTE_TVA_DEDUCTIBLE)
        for ligne in document.lignes.select_related("article"):
            compte = ligne.article.get_compte_achat() if ligne.article else Compte.par_numero("605")
            lignes.append({"compte": compte, "debit": sens * ligne.montant_ht})
            lignes.append({"compte": tva, "debit": sens * ligne.montant_tva})
        lignes.append({"compte": compte_tiers, "tiers": tiers, "credit": sens * document.total_ttc})

    ecriture = creer_ecriture(
        journal, document.date, libelle, lignes,
        reference=document.reference_externe or document.numero, origine=document.numero,
    )
    document.ecriture = ecriture
    document.save(update_fields=["ecriture"])
    return ecriture


def comptabiliser_reglement(reglement):
    """Encaissement client : D 52/57 / C 411 — Décaissement fournisseur : D 401 / C 52/57."""
    if reglement.ecriture_id:
        return reglement.ecriture
    journal = reglement.journal
    if not journal.compte_tresorerie_id:
        raise ValidationError(f"Le journal {journal.code} n'a pas de compte de trésorerie associé.")
    tiers = reglement.tiers
    compte_tiers = tiers.get_compte_collectif()
    libelle = reglement.libelle or f"Règlement {reglement.numero} - {tiers.nom}"
    if reglement.est_encaissement:
        lignes = [
            {"compte": journal.compte_tresorerie, "debit": reglement.montant},
            {"compte": compte_tiers, "tiers": tiers, "credit": reglement.montant},
        ]
    else:
        lignes = [
            {"compte": compte_tiers, "tiers": tiers, "debit": reglement.montant},
            {"compte": journal.compte_tresorerie, "credit": reglement.montant},
        ]
    ecriture = creer_ecriture(journal, reglement.date, libelle, lignes,
                              reference=reglement.reference or reglement.numero, origine=reglement.numero)
    reglement.ecriture = ecriture
    reglement.save(update_fields=["ecriture"])
    return ecriture


# ---------------------------------------------------------------------------
# Consultations
# ---------------------------------------------------------------------------

def lignes_validees(date_debut=None, date_fin=None, exercice=None):
    qs = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE)
    if exercice is not None:
        qs = qs.filter(ecriture__exercice=exercice)
    if date_fin:
        qs = qs.filter(ecriture__date__lte=date_fin)
    if date_debut:
        qs = qs.filter(ecriture__date__gte=date_debut)
    return qs


def balance(date_debut, date_fin, compte_debut="", compte_fin="", exercice=None):
    """Balance générale à 6 colonnes : à-nouveaux / mouvements de la période / soldes."""
    base = lignes_validees(date_fin=date_fin, exercice=exercice)
    if compte_debut:
        base = base.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        base = base.filter(compte__numero__lte=compte_fin + "￿")

    anterieur = base.filter(ecriture__date__lt=date_debut).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))
    periode = base.filter(ecriture__date__gte=date_debut).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))

    donnees = defaultdict(lambda: {"an_d": ZERO, "an_c": ZERO, "mvt_d": ZERO, "mvt_c": ZERO})
    for row in anterieur:
        solde = (row["d"] or ZERO) - (row["c"] or ZERO)
        donnees[row["compte"]]["an_d" if solde > 0 else "an_c"] += abs(solde)
    for row in periode:
        donnees[row["compte"]]["mvt_d"] += row["d"] or ZERO
        donnees[row["compte"]]["mvt_c"] += row["c"] or ZERO

    comptes = {c.pk: c for c in Compte.objects.filter(pk__in=donnees.keys())}
    lignes = []
    totaux = {k: ZERO for k in ("an_d", "an_c", "mvt_d", "mvt_c", "solde_d", "solde_c")}
    for pk, d in donnees.items():
        solde = d["an_d"] - d["an_c"] + d["mvt_d"] - d["mvt_c"]
        d["solde_d"] = solde if solde > 0 else ZERO
        d["solde_c"] = -solde if solde < 0 else ZERO
        d["compte"] = comptes[pk]
        lignes.append(d)
        for k in totaux:
            totaux[k] += d[k]
    lignes.sort(key=lambda l: l["compte"].numero)
    return lignes, totaux


def grand_livre(date_debut, date_fin, compte_debut="", compte_fin="", tiers=None):
    """Grand livre : pour chaque compte, report à nouveau puis détail des lignes avec solde progressif."""
    qs = lignes_validees(date_fin=date_fin).select_related("compte", "ecriture__journal", "tiers")
    if compte_debut:
        qs = qs.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        qs = qs.filter(compte__numero__lte=compte_fin + "￿")
    if tiers is not None:
        qs = qs.filter(tiers=tiers)

    reports = {
        r["compte"]: (r["d"] or ZERO) - (r["c"] or ZERO)
        for r in qs.filter(ecriture__date__lt=date_debut).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))
    }
    resultat = OrderedDict()
    for ligne in qs.filter(ecriture__date__gte=date_debut).order_by("compte__numero", "ecriture__date", "ecriture__numero", "id"):
        bloc = resultat.get(ligne.compte_id)
        if bloc is None:
            report = reports.pop(ligne.compte_id, ZERO)
            bloc = resultat[ligne.compte_id] = {
                "compte": ligne.compte, "report": report, "lignes": [],
                "total_debit": ZERO, "total_credit": ZERO, "solde": report,
            }
        bloc["solde"] += ligne.debit - ligne.credit
        bloc["total_debit"] += ligne.debit
        bloc["total_credit"] += ligne.credit
        bloc["lignes"].append({"ligne": ligne, "solde": bloc["solde"]})
    # Comptes sans mouvement sur la période mais avec un report
    for pk, report in reports.items():
        if report:
            resultat[pk] = {"compte": Compte.objects.get(pk=pk), "report": report, "lignes": [],
                            "total_debit": ZERO, "total_credit": ZERO, "solde": report}
    return sorted(resultat.values(), key=lambda b: b["compte"].numero)


def soldes_par_compte(date_fin, date_debut=None, exercice=None):
    """{numero_compte: solde débiteur (>0) ou créditeur (<0)}."""
    qs = lignes_validees(date_debut=date_debut, date_fin=date_fin, exercice=exercice)
    return {
        r["compte__numero"]: (r["d"] or ZERO) - (r["c"] or ZERO)
        for r in qs.values("compte__numero").annotate(d=Sum("debit"), c=Sum("credit"))
    }


@transaction.atomic
def lettrer(lignes):
    """Lettre un ensemble de lignes d'un même compte si elles sont équilibrées."""
    lignes = list(lignes)
    if len({l.compte_id for l in lignes}) != 1:
        raise ValidationError("Le lettrage porte sur un seul compte.")
    if sum(l.debit for l in lignes) != sum(l.credit for l in lignes):
        raise ValidationError("Les lignes sélectionnées ne sont pas équilibrées.")
    compte = lignes[0].compte
    existants = LigneEcriture.objects.filter(compte=compte).exclude(lettrage="").values_list("lettrage", flat=True)
    code = _prochain_code_lettrage(set(existants))
    LigneEcriture.objects.filter(pk__in=[l.pk for l in lignes]).update(lettrage=code)
    return code


def _prochain_code_lettrage(existants):
    import itertools
    import string

    for longueur in range(1, 5):
        for combo in itertools.product(string.ascii_uppercase, repeat=longueur):
            code = "".join(combo)
            if code not in existants:
                return code
    raise ValidationError("Plus de code de lettrage disponible.")


def lignes_non_lettrees(compte, tiers=None):
    qs = LigneEcriture.objects.filter(compte=compte, lettrage="", ecriture__statut=Ecriture.STATUT_VALIDEE)
    if tiers:
        qs = qs.filter(tiers=tiers)
    return qs.select_related("ecriture", "tiers").order_by("ecriture__date")


def declaration_tva(date_debut, date_fin):
    """TVA collectée (443) - TVA déductible (445) sur la période."""
    qs = lignes_validees(date_debut=date_debut, date_fin=date_fin)
    collectee = qs.filter(compte__numero__startswith="443").aggregate(d=Sum("debit"), c=Sum("credit"))
    deductible = qs.filter(compte__numero__startswith="445").aggregate(d=Sum("debit"), c=Sum("credit"))
    tva_collectee = (collectee["c"] or ZERO) - (collectee["d"] or ZERO)
    tva_deductible = (deductible["d"] or ZERO) - (deductible["c"] or ZERO)
    return {
        "collectee": tva_collectee,
        "deductible": tva_deductible,
        "solde": tva_collectee - tva_deductible,
    }


def constater_variation_stock(date):
    """Inventaire permanent → comptabilité : ajuste le compte 311 à la valeur du stock de marchandises.

    Stock en hausse : D 311 / C 6031 — stock en baisse : D 6031 / C 311.
    """
    from apps.commercial.models import Article

    articles = Article.objects.filter(suivi_stock=True, nature=Article.MARCHANDISE)
    valeur = sum((max(a.valeur_stock, ZERO) for a in articles), ZERO).quantize(Decimal("1"))
    solde_actuel = sum((s for n, s in soldes_par_compte(date).items() if n.startswith("31")), ZERO)
    ecart = valeur - solde_actuel
    if not ecart:
        raise ValidationError("Le compte de stock est déjà à jour : aucune variation à constater.")
    stock, variation = Compte.par_numero("311"), Compte.par_numero("6031")
    lignes = ([{"compte": stock, "debit": ecart}, {"compte": variation, "credit": ecart}] if ecart > 0 else
              [{"compte": variation, "debit": -ecart}, {"compte": stock, "credit": -ecart}])
    return creer_ecriture(_journal("OD"), date, f"Variation des stocks de marchandises au {date:%d/%m/%Y}", lignes,
                          reference="INVENTAIRE")
