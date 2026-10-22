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
    journal.verifier_periode(date)
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
        cle = (ligne["compte"].pk, getattr(ligne.get("tiers"), "pk", None), getattr(ligne.get("section"), "pk", None),
               "D" if debit else "C")
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
            ecriture=ecriture, compte=l["compte"], tiers=l.get("tiers"), section=l.get("section"),
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
                          société non assujettie : D 60x (TTC) / C 401 (TTC)
    Les avoirs sont passés en sens inverse.
    """
    if document.ecriture_id:
        return document.ecriture
    tiers = document.tiers_payeur          # la créance / la dette va au tiers payeur
    compte_tiers = tiers.get_compte_collectif()
    sens = -1 if document.est_avoir else 1
    libelle = f"{document.get_type_document_display()} {document.numero} - {document.tiers.nom}"

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
        from apps.core.models import Societe

        journal = _journal("AC")
        tva = Compte.par_numero(COMPTE_TVA_DEDUCTIBLE)
        recuperable = Societe.get().assujettie_tva
        for ligne in document.lignes.select_related("article"):
            compte = ligne.article.get_compte_achat() if ligne.article else Compte.par_numero("605")
            if recuperable:
                lignes.append({"compte": compte, "debit": sens * ligne.montant_ht})
                lignes.append({"compte": tva, "debit": sens * ligne.montant_tva})
            else:   # TVA non récupérable : elle fait partie de la charge
                lignes.append({"compte": compte, "debit": sens * (ligne.montant_ht + ligne.montant_tva)})
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
    """Lignes validées de la période.

    Les écritures d'un exercice clôturé sont remplacées par les à-nouveaux de l'exercice suivant :
    elles sont écartées dès que la période interrogée va au-delà de la fin de cet exercice.
    """
    qs = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE)
    clotures = Q(ecriture__exercice__cloture=True)
    if date_fin:
        clotures &= Q(ecriture__exercice__date_fin__lt=date_fin)
    if exercice is None:
        qs = qs.exclude(clotures)
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

    an = Q(ecriture__date__lt=date_debut) | Q(ecriture__journal__type_journal=Journal.TYPE_AN)
    anterieur = base.filter(an).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))
    periode = base.exclude(an).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))

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

    an = Q(ecriture__date__lt=date_debut) | Q(ecriture__journal__type_journal=Journal.TYPE_AN)
    reports = {
        r["compte"]: (r["d"] or ZERO) - (r["c"] or ZERO)
        for r in qs.filter(an).values("compte").annotate(d=Sum("debit"), c=Sum("credit"))
    }
    resultat = OrderedDict()
    for ligne in qs.exclude(an).order_by("compte__numero", "ecriture__date", "ecriture__numero", "id"):
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


@transaction.atomic
def delettrer(compte, code):
    """Supprime un code de lettrage sur un compte ; renvoie le nombre de lignes délettrées."""
    return LigneEcriture.objects.filter(compte=compte, lettrage=code).update(lettrage="")


@transaction.atomic
def lettrage_automatique(comptes=None, tiers=None):
    """Traitement > Lettrage automatique, par compte et par tiers.

    1. Montants identiques : une ligne au débit et une ligne au crédit de même montant (ordre chronologique).
    2. Solde nul : si le reste des lignes non lettrées du tiers est équilibré, il est lettré d'un seul code.
    Renvoie le nombre de codes de lettrage attribués.
    """
    qs = LigneEcriture.objects.filter(lettrage="", ecriture__statut=Ecriture.STATUT_VALIDEE, compte__lettrable=True)
    if comptes is not None:
        qs = qs.filter(compte__in=comptes)
    if tiers is not None:
        qs = qs.filter(tiers=tiers)
    groupes = defaultdict(list)
    for ligne in qs.select_related("compte").order_by("ecriture__date", "id"):
        groupes[(ligne.compte_id, ligne.tiers_id)].append(ligne)
    codes = 0
    for lignes in groupes.values():
        restantes = list(lignes)
        for debit in [l for l in lignes if l.debit]:
            credit = next((l for l in restantes if l.credit == debit.debit), None)
            if credit is not None and debit in restantes:
                lettrer([debit, credit])
                restantes.remove(debit)
                restantes.remove(credit)
                codes += 1
        if len(restantes) > 1 and sum(l.debit for l in restantes) == sum(l.credit for l in restantes):
            lettrer(restantes)
            codes += 1
    return codes


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
    solde = tva_collectee - tva_deductible
    principal = (solde / Decimal("1.1")).quantize(Decimal("1")) if solde > 0 else ZERO
    return {
        "collectee": tva_collectee,
        "deductible": tva_deductible,
        "solde": solde,
        # TVA camerounaise = principal + CAC (10 % du principal) : répartition indicative du montant dû
        "principal": principal,
        "cac": solde - principal if solde > 0 else ZERO,
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


# ---------------------------------------------------------------------------
# Rapprochement bancaire
# ---------------------------------------------------------------------------
def rapprochement(compte, date_releve):
    """Situation de rapprochement d'un compte de banque à la date d'un relevé."""
    lignes = lignes_validees(date_fin=date_releve).filter(compte=compte).select_related("ecriture__journal", "tiers")
    totaux = lignes.aggregate(d=Sum("debit"), c=Sum("credit"))
    solde_comptable = (totaux["d"] or ZERO) - (totaux["c"] or ZERO)
    non_pointees = lignes.filter(Q(date_pointage__isnull=True) | Q(date_pointage__gt=date_releve))
    np = non_pointees.aggregate(d=Sum("debit"), c=Sum("credit"))
    return {
        "solde_comptable": solde_comptable,
        "non_pointees": non_pointees.order_by("ecriture__date", "id"),
        "non_pointe_debit": np["d"] or ZERO,
        "non_pointe_credit": np["c"] or ZERO,
        # Ce que la banque doit afficher : solde comptable moins les opérations qu'elle n'a pas encore passées
        "solde_banque_theorique": solde_comptable - (np["d"] or ZERO) + (np["c"] or ZERO),
    }


@transaction.atomic
def pointer(lignes, date_releve):
    return LigneEcriture.objects.filter(pk__in=[l.pk for l in lignes]).update(date_pointage=date_releve)


# ---------------------------------------------------------------------------
# Fin d'exercice
# ---------------------------------------------------------------------------
def exercice_suivant(exercice, creer=True):
    import datetime

    suivant = Exercice.objects.filter(date_debut=exercice.date_fin + datetime.timedelta(days=1)).first()
    if suivant is None and creer:
        debut = exercice.date_fin + datetime.timedelta(days=1)
        try:
            fin = debut.replace(year=debut.year + 1) - datetime.timedelta(days=1)
        except ValueError:          # 29 février
            fin = debut.replace(year=debut.year + 1, day=28) - datetime.timedelta(days=1)
        code = str(debut.year) if debut.month == 1 else f"{debut.year}-{fin.year}"
        suivant = Exercice.objects.create(code=code, date_debut=debut, date_fin=fin)
    return suivant


def controle_liaison(date_debut, date_fin):
    """Rapprochement Gestion commerciale → Comptabilité (proposition du dossier « liaisons comptabilité ») :
    chaque facture, avoir et règlement validé doit avoir son écriture validée, au bon montant sur le compte du
    tiers ; chaque écriture des journaux VT / AC qui cite une pièce commerciale doit la retrouver.
    Une balance équilibrée ne garantit pas l'absence de facture oubliée ou passée deux fois."""
    from apps.commercial.models import Document, Reglement

    anomalies, flux = [], []

    def montant_tiers(ecriture, tiers):
        agg = ecriture.lignes.filter(tiers=tiers).aggregate(d=Sum("debit"), c=Sum("credit"))
        return abs((agg["d"] or ZERO) - (agg["c"] or ZERO))

    def verifier(piece, montant, libelle):
        from django.urls import reverse

        vue = "commercial:reglement_detail" if isinstance(piece, Reglement) else "commercial:document_detail"
        anomalies_avant = len(anomalies)
        ecriture = piece.ecriture
        if ecriture is None:
            anomalies.append({"url": reverse(vue, args=[piece.pk]), "libelle": libelle, "probleme": "Aucune écriture comptable"})
            return False
        if ecriture.statut != Ecriture.STATUT_VALIDEE:
            anomalies.append({"url": reverse(vue, args=[piece.pk]), "libelle": libelle, "probleme": f"Écriture {ecriture.numero} non validée"})
        ecart = montant - montant_tiers(ecriture, getattr(piece, "tiers_payeur", piece.tiers))
        if ecart:
            anomalies.append({"url": reverse(vue, args=[piece.pk]), "libelle": libelle,
                              "probleme": f"Montant du tiers en comptabilité différent ({ecart:+,.0f})".replace(",", " ")})
        return len(anomalies) == anomalies_avant

    documents = (Document.objects.filter(type_document__in=Document.TYPES_FACTURATION, date__range=(date_debut, date_fin))
                 .exclude(statut__in=(Document.BROUILLON, Document.ANNULE)).select_related("tiers", "ecriture"))
    for domaine, est_vente in (("Ventes", True), ("Achats", False)):
        docs = [d for d in documents if d.est_vente == est_vente]
        passes = [d for d in docs if verifier(d, d.total_ttc, f"{d.get_type_document_display()} {d.numero} - {d.tiers.nom}")]
        ht = sum((d.total_ht for d in docs), ZERO)
        ttc = sum((d.total_ttc for d in docs), ZERO)
        flux.append({"flux": domaine, "nombre": len(docs), "conformes": len(passes), "ht": ht,
                     "tva": sum((d.total_tva for d in docs), ZERO), "ttc": ttc})
    reglements = Reglement.objects.filter(date__range=(date_debut, date_fin)).select_related("tiers", "ecriture")
    passes = [r for r in reglements if verifier(r, r.montant, f"Règlement {r.numero} - {r.tiers.nom}")]
    total = sum((r.montant for r in reglements), ZERO)
    flux.append({"flux": "Règlements", "nombre": len(reglements), "conformes": len(passes), "ht": None, "tva": None, "ttc": total})

    # Écritures orphelines : pièce commerciale citée mais introuvable (ou rattachée à une autre écriture)
    rattachees = set(Document.objects.exclude(ecriture=None).values_list("ecriture_id", flat=True)) | \
        set(Reglement.objects.exclude(ecriture=None).values_list("ecriture_id", flat=True))
    for ecriture in (Ecriture.objects.filter(date__range=(date_debut, date_fin), journal__code__in=("VT", "AC"))
                     .exclude(origine="").exclude(pk__in=rattachees)):
        anomalies.append({"url": "", "libelle": f"Écriture {ecriture.journal.code} {ecriture.numero} ({ecriture.origine})",
                          "probleme": "Pièce commerciale introuvable : écriture passée en double ou pièce supprimée"})
    return {"flux": flux, "anomalies": anomalies}


