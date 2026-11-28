"""Reprise du dossier d'origine — comptabilité (journaux, analytique, taxes, écritures détaillées) et gestion commerciale
(tarifs, pièces en cours et historique, échéances, règlements).

Principes :
- les écritures Sage de l'exercice en cours sont reprises ligne à ligne (lettrage et analytique compris) : la
  comptabilité de l'ERP est celle de Sage à la date de bascule ;
- les pièces commerciales sont reprises telles quelles (n° Sage conservé) sans générer ni stock ni écriture : le
  stock vient de F_ARTSTOCK, la comptabilité des écritures Sage. Une facture garde son reste dû ; un règlement
  non imputé reste « en attente de rattachement » ;
- chaque bloc est contrôlé (équilibre, totaux) ; au moindre écart, la reprise entière est annulée.
"""
import datetime
import hashlib
from collections import OrderedDict, defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError

ZERO = Decimal("0")
CLE_ECRITURE = "ORIG|"          # clé source d'une pièce comptable : ORIG|journal|mois|n° de pièce

# (DO_Domaine, DO_Type) → type de pièce de l'ERP ; facture : selon DO_Provenance (1 retour, 2 avoir)
TYPES_PIECES = {
    (0, 0): "DEVIS", (0, 1): "COMMANDE", (0, 2): "PREPARATION", (0, 3): "LIVRAISON", (0, 4): "RETOUR",
    (0, 5): "AVOIR_FINANCIER", (0, 6): "FACTURE", (0, 7): "FACTURE",
    (1, 10): "ACHAT_DEMANDE", (1, 11): "ACHAT_PREPARATION", (1, 12): "ACHAT_COMMANDE", (1, 13): "ACHAT_RECEPTION",
    (1, 14): "ACHAT_RETOUR", (1, 15): "ACHAT_AVOIR_FINANCIER", (1, 16): "ACHAT_FACTURE", (1, 17): "ACHAT_FACTURE",
    (2, 20): "STOCK_ENTREE", (2, 21): "STOCK_SORTIE", (2, 23): "STOCK_VIREMENT",
}
PROVENANCES = {("FACTURE", "1"): "FACTURE_RETOUR", ("FACTURE", "2"): "AVOIR",
               ("ACHAT_FACTURE", "1"): "ACHAT_FACTURE_RETOUR", ("ACHAT_FACTURE", "2"): "ACHAT_AVOIR"}
TYPES_JOURNAUX = {"0": "ACHAT", "1": "VENTE", "2": "TRESORERIE", "3": "OD"}


def _entier(valeur, defaut=None):
    try:
        return int(Decimal((valeur or "").strip()))
    except Exception:
        return defaut


def _empreinte(valeur):
    """Empreinte d'un contenu d'origine : un changement dans l'ancien logiciel change l'empreinte."""
    return hashlib.sha256(repr(valeur).encode("utf-8")).hexdigest()


def _date(valeur):
    valeur = (valeur or "").strip()[:10]
    for format_ in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(valeur, format_).date()
        except ValueError:
            continue
    raise ValueError(f"date illisible « {valeur} »")