def controles_cloture(exercice):
    """Préconditions de la clôture (liste de messages bloquants)."""
    erreurs = []
    brouillard = Ecriture.objects.filter(exercice=exercice, statut=Ecriture.STATUT_BROUILLARD).count()
    if brouillard:
        erreurs.append(f"{brouillard} écriture(s) au brouillard dans l'exercice : validez-les ou supprimez-les.")
    precedent = Exercice.objects.filter(date_fin__lt=exercice.date_debut, cloture=False).first()
    if precedent:
        erreurs.append(f"L'exercice précédent {precedent.code} doit être clôturé d'abord.")
    if exercice.cloture:
        erreurs.append(f"L'exercice {exercice.code} est déjà clôturé.")
    anomalies = controle_liaison(exercice.date_debut, exercice.date_fin)["anomalies"]
    if anomalies:
        erreurs.append(f"{len(anomalies)} anomalie(s) entre la Gestion commerciale et la Comptabilité : "
                       "voir Etat › Analyse et contrôles › Contrôle de la liaison commerciale.")
    return erreurs


@transaction.atomic
def cloturer_exercice(exercice):
    """Traitement > Fin d'exercice > Clôture de l'exercice.

    Génère dans le journal des à-nouveaux de l'exercice suivant les soldes des comptes de bilan
    (classes 1 à 5, détaillés par tiers), affecte le résultat (classes 6 à 8) en 131 bénéfice
    ou 139 perte, puis clôture l'exercice : ses écritures ne sont plus modifiables.
    """
    erreurs = controles_cloture(exercice)
    if erreurs:
        raise ValidationError(erreurs)
    suivant = exercice_suivant(exercice)
    lignes_ex = LigneEcriture.objects.filter(ecriture__exercice=exercice, ecriture__statut=Ecriture.STATUT_VALIDEE)
    soldes = lignes_ex.values("compte", "compte__numero", "tiers").annotate(d=Sum("debit"), c=Sum("credit"))
    comptes = {c.pk: c for c in Compte.objects.filter(pk__in={s["compte"] for s in soldes})}
    from apps.commercial.models import Tiers
    tiers = {t.pk: t for t in Tiers.objects.filter(pk__in={s["tiers"] for s in soldes if s["tiers"]})}

    lignes, resultat = [], ZERO
    for s in soldes:
        solde = (s["d"] or ZERO) - (s["c"] or ZERO)
        if not solde:
            continue
        if s["compte__numero"][0] in "678":
            resultat -= solde
            continue
        lignes.append({"compte": comptes[s["compte"]], "tiers": tiers.get(s["tiers"]),
                       "debit": solde if solde > 0 else ZERO, "credit": -solde if solde < 0 else ZERO,
                       "libelle": f"À-nouveau {exercice.code}"})
    if resultat > 0:
        lignes.append({"compte": Compte.par_numero("131"), "credit": resultat, "libelle": f"Résultat {exercice.code} : bénéfice"})
    elif resultat < 0:
        lignes.append({"compte": Compte.par_numero("139"), "debit": -resultat, "libelle": f"Résultat {exercice.code} : perte"})
    ecriture = None
    if lignes:
        journal = Journal.objects.filter(type_journal=Journal.TYPE_AN).first() or _journal("AN")
        ecriture = creer_ecriture(journal, suivant.date_debut, f"Reports à nouveau de l'exercice {exercice.code}",
                                  lignes, reference=f"AN {exercice.code}", origine=f"Clôture {exercice.code}")
    exercice.cloture = True
    exercice.save(update_fields=["cloture"])
    return {"exercice_suivant": suivant, "ecriture": ecriture, "resultat": resultat}


# ---------------------------------------------------------------------------
# Analytique
# ---------------------------------------------------------------------------
def balance_analytique(date_debut, date_fin):
    """Charges (classe 6), produits (classe 7) et résultat par section analytique."""
    from .models import SectionAnalytique

    qs = lignes_validees(date_debut, date_fin).filter(Q(compte__numero__startswith="6") | Q(compte__numero__startswith="7"))
    donnees = defaultdict(lambda: {"charges": ZERO, "produits": ZERO})
    for r in qs.values("section", "compte__numero").annotate(d=Sum("debit"), c=Sum("credit")):
        solde = (r["d"] or ZERO) - (r["c"] or ZERO)
        if r["compte__numero"].startswith("6"):
            donnees[r["section"]]["charges"] += solde
        else:
            donnees[r["section"]]["produits"] -= solde
    sections = {s.pk: s for s in SectionAnalytique.objects.filter(pk__in=[k for k in donnees if k])}
    lignes = []
    for pk, d in donnees.items():
        lignes.append({"section": sections.get(pk), **d, "resultat": d["produits"] - d["charges"]})
    lignes.sort(key=lambda l: (l["section"] is None, l["section"].code if l["section"] else ""))
    return lignes


# ---------------------------------------------------------------------------
# Etats tiers
# ---------------------------------------------------------------------------
def justificatif_solde(date, type_tiers=None, tiers=None):
    """Etat › Etats tiers › Justificatif de solde à date.

    Pour chaque tiers, les écritures qui composent son solde à la date : un groupe lettré n'est écarté que si
    toutes ses lignes sont antérieures ou égales à la date (sinon il n'était pas encore soldé à cette date).
    """
    qs = lignes_validees(date_fin=date).filter(tiers__isnull=False).select_related("ecriture__journal", "tiers", "compte")
    if type_tiers:
        qs = qs.filter(tiers__type_tiers=type_tiers)
    if tiers is not None:
        qs = qs.filter(tiers=tiers)
    lettres_ouverts = set(
        LigneEcriture.objects.filter(ecriture__date__gt=date).exclude(lettrage="").values_list("compte_id", "lettrage"))
    blocs = OrderedDict()
    for ligne in qs.order_by("tiers__nom", "compte__numero", "ecriture__date", "id"):
        if ligne.lettrage and (ligne.compte_id, ligne.lettrage) not in lettres_ouverts:
            continue
        bloc = blocs.setdefault((ligne.tiers_id, ligne.compte_id), {
            "tiers": ligne.tiers, "compte": ligne.compte, "lignes": [], "debit": ZERO, "credit": ZERO})
        bloc["lignes"].append(ligne)
        bloc["debit"] += ligne.debit
        bloc["credit"] += ligne.credit
    resultat = []
    for bloc in blocs.values():
        bloc["solde"] = bloc["debit"] - bloc["credit"]
        if bloc["solde"]:
            resultat.append(bloc)
    return resultat