class Complements:
    # ------------------------------------------------------------------ référentiels comptables
    def _journaux(self, l, bilan):
        from apps.comptabilite.models import Compte, Journal

        type_sage = (l.get("JO_Type") or "3").strip()
        if type_sage == "4":
            bilan.ignorees += 1               # journal de situation : pas d'écritures réelles
            return
        valeurs = {"intitule": (l["JO_Intitule"] or l["JO_Num"])[:100], "type_journal": TYPES_JOURNAUX.get(type_sage, "OD")}
        if l.get("CG_Num") and valeurs["type_journal"] == Journal.TYPE_TRESORERIE:
            valeurs["compte_tresorerie"] = Compte.objects.filter(numero=l["CG_Num"]).first()
        self.journaux[l["JO_Num"]] = self._maj(Journal, {"code": l["JO_Num"][:10]}, valeurs, bilan)

    def _sections(self, l, bilan):
        from apps.comptabilite.models import SectionAnalytique

        if (l.get("CA_Type") or "0") not in ("", "0"):
            bilan.ignorees += 1               # section de total
            return
        plan, code = l["N_Analytique"], l["CA_Num"]
        # Même code de section dans deux plans : le second est préfixé du n° de son plan
        autre_plan = any(c == code and p != plan for p, c in self.sections)
        cle = f"{plan}-{code}"[:20] if autre_plan else code[:20]
        self.sections[(plan, code)] = self._maj(
            SectionAnalytique, {"code": cle},
            {"plan": f"Plan analytique {plan}", "intitule": (l["CA_Intitule"] or code)[:100],
             "actif": (l.get("CA_Sommeil") or "0") in ("", "0")}, bilan)

    def _taxes(self, l, bilan):
        from apps.comptabilite.models import Compte, Taxe

        compte = Compte.objects.filter(numero=l.get("CG_Num") or "").first()
        if compte is None:
            raise ValueError(f"taxe {l['TA_Code']} : compte {l.get('CG_Num') or '(vide)'} absent du plan : non reprise")
        sens = Taxe.COLLECTEE if (l.get("TA_Sens") or "1").strip() == "1" else Taxe.DEDUCTIBLE
        self._maj(Taxe, {"code": l["TA_Code"][:10]}, {"intitule": (l["TA_Intitule"] or l["TA_Code"])[:100], "sens": sens,
                                                      "taux": self.nombre(l["TA_Taux"]), "compte": compte}, bilan)

    def _categorie(self, numero):
        from apps.commercial.models import CategorieTarifaire

        categorie, _ = CategorieTarifaire.objects.get_or_create(
            code=f"CAT{numero}", defaults={"intitule": f"Catégorie tarifaire {numero} (reprise)"})
        return categorie

    def _tarifs(self, l, bilan):
        from apps.commercial.models import Article, TarifCategorie

        if (l.get("CT_Num") or "").strip():
            bilan.ignorees += 1
            if not getattr(self, "_tarif_client_signale", False):
                self._tarif_client_signale = True
                self.rapport.avertissements.append("Tarifs propres à un client (F_ARTCLIENT avec CT_Num) non repris : "
                                                   "l'ERP gère les tarifs par catégorie.")
            return
        article = Article.objects.filter(reference=l["AR_Ref"][:30]).first()
        numero = _entier(l["AC_Categorie"])
        if article is None or not numero:
            raise ValueError(f"tarif : article {l['AR_Ref']} inconnu ou catégorie « {l['AC_Categorie']} » invalide")
        self._maj(TarifCategorie, {"article": article, "categorie": self._categorie(numero)},
                  {"prix_vente": self.nombre(l["AC_PrixVen"])}, bilan)

    # ------------------------------------------------------------------ exercice et écritures
    def _exercice(self, debut_donnees, fin_donnees):
        """Exercice de l'ERP couvrant les écritures reprises ; créé s'il n'existe pas."""
        from apps.core.models import Exercice

        debut = self.debut_exercice or debut_donnees
        if Exercice.objects.filter(date_debut__lte=debut, date_fin__gte=fin_donnees).exists():
            return
        if Exercice.objects.filter(date_debut__lte=fin_donnees, date_fin__gte=debut).exists():
            raise ValidationError(f"Un exercice de l'ERP chevauche l'exercice d'origine (du {debut:%d/%m/%Y}) sans le couvrir : "
                                  "créez dans l'ERP l'exercice aux mêmes dates que dans l'ancien logiciel, puis relancez.")
        fin = debut.replace(year=debut.year + 1) - datetime.timedelta(days=1)
        Exercice.objects.create(code=f"{debut.year}" if debut.month == 1 else f"{debut:%Y-%m}", date_debut=debut,
                                date_fin=max(fin, fin_donnees))

    def _ecritures_bloc(self):
        from apps.commercial.models import Tiers
        from apps.comptabilite.models import Compte, Ecriture, Journal, LigneEcriture, SectionAnalytique
        from apps.core.models import Exercice, Sequence

        from . import _fmt

        bilan = self.rapport.bilans["ecritures"]
        lignes = self.donnees["ecritures"]
        if not lignes:
            return
        # Ventilations analytiques par ligne Sage
        ventilations = defaultdict(list)
        if "analytique" in self.donnees:
            self.rapport.bilans["analytique"].lues = len(self.donnees["analytique"])
            for a in self.donnees["analytique"]:
                section = self.sections.get((a["N_Analytique"], a["CA_Num"])) or \
                    SectionAnalytique.objects.filter(code=a["CA_Num"][:20]).first()
                if section is None:
                    self.rapport.bilans["analytique"].anomalies.append(
                        f"section {a['N_Analytique']}/{a['CA_Num']} inconnue : ventilation non reprise")
                    continue
                ventilations[a["EC_No"]].append((a["N_Analytique"], section, self.nombre(a["EA_Montant"])))
            # Chaque plan Sage ventile le montant entier de la ligne ; l'ERP n'a qu'une section par ligne :
            # le premier plan est repris, les autres sont signalés (sinon le montant serait compté deux fois)
            autres_plans = 0
            for no, liste in ventilations.items():
                premier = min(p for p, _, _ in liste)
                autres_plans += sum(1 for p, _, _ in liste if p != premier)
                ventilations[no] = [(section, montant) for p, section, montant in liste if p == premier]
            self.rapport.bilans["analytique"].ignorees = autres_plans
            if autres_plans:
                self.rapport.avertissements.append(
                    f"{autres_plans} ventilation(s) sur un second plan analytique non reprise(s) : l'ERP ventile chaque "
                    "ligne sur un seul plan (le premier).")
        # Lecture et contrôle des lignes
        comptes = {c.numero: c for c in Compte.objects.all()}
        tiers = {t.code: t for t in Tiers.objects.all()}
        manquants, sans_fiche = set(), set()
        pieces = OrderedDict()
        debit_source = credit_source = ZERO
        for l in lignes:
            date = _date(l["EC_DateCompta"])
            montant = self.nombre(l["EC_Montant"])
            debit, credit = (montant, ZERO) if l["EC_Sens"].strip() == "0" else (ZERO, montant)
            debit_source += debit
            credit_source += credit
            compte = comptes.get(l["CG_Num"])
            if compte is None:
                manquants.add(l["CG_Num"])
                continue
            code_tiers = (l.get("CT_Num") or "").strip()
            fiche = tiers.get(code_tiers[:20]) if code_tiers else None
            if code_tiers and fiche is None:
                sans_fiche.add(code_tiers)
            piece = pieces.setdefault((l["JO_Num"], f"{date:%Y-%m}", l["EC_Piece"]), [])
            piece.append({"no": l["EC_No"], "date": date, "compte": compte, "tiers": fiche, "debit": debit, "credit": credit,
                          "libelle": (l.get("EC_Intitule") or "")[:200], "lettrage": (l.get("EC_Lettrage") or "")[:10]})
        if manquants:
            self.rapport.erreurs.append("Écritures : comptes absents du plan " + ", ".join(sorted(manquants)[:20]))
            return
        if sans_fiche:
            self.rapport.avertissements.append(
                f"{len(sans_fiche)} compte(s) tiers des écritures sans fiche client/fournisseur (salariés, autres) : "
                "lignes reprises sur leur compte général, sans tiers.")
        # Pièces déséquilibrées : regroupées par journal et par mois (un journal Sage est équilibré sur la période)
        regroupees = OrderedDict()
        for (journal, mois, numero), l in pieces.items():
            if sum(x["debit"] for x in l) == sum(x["credit"] for x in l):
                regroupees[(journal, mois, numero)] = l
            else:
                regroupees.setdefault((journal, mois, "*"), []).extend(l)
        for cle, l in regroupees.items():
            if cle[2] == "*" and sum(x["debit"] for x in l) != sum(x["credit"] for x in l):
                self.rapport.erreurs.append(f"Écritures du journal {cle[0]} en {cle[1]} déséquilibrées dans le dossier d'origine.")
        if self.rapport.erreurs:
            return
        dates = [x["date"] for l in regroupees.values() for x in l]
        self._exercice(min(dates), max(dates))
        # Journaux absents de F_JOURNAUX : créés en opérations diverses
        for code in {c[0] for c in regroupees}:
            if code not in self.journaux:
                journal = Journal.objects.filter(code=code[:10]).first()
                if journal is None:
                    journal = Journal.objects.create(code=code[:10], intitule=f"Journal {code} (reprise)", type_journal=Journal.TYPE_OD)
                    bilan.anomalies.append(f"journal {code} absent de F_JOURNAUX : créé en opérations diverses")
                self.journaux[code] = journal
        # Synchronisation : chaque pièce d'origine a une clé stable et une empreinte de son contenu. Nouvelle pièce :
        # créée ; contenu changé : lignes refaites (n° ERP conservé) ; pièce disparue de la période : supprimée.
        existantes = {e.source_cle: e for e in Ecriture.objects.filter(source_cle__startswith=CLE_ECRITURE)}
        vues = set()
        for (code, mois, numero), l in regroupees.items():
            cle = f"{CLE_ECRITURE}{code}|{mois}|{numero}"[:80]
            vues.add(cle)
            empreinte = _empreinte([(x["no"], x["date"], x["compte"].numero, getattr(x["tiers"], "code", ""), x["debit"],
                                     x["credit"], x["libelle"], x["lettrage"],
                                     [(s.code, m) for s, m in ventilations.get(x["no"], [])]) for x in l])
            journal, date = self.journaux[code], min(x["date"] for x in l)
            libelle = (next((x["libelle"] for x in l if x["libelle"]), "") or f"Pièce {numero} reprise")[:200]
            reference = (numero if numero != "*" else f"{code} {mois}")[:50]
            ecriture = existantes.get(cle)
            if ecriture is not None and ecriture.source_empreinte == empreinte:
                continue
            if ecriture is None:
                ecriture = Ecriture.objects.create(
                    journal=journal, exercice=Exercice.pour_date(date), date=date, statut=Ecriture.STATUT_VALIDEE,
                    numero=Sequence.suivant(journal.code, date.year, largeur=6), cree_par=self.utilisateur,
                    libelle=libelle, reference=reference, source_cle=cle, source_empreinte=empreinte)
                bilan.creees += 1
            else:
                ecriture.lignes.all().delete()
                ecriture.journal, ecriture.date, ecriture.exercice = journal, date, Exercice.pour_date(date)
                ecriture.libelle, ecriture.reference, ecriture.source_empreinte = libelle, reference, empreinte
                ecriture.save()
                bilan.mises_a_jour += 1
            if "analytique" in self.rapport.bilans:                # ventilations (re)passées avec la pièce
                self.rapport.bilans["analytique"].creees += sum(len(ventilations.get(x["no"], [])) for x in l)
            lignes_erp = []
            for x in l:
                # Ventilation analytique : la ligne est découpée par section, le reste sans section
                reste_d, reste_c = x["debit"], x["credit"]
                for section, montant in ventilations.get(x["no"], []):
                    d, c = (montant, ZERO) if x["debit"] else (ZERO, montant)
                    lignes_erp.append(LigneEcriture(ecriture=ecriture, compte=x["compte"], tiers=x["tiers"], section=section,
                                                    libelle=x["libelle"], debit=d, credit=c, lettrage=x["lettrage"],
                                                    source_cle=x["no"][:20]))
                    reste_d -= d
                    reste_c -= c
                if reste_d or reste_c:
                    lignes_erp.append(LigneEcriture(ecriture=ecriture, compte=x["compte"], tiers=x["tiers"], libelle=x["libelle"],
                                                    debit=reste_d, credit=reste_c, lettrage=x["lettrage"], source_cle=x["no"][:20]))
            LigneEcriture.objects.bulk_create(lignes_erp, batch_size=2000)
        # Pièces de la période synchronisée qui n'existent plus à l'origine (supprimées dans l'ancien logiciel)
        debut_periode = self.debut_exercice or min(dates)
        for cle, ecriture in existantes.items():
            if cle not in vues and debut_periode <= ecriture.date <= self.date:
                ecriture.delete()
                bilan.supprimees += 1
        # Contrôles sur l'ensemble des écritures synchronisées de la période (pas seulement celles de ce passage)
        synchronisees = LigneEcriture.objects.filter(ecriture__source_cle__startswith=CLE_ECRITURE,
                                                     ecriture__date__range=(debut_periode, self.date))
        debit = sum((x.debit for x in synchronisees), ZERO)
        credit = sum((x.credit for x in synchronisees), ZERO)
        nb_erp = len({x.source_cle for x in synchronisees})
        self.rapport.controles.append(("Écritures : total débit origine = ERP", _fmt(debit_source), _fmt(debit), debit_source == debit))
        self.rapport.controles.append(("Écritures : total crédit origine = ERP", _fmt(credit_source), _fmt(credit), credit_source == credit))
        self.rapport.controles.append(("Écritures : nombre de lignes origine = ERP (avant ventilation analytique)",
                                       str(len(lignes)), str(nb_erp), len(lignes) == nb_erp))
        negatives = [n for n, v in ventilations.items() if v and any(m < 0 for _, m in v)]
        if negatives:
            self.rapport.avertissements.append(f"{len(negatives)} ventilation(s) analytique(s) négative(s) : à vérifier.")

    # ------------------------------------------------------------------ pièces commerciales et règlements
    def _pieces_bloc(self):
        """Pièces commerciales, échéances et règlements : synchronisés par clé (domaine-type-n°) et empreinte."""
        from apps.commercial.models import Article, Depot, Document, Imputation, LigneDocument, Reglement, Tiers
        from apps.comptabilite.models import Journal

        from . import _fmt

        bilan = self.rapport.bilans["documents"]
        tiers = {t.code: t for t in Tiers.objects.all()}
        articles = {a.reference: a for a in Article.objects.all()}
        depots = {d.code: d for d in Depot.objects.all()}
        par_defaut = Depot.par_defaut()
        lignes_par_piece = defaultdict(list)
        for l in self.donnees.get("lignes", []):
            lignes_par_piece[(l["DO_Domaine"], l["DO_Type"], l["DO_Piece"])].append(l)
        echeances = defaultdict(list)
        for e in self.donnees.get("echeances", []):
            echeances[(e["DO_Domaine"], e["DO_Type"], e["DO_Piece"])].append(e)
        impute_par_echeance, impute_par_reglement = defaultdict(lambda: ZERO), defaultdict(lambda: ZERO)
        avec_montant = any("RC_Montant" in i for i in self.donnees.get("imputations", [])[:1])
        for i in self.donnees.get("imputations", []):
            if avec_montant:
                impute_par_echeance[i["DR_No"]] += self.nombre(i["RC_Montant"])
                impute_par_reglement[i["RG_No"]] += self.nombre(i["RC_Montant"])
        if self.donnees.get("echeances") and not avec_montant:
            self.rapport.avertissements.append("RC_Montant absent de F_REGLECH : une échéance est soit réglée (DR_Regle = 1), "
                                               "soit due en entier ; les règlements partiels d'une échéance sont à vérifier.")

        existantes = {d.reprise_sage: d for d in Document.objects.exclude(reprise_sage="")}
        numeros = set(Document.objects.values_list("numero", flat=True))
        ttc_source = ttc_erp = ZERO
        restes, vues = {}, set()
        refaites = {"lignes": 0, "echeances": 0}                   # lignes et échéances des pièces créées ou mises à jour
        for d in self.donnees["documents"]:
            cle = (d["DO_Domaine"], d["DO_Type"], d["DO_Piece"])
            type_erp = TYPES_PIECES.get((_entier(d["DO_Domaine"]), _entier(d["DO_Type"])))
            if type_erp is None:
                bilan.ignorees += 1
                continue
            type_erp = PROVENANCES.get((type_erp, (d.get("DO_Provenance") or "0").strip()), type_erp)
            domaine = _entier(d["DO_Domaine"])
            fiche = tiers.get((d.get("DO_Tiers") or "").strip()[:20]) if domaine in (0, 1) else None
            if domaine in (0, 1) and fiche is None:
                bilan.ignorees += 1
                bilan.anomalies.append(f"pièce {d['DO_Piece']} : tiers « {d.get('DO_Tiers')} » inconnu, non reprise")
                continue
            cle_erp = f"{d['DO_Domaine']}-{d['DO_Type']}-{d['DO_Piece']}"[:40]
            vues.add(cle_erp)
            lignes_source = lignes_par_piece.get(cle, [])
            ech = echeances.get(cle, [])
            empreinte = _empreinte([d, lignes_source, ech])
            payeur = tiers.get((d.get("CT_NumPayeur") or "").strip()[:20])
            entete = {"type_document": type_erp, "date": _date(d["DO_Date"]), "tiers": fiche,
                      "payeur": payeur if payeur and fiche and payeur.pk != fiche.pk else None,
                      "depot": depots.get(d.get("DE_No") or "") or par_defaut,
                      "depot_destination": depots.get(d.get("DO_Tiers") or "") if type_erp == "STOCK_VIREMENT" else None,
                      "reference_externe": (d.get("DO_Ref") or "")[:50]}
            doc = existantes.get(cle_erp)
            if doc is not None and doc.source_empreinte == empreinte:
                pass                                       # inchangée depuis le passage précédent
            elif doc is not None and (doc.documents_generes.exists() or
                                      doc.imputations.exclude(reglement__reprise_sage__in=("ANTERIEURS",)).exists()):
                bilan.anomalies.append(f"pièce {doc.numero} modifiée à l'origine mais déjà utilisée dans l'ERP : non mise à jour")
            else:
                if doc is None:
                    numero = d["DO_Piece"][:30]
                    if numero in numeros:                  # même n° déjà utilisé : suffixe du type d'origine
                        numero = f"{numero}-{d['DO_Type']}"[:30]
                    numeros.add(numero)
                    doc = Document.objects.create(numero=numero, statut=Document.VALIDE, cree_par=self.utilisateur,
                                                  reprise_sage=cle_erp, source_empreinte=empreinte,
                                                  notes="Pièce reprise du dossier d'origine (ni stock ni écriture générés par l'ERP)",
                                                  **entete)
                    bilan.creees += 1
                else:
                    for champ, valeur in entete.items():
                        setattr(doc, champ, valeur)
                    doc.source_empreinte, doc.statut = empreinte, Document.VALIDE
                    doc.save()
                    doc.lignes.all().delete()
                    bilan.mises_a_jour += 1
                refaites["lignes"] += len(lignes_source)
                refaites["echeances"] += len(ech)
                lignes_erp = []
                for l in lignes_source:
                    quantite, ht, ttc = self.nombre(l["DL_Qte"]), self.nombre(l["DL_MontantHT"]), self.nombre(l["DL_MontantTTC"])
                    tva = ZERO if doc.est_stock else ttc - ht
                    lignes_erp.append(LigneDocument(
                        document=doc, article=articles.get((l.get("AR_Ref") or "").strip()[:30]),
                        designation=(l.get("DL_Design") or l.get("AR_Ref") or "")[:200], quantite=quantite,
                        prix_unitaire=(ht / quantite).quantize(Decimal("0.01")) if quantite else ht,
                        taux_tva=(tva * 100 / ht).quantize(Decimal("0.01")) if ht else ZERO, montant_ht=ht, montant_tva=tva))
                LigneDocument.objects.bulk_create(lignes_erp)
                doc.recalculer()
                if ech:
                    ouvertes = [e for e in ech if (e.get("DR_Regle") or "0").strip() in ("", "0")]
                    doc.date_echeance = min(_date(e["DR_Date"]) for e in (ouvertes or ech))
                    doc.save(update_fields=["date_echeance"])
            if doc.est_facturation:
                ttc_source += sum((self.nombre(l["DL_MontantTTC"]) for l in lignes_source), ZERO)
                ttc_erp += doc.total_ttc
            if doc.est_facturation and not doc.est_avoir:
                if ech and avec_montant:
                    reste = sum((self.nombre(e["DR_Montant"]) - impute_par_echeance[e["DR_No"]] for e in ech), ZERO)
                elif ech:
                    reste = sum((self.nombre(e["DR_Montant"]) for e in ech if (e.get("DR_Regle") or "0").strip() in ("", "0")), ZERO)
                else:
                    reste = doc.total_ttc
                    bilan.anomalies.append(f"facture {doc.numero} sans échéance dans le dossier d'origine : reprise entièrement due")
                restes[doc] = max(min(reste, doc.total_ttc), ZERO)
        # Pièces reprises qui ne sont plus dans l'extraction : facture → soldée (l'extraction garde toute facture
        # non soldée) ; pièce en cours → transformée dans l'ancien logiciel (commande devenue BL, BL facturé…)
        for cle_erp, doc in existantes.items():
            if cle_erp in vues:
                continue
            if doc.est_facturation and not doc.est_avoir:
                restes[doc] = ZERO
            elif not doc.est_facturation and not doc.est_stock and doc.statut == Document.VALIDE:
                doc.statut = Document.TRANSFORME
                doc.save(update_fields=["statut"])
                bilan.mises_a_jour += 1
        for nom, nombre in refaites.items():
            if nom in self.rapport.bilans:
                self.rapport.bilans[nom].creees = nombre
        if "imputations" in self.rapport.bilans and not existantes:  # premier passage ; ensuite : règlements recalculés
            self.rapport.bilans["imputations"].creees = self.rapport.bilans["imputations"].lues
        self.rapport.controles.append(("Pièces : total TTC des factures origine = ERP", _fmt(ttc_source), _fmt(ttc_erp),
                                       abs(ttc_source - ttc_erp) <= Decimal("0.01") * max(len(restes), 1)))

        # Part déjà réglée à l'origine : un règlement technique par tiers (sans écriture : déjà comptabilisé à
        # l'origine), recalculé à chaque passage
        journal_an = Journal.objects.filter(type_journal=Journal.TYPE_AN).first()
        Reglement.objects.filter(reprise_sage="ANTERIEURS").delete()
        anterieurs = defaultdict(list)
        for doc, reste in restes.items():
            paye = doc.total_ttc - reste - sum((i.montant for i in doc.imputations.all()), ZERO)
            if paye > 0:
                anterieurs[doc.tiers_payeur].append((doc, paye))
        for t, liste in anterieurs.items():
            reglement = Reglement.objects.create(
                tiers=t, date=self.date, montant=sum((p for _, p in liste), ZERO), journal=journal_an,
                numero=f"RS-ANT-{t.code}"[:30], libelle="Règlements antérieurs (reprise)", reprise_sage="ANTERIEURS",
                cree_par=self.utilisateur)
            Imputation.objects.bulk_create([Imputation(reglement=reglement, document=doc, montant=p) for doc, p in liste])
        # Règlements non (entièrement) imputés à l'origine : en attente de rattachement dans l'ERP
        bilan_r = self.rapport.bilans.get("reglements") or self.rapport.bilans.setdefault("reglements", type(bilan)("reglements"))
        journal_defaut = Journal.objects.filter(code="CA").first() or journal_an
        existants = {r.reprise_sage: r for r in Reglement.objects.filter(reprise_sage__startswith="RG-")}
        vus = set()
        for r in self.donnees.get("reglements", []):
            fiche = tiers.get((r.get("CT_NumPayeur") or "").strip()[:20])
            if fiche is None:
                bilan_r.ignorees += 1
                bilan_r.anomalies.append(f"règlement {r['RG_No']} : tiers « {r.get('CT_NumPayeur')} » inconnu")
                continue
            montant = self.nombre(r["RG_Montant"])
            reste = montant - impute_par_reglement[r["RG_No"]] if avec_montant else \
                (montant if (r.get("RG_Impute") or "0").strip() in ("", "0") else ZERO)
            if reste <= 0:
                bilan_r.ignorees += 1
                continue
            cle = f"RG-{r['RG_No']}"[:40]
            vus.add(cle)
            valeurs = {"tiers": fiche, "date": _date(r["RG_Date"]), "montant": reste,
                       "journal": self.journaux.get(r.get("JO_Num") or "") or journal_defaut,
                       "reference": (r.get("RG_Reference") or "")[:60],
                       "libelle": ((r.get("RG_Libelle") or f"Règlement repris n° {r['RG_No']}") +
                                   ("" if reste == montant else f" (reste non imputé sur {montant:,.0f})".replace(",", " ")))[:200]}
            existant = existants.get(cle)
            if existant is None:
                Reglement.objects.create(numero=f"RS-{r['RG_No']}"[:30], reprise_sage=cle, cree_par=self.utilisateur, **valeurs)
                bilan_r.creees += 1
            elif any(getattr(existant, k) != v for k, v in valeurs.items()):
                if existant.imputations.exists():
                    bilan_r.anomalies.append(f"règlement {existant.numero} déjà rattaché dans l'ERP : non mis à jour")
                else:
                    for k, v in valeurs.items():
                        setattr(existant, k, v)
                    existant.save()
                    bilan_r.mises_a_jour += 1
        for cle, existant in existants.items():         # entièrement imputé (ou supprimé) à l'origine depuis
            if cle not in vus and not existant.imputations.exists():
                existant.delete()
                bilan_r.supprimees += 1
        self._rapprocher_tiers(restes)
        en_attente = sum((r.montant for r in Reglement.objects.filter(reprise_sage__startswith="RG-")), ZERO)
        if en_attente:
            self.rapport.avertissements.append(
                f"Règlements non imputés repris en attente de rattachement : {_fmt(en_attente)}.")

    def _rapprocher_tiers(self, restes):
        """Par tiers : factures non soldées − règlements en attente − avoirs repris = solde comptable repris (si les
        écritures sont reprises). Écart signalé, non bloquant : avoirs déjà imputés, OD de tiers… à vérifier."""
        from django.db.models import Sum

        from apps.commercial.models import Document, Reglement
        from apps.comptabilite.models import LigneEcriture

        from . import _fmt

        if "ecritures" not in self.donnees:
            return
        attendu = defaultdict(lambda: ZERO)
        for doc, reste in restes.items():
            attendu[doc.tiers_payeur] += reste if doc.est_vente else -reste
        for r in Reglement.objects.filter(reprise_sage__startswith="RG-").select_related("tiers"):
            attendu[r.tiers] += -r.montant if r.est_encaissement else r.montant
        for avoir in Document.objects.exclude(reprise_sage="").filter(type_document__in=("AVOIR", "ACHAT_AVOIR")):
            attendu[avoir.tiers_payeur] += -avoir.total_ttc if avoir.est_vente else avoir.total_ttc
        ecarts = []
        for tiers, montant in attendu.items():
            agg = LigneEcriture.objects.filter(tiers=tiers).aggregate(d=Sum("debit"), c=Sum("credit"))
            solde = (agg["d"] or ZERO) - (agg["c"] or ZERO)
            if solde != montant:
                ecarts.append(f"{tiers.code} : pièces {_fmt(montant)} · comptabilité {_fmt(solde)}")
        if ecarts:
            self.rapport.avertissements.append("Tiers dont les pièces reprises ne correspondent pas au solde comptable "
                                               f"({len(ecarts)}) : " + " ; ".join(ecarts[:20]))
        else:
            self.rapport.controles.append(("Créances et dettes : pièces reprises = soldes comptables des tiers",
                                           f"{len(attendu)} tiers", f"{len(attendu)} tiers", True))