def statistiques_tiers(date_debut, date_fin, type_tiers):
    """Etat › Etats tiers › Statistiques tiers : mouvements, solde et délai de règlement de chaque tiers."""
    from apps.commercial.models import Tiers

    qs = lignes_validees(date_fin=date_fin).filter(tiers__type_tiers=type_tiers)
    client = type_tiers == Tiers.CLIENT
    resultats = []
    for tiers in Tiers.objects.filter(pk__in=qs.values("tiers")).order_by("nom"):
        lignes = qs.filter(tiers=tiers)
        avant = lignes.filter(ecriture__date__lt=date_debut).aggregate(d=Sum("debit"), c=Sum("credit"))
        periode = lignes.filter(ecriture__date__gte=date_debut)
        mvt = periode.aggregate(d=Sum("debit"), c=Sum("credit"))
        factures = periode.filter(**({"debit__gt": 0} if client else {"credit__gt": 0}))
        reglements = periode.filter(**({"credit__gt": 0} if client else {"debit__gt": 0}))
        report = (avant["d"] or ZERO) - (avant["c"] or ZERO)
        facture = (mvt["d"] if client else mvt["c"]) or ZERO
        regle = (mvt["c"] if client else mvt["d"]) or ZERO
        solde = report + (mvt["d"] or ZERO) - (mvt["c"] or ZERO)
        resultats.append({
            "tiers": tiers, "report": report, "facture": facture, "regle": regle, "solde": solde,
            "nb_factures": factures.count(), "nb_reglements": reglements.count(),
            "derniere_facture": factures.order_by("-ecriture__date").values_list("ecriture__date", flat=True).first(),
            "dernier_reglement": reglements.order_by("-ecriture__date").values_list("ecriture__date", flat=True).first(),
            "taux_recouvrement": (regle / facture * 100) if facture else None,
        })
    return sorted(resultats, key=lambda r: -abs(r["solde"]))


# ---------------------------------------------------------------------------
# Configuration de la TVA à la création de la société
# ---------------------------------------------------------------------------
def configurer_tva_automatique():
    """Crée les taux de TVA du Cameroun (s'ils n'existent pas) et propose 19,25 % sur les nouveaux articles."""
    from apps.core.models import Societe

    from .models import Taxe
    from .plan_syscohada import TAXES

    for code, intitule, sens, taux, compte in TAXES:
        numero = Compte.objects.filter(numero=compte).first()
        if numero:
            Taxe.objects.get_or_create(code=code, defaults={"intitule": intitule, "sens": sens, "taux": Decimal(taux),
                                                           "compte": numero})
    societe = Societe.get()
    if not societe.taux_tva_defaut:
        societe.taux_tva_defaut = Decimal("19.25")
        societe.save(update_fields=["taux_tva_defaut"])


def configurer_tva_manuelle():
    """Aucune TVA paramétrée : les nouveaux articles sont proposés à 0 %, l'utilisateur saisit ses taux s'il le souhaite."""
    from apps.core.models import Societe

    societe = Societe.get()
    if societe.taux_tva_defaut:
        societe.taux_tva_defaut = ZERO
        societe.save(update_fields=["taux_tva_defaut"])
