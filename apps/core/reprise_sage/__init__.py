"""Reprise des données d'un dossier Sage 100 SQL Server dans l'ERP.

Principe (skill « sage100-sql-server-structure-v5-v12 ») :
- Sage n'est jamais modifié : l'utilisateur exécute les SELECT de `export_sage100_lecture_seule.sql` sur une
  copie de test, puis sur la base réelle, et enregistre chaque résultat en CSV ;
- l'ERP lit ces CSV. Par défaut il ne fait qu'une simulation (rien n'est enregistré) et rend un rapport de
  rapprochement : nombres de fiches, quantités et valeurs de stock, débits et crédits des soldes ;
- l'import est rejouable : une fiche existante est mise à jour, le stock et les soldes d'ouverture ne sont
  passés qu'une fois.

Chaque colonne porte un statut : DOCUMENTÉ (manuel « Structure des bases Sage 100 V12.20 », référence du
catalogue du skill) ou À CONFIRMER (connu des installations Sage mais absent du catalogue : vérifier sur la
base réelle avant de s'y fier).
"""
import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

DOC = "DOCUMENTÉ V12.20"
A_CONFIRMER = "À CONFIRMER"
REFERENCE_REPRISE = "REPRISE SAGE"
SQL_EXPORT = Path(__file__).with_name("export_sage100_lecture_seule.sql")

# fichier → (table Sage, {colonne: (obligatoire, statut, référence catalogue, usage dans l'ERP)})
FICHIERS = {
    "depots": ("F_DEPOT", {
        "DE_No": (True, DOC, "C067", "Code du dépôt"),
        "DE_Intitule": (True, DOC, "CX071", "Intitulé"),
        "DE_Principal": (False, DOC, "CX077", "Dépôt principal (1 = oui)"),
        "DE_Ville": (False, DOC, "CX075", "Ville"),
    }),
    "familles": ("F_FAMILLE", {
        "FA_CodeFamille": (True, DOC, "C068", "Code famille"),
        "FA_Intitule": (True, DOC, "CX001", "Libellé"),
        "FA_Type": (False, DOC, "C069", "Seul le type 0 (famille de détail) est repris"),
    }),
    "comptes": ("F_COMPTEG", {
        "CG_Num": (True, DOC, "C085", "Numéro de compte"),
        "CG_Intitule": (True, DOC, "M01 V12.20", "Intitulé du compte"),
    }),
    "tiers": ("F_COMPTET", {
        "CT_Num": (True, DOC, "C070", "Code tiers"),
        "CT_Intitule": (True, DOC, "M01 V12.20", "Raison sociale"),
        "CT_Type": (True, DOC, "M01 V12.20", "0 = client, 1 = fournisseur ; les autres types sont ignorés"),
        "CG_NumPrinc": (False, DOC, "M01 V12.20", "Compte collectif"),
        "CT_Ville": (False, DOC, "M01 V12.20", "Ville"),
        "CT_Telephone": (False, DOC, "M01 V12.20", "Téléphone"),
        "CT_EMail": (False, DOC, "M01 V12.20", "E-mail"),
        "CT_Sommeil": (False, DOC, "M01 V12.20", "1 = en sommeil (repris inactif)"),
        "CT_NumPayeur": (False, DOC, "M01 V12.20", "Tiers payeur (égal à CT_Num quand le tiers règle lui-même)"),
    }),
    "articles": ("F_ARTICLE", {
        "AR_Ref": (True, DOC, "C058", "Référence"),
        "AR_Design": (True, DOC, "C060", "Désignation"),
        "FA_CodeFamille": (False, DOC, "C059", "Famille"),
        "AR_SuiviStock": (False, DOC, "CX015", "0 = sans suivi de stock, autre valeur = suivi"),
        "AR_Sommeil": (False, DOC, "IX006", "1 = en sommeil (repris inactif)"),
        "AR_PrixAch": (False, DOC, "M01 V12.20", "Prix d'achat HT"),
        "AR_PrixVen": (False, DOC, "M01 V12.20", "Prix de vente HT"),
    }),
    "stocks": ("F_ARTSTOCK", {
        "AR_Ref": (True, DOC, "C061", "Article"),
        "DE_No": (True, DOC, "C062", "Dépôt"),
        "AS_QteSto": (True, DOC, "CX032", "Quantité en stock (ni réservée, ni commandée : règle RGX001)"),
        "AS_MontSto": (True, DOC, "CX033", "Valeur du stock : coût d'entrée = AS_MontSto / AS_QteSto"),
        "AS_QteMini": (False, DOC, "CX030", "Stock minimum du dépôt"),
        "AS_QteMaxi": (False, DOC, "CX031", "Stock maximum du dépôt"),
    }),
    "soldes": ("F_ECRITUREC", {
        "CG_Num": (True, DOC, "C080", "Compte général"),
        "CT_Num": (True, DOC, "C081", "Compte tiers (vide si aucun)"),
        "Debit": (True, DOC, "C077 + C078", "Somme EC_Montant où EC_Sens = 0"),
        "Credit": (True, DOC, "C077 + C078", "Somme EC_Montant où EC_Sens = 1"),
    }),
}
ORDRE = ["depots", "familles", "comptes", "tiers", "articles", "stocks", "soldes"]


@dataclass
class Bilan:
    fichier: str
    lues: int = 0
    creees: int = 0
    mises_a_jour: int = 0
    ignorees: int = 0
    anomalies: list = field(default_factory=list)


@dataclass
class Rapport:
    simulation: bool
    bilans: dict = field(default_factory=dict)
    controles: list = field(default_factory=list)      # (contrôle, source Sage, ERP, conforme)
    erreurs: list = field(default_factory=list)

    @property
    def conforme(self):
        return not self.erreurs and all(c[3] for c in self.controles)

    def texte(self):
        lignes = [f"Reprise Sage 100 — {'SIMULATION (rien n’est enregistré)' if self.simulation else 'IMPORT ENREGISTRÉ'}", ""]
        lignes.append(f"{'Fichier':<10} {'lues':>6} {'créées':>7} {'m.à.j.':>7} {'ignorées':>9}")
        for b in self.bilans.values():
            lignes.append(f"{b.fichier:<10} {b.lues:>6} {b.creees:>7} {b.mises_a_jour:>7} {b.ignorees:>9}")
        if self.controles:
            lignes += ["", "Rapprochement"]
            for nom, source, erp, ok in self.controles:
                lignes.append(f"  [{'OK' if ok else 'ÉCART'}] {nom} : Sage {source} · ERP {erp}")
        anomalies = [(b.fichier, a) for b in self.bilans.values() for a in b.anomalies]
        if anomalies:
            lignes += ["", f"Anomalies ({len(anomalies)})"]
            lignes += [f"  {f} : {a}" for f, a in anomalies[:200]]
        if self.erreurs:
            lignes += ["", "Erreurs bloquantes"] + [f"  {e}" for e in self.erreurs]
        lignes += ["", "Résultat : " + ("conforme" if self.conforme else "à corriger avant import")]
        return "\n".join(lignes)


# ---------------------------------------------------------------------------
# Lecture des CSV
# ---------------------------------------------------------------------------
def lire_csv(chemin):
    texte = Path(chemin).read_text(encoding="utf-8-sig")
    try:
        dialecte = csv.Sniffer().sniff(texte.splitlines()[0], delimiters=";,\t")
    except (csv.Error, IndexError):
        dialecte = csv.excel
    return [{(k or "").strip(): (v or "").strip() for k, v in ligne.items()}
            for ligne in csv.DictReader(io.StringIO(texte), dialect=dialecte)]


def nombre(valeur):
    valeur = (valeur or "").replace(" ", "").replace("\xa0", "").replace(" ", "").replace(",", ".")
    if valeur in ("", "NULL"):
        return Decimal("0")
    try:
        return Decimal(valeur)
    except InvalidOperation:
        raise ValueError(f"nombre illisible « {valeur} »")


def vrai(valeur):
    return (valeur or "").strip().lower() in ("1", "true", "oui", "vrai")


def controler_colonnes(nom, lignes):
    """Colonnes obligatoires absentes (liste vide si le fichier est conforme)."""
    if not lignes:
        return []
    requis = [c for c, (obligatoire, *_) in FICHIERS[nom][1].items() if obligatoire]
    return [c for c in requis if c not in lignes[0]]


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def importer(dossier, date_bascule, appliquer=False, utilisateur=None):
    """Lit les CSV du dossier, importe (ou simule) et renvoie le rapport de rapprochement."""
    dossier = Path(dossier)
    rapport = Rapport(simulation=not appliquer)
    donnees = {}
    for nom in ORDRE:
        chemin = dossier / f"{nom}.csv"
        if not chemin.exists():
            continue
        lignes = lire_csv(chemin)
        manquantes = controler_colonnes(nom, lignes)
        if manquantes:
            rapport.erreurs.append(f"{nom}.csv : colonnes absentes {', '.join(manquantes)}")
        donnees[nom] = lignes
    if not donnees:
        rapport.erreurs.append(f"Aucun fichier CSV attendu dans {dossier} ({', '.join(n + '.csv' for n in ORDRE)}).")
    if rapport.erreurs:
        return rapport
    try:
        with transaction.atomic():
            _Import(donnees, date_bascule, rapport, utilisateur).executer()
            if not appliquer or not rapport.conforme:
                transaction.set_rollback(True)
    except ValidationError as exc:
        rapport.erreurs.extend(exc.messages)
    if appliquer and not rapport.conforme:
        rapport.simulation = True
        rapport.erreurs.append("Import annulé : corrigez les écarts ou erreurs ci-dessus (aucune donnée enregistrée).")
    return rapport


class _Import:
    def __init__(self, donnees, date_bascule, rapport, utilisateur):
        from apps.commercial.models import Depot

        self.donnees, self.date, self.rapport, self.utilisateur = donnees, date_bascule, rapport, utilisateur
        self.depots = {d.code: d for d in Depot.objects.all()}

    def executer(self):
        for nom in ORDRE:
            if nom in self.donnees:
                bilan = self.rapport.bilans[nom] = Bilan(nom, lues=len(self.donnees[nom]))
                for numero, ligne in enumerate(self.donnees[nom], start=2):
                    try:
                        getattr(self, f"_{nom}")(ligne, bilan)
                    except (ValueError, ValidationError) as exc:
                        bilan.ignorees += 1
                        message = "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
                        bilan.anomalies.append(f"ligne {numero} : {message}")
                fin = getattr(self, f"_fin_{nom}", None)
                if fin:
                    fin(bilan)

    @staticmethod
    def _maj(modele, cle, valeurs, bilan):
        objet, cree = modele.objects.get_or_create(**cle, defaults=valeurs)
        if cree:
            bilan.creees += 1
            return objet
        modifie = [k for k, v in valeurs.items() if getattr(objet, k) != v]
        if modifie:
            for k in modifie:
                setattr(objet, k, valeurs[k])
            objet.save(update_fields=modifie)
            bilan.mises_a_jour += 1
        return objet

    # --- Référentiels -------------------------------------------------------
    def _depots(self, l, bilan):
        from apps.commercial.models import Depot

        code = l["DE_No"]
        if not code:
            raise ValueError("DE_No vide")
        valeurs = {"intitule": l["DE_Intitule"][:100] or f"Dépôt {code}", "ville": l.get("DE_Ville", "")[:80]}
        if "DE_Principal" in l:
            valeurs["principal"] = vrai(l["DE_Principal"])
        self.depots[code] = self._maj(Depot, {"code": code[:10]}, valeurs, bilan)

    def _fin_depots(self, bilan):
        principaux = [l["DE_No"] for l in self.donnees["depots"] if vrai(l.get("DE_Principal"))]
        if len(principaux) > 1:      # l'ERP n'en garde qu'un : le dernier lu
            bilan.anomalies.append(f"plusieurs dépôts principaux dans Sage ({', '.join(principaux)}) : "
                                   "Sage n'en admet qu'un (règle RGX008), vérifier l'export")

    def _familles(self, l, bilan):
        from apps.commercial.models import FamilleArticle

        if l.get("FA_Type", "0") not in ("", "0"):
            bilan.ignorees += 1          # familles centralisatrices / totaux : pas d'articles rattachés
            return
        self._maj(FamilleArticle, {"code": l["FA_CodeFamille"][:20]}, {"libelle": l["FA_Intitule"][:100]}, bilan)

    def _comptes(self, l, bilan):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.plan_syscohada import LETTRABLES_PREFIXES

        numero = l["CG_Num"]
        if not numero.isdigit() or numero[0] == "0":
            raise ValueError(f"compte « {numero} » hors plan SYSCOHADA (chiffres, classes 1 à 9)")
        self._maj(Compte, {"numero": numero}, {"intitule": l["CG_Intitule"][:200],
                                               "lettrable": numero.startswith(LETTRABLES_PREFIXES)}, bilan)

    def _tiers(self, l, bilan):
        from apps.commercial.models import Tiers
        from apps.comptabilite.models import Compte

        type_tiers = {"0": Tiers.CLIENT, "1": Tiers.FOURNISSEUR}.get(l["CT_Type"])
        if type_tiers is None:
            bilan.ignorees += 1          # salariés, autres : comptes tiers sans fiche commerciale
            return
        valeurs = {"type_tiers": type_tiers, "nom": l["CT_Intitule"][:150] or l["CT_Num"],
                   "ville": l.get("CT_Ville", "")[:80], "telephone": l.get("CT_Telephone", "")[:50],
                   "actif": not vrai(l.get("CT_Sommeil"))}
        email = l.get("CT_EMail", "")
        if email and "@" in email:
            valeurs["email"] = email[:254]
        if l.get("CG_NumPrinc"):
            valeurs["compte_collectif"] = Compte.objects.filter(numero=l["CG_NumPrinc"]).first()
        self._maj(Tiers, {"code": l["CT_Num"][:20]}, valeurs, bilan)

    def _fin_tiers(self, bilan):
        """Tiers payeur, après la lecture de tous les tiers (le payeur peut figurer plus loin dans le fichier)."""
        from apps.commercial.models import Tiers

        for l in self.donnees["tiers"]:
            payeur = (l.get("CT_NumPayeur") or "").strip()
            tiers = Tiers.objects.filter(code=l["CT_Num"][:20]).first()
            if tiers is None:
                continue
            cible = None if payeur in ("", l["CT_Num"]) else Tiers.objects.filter(code=payeur[:20]).first()
            if payeur not in ("", l["CT_Num"]) and (cible is None or cible.type_tiers != tiers.type_tiers or cible.payeur_id):
                bilan.anomalies.append(f"tiers {l['CT_Num']} : payeur « {payeur} » introuvable, d'un autre type ou "
                                       "lui-même payé par un tiers : non repris")
                continue
            if tiers.payeur_id != getattr(cible, "pk", None):
                tiers.payeur = cible
                tiers.save(update_fields=["payeur"])

    def _articles(self, l, bilan):
        from apps.commercial.models import Article, FamilleArticle

        valeurs = {"designation": l["AR_Design"][:200] or l["AR_Ref"], "actif": not vrai(l.get("AR_Sommeil"))}
        if l.get("FA_CodeFamille"):
            valeurs["famille"] = FamilleArticle.objects.filter(code=l["FA_CodeFamille"]).first()
        if "AR_SuiviStock" in l:
            valeurs["suivi_stock"] = l["AR_SuiviStock"] not in ("", "0")
        for colonne, champ in (("AR_PrixAch", "prix_achat"), ("AR_PrixVen", "prix_vente")):
            if l.get(colonne):
                valeurs[champ] = nombre(l[colonne])
        self._maj(Article, {"reference": l["AR_Ref"][:30]}, valeurs, bilan)

    # --- Stock d'ouverture ----------------------------------------------------
    def _stocks(self, l, bilan):
        from apps.commercial.models import Article, StockDepot

        article = Article.objects.filter(reference=l["AR_Ref"]).first()
        depot = self.depots.get(l["DE_No"])
        if article is None or depot is None:
            raise ValueError(f"article {l['AR_Ref']} ou dépôt {l['DE_No']} inconnu (importez articles.csv et depots.csv)")
        quantite, valeur = nombre(l["AS_QteSto"]), nombre(l["AS_MontSto"])
        self.stock_source = getattr(self, "stock_source", [Decimal(0), Decimal(0)])
        self.stock_source[0] += quantite
        self.stock_source[1] += valeur
        if l.get("AS_QteMini") or l.get("AS_QteMaxi"):
            stock, _ = StockDepot.objects.get_or_create(article=article, depot=depot)
            stock.stock_mini, stock.stock_maxi = nombre(l.get("AS_QteMini")), nombre(l.get("AS_QteMaxi"))
            stock.save(update_fields=["stock_mini", "stock_maxi"])
        if quantite < 0:
            raise ValueError(f"stock négatif ({quantite}) pour {article.reference} au dépôt {depot.code} : à régulariser dans Sage")
        if quantite == 0:
            bilan.ignorees += 1
            return
        if not article.suivi_stock:
            raise ValueError(f"{article.reference} a du stock mais n'est pas suivi en stock")
        self.lignes_stock = getattr(self, "lignes_stock", {})
        self.lignes_stock.setdefault(depot, []).append((article, quantite, valeur / quantite))

    def _fin_stocks(self, bilan):
        from apps.commercial.models import Article, Document, LigneDocument, StockDepot

        deja = Document.objects.filter(type_document=Document.STOCK_ENTREE, reference_externe=REFERENCE_REPRISE)
        if deja.exists():
            bilan.anomalies.append("stock d'ouverture déjà repris : non rejoué")
        else:
            for depot, lignes in getattr(self, "lignes_stock", {}).items():
                doc = Document.objects.create(type_document=Document.STOCK_ENTREE, depot=depot, date=self.date,
                                              reference_externe=REFERENCE_REPRISE, cree_par=self.utilisateur,
                                              notes="Stock d'ouverture repris de Sage 100 (F_ARTSTOCK)")
                for article, quantite, cout in lignes:
                    LigneDocument.objects.create(document=doc, article=article, quantite=quantite, prix_unitaire=cout)
                doc.recalculer()
                doc.valider()
                bilan.creees += len(lignes)
        source = getattr(self, "stock_source", [Decimal(0), Decimal(0)])
        quantite = sum((s.quantite for s in StockDepot.objects.all()), Decimal(0))
        valeur = sum((a.valeur_stock for a in Article.objects.filter(suivi_stock=True)), Decimal(0))
        self.rapport.controles.append(("Quantité totale en stock", _fmt(source[0]), _fmt(quantite), source[0] == quantite))
        # Arrondis admis : coût unitaire au centime (prix_unitaire) et valeur arrondie au franc par article
        nb = sum(len(l) for l in getattr(self, "lignes_stock", {}).values())
        tolerance = Decimal("0.005") * source[0] + nb
        self.rapport.controles.append(("Valeur du stock", _fmt(source[1]), _fmt(valeur), abs(source[1] - valeur) <= tolerance))

    # --- Soldes d'ouverture -------------------------------------------------
    def _soldes(self, l, bilan):
        from apps.commercial.models import Tiers
        from apps.comptabilite.models import Compte

        compte = Compte.objects.filter(numero=l["CG_Num"]).first()
        if compte is None:
            raise ValueError(f"compte {l['CG_Num']} absent du plan (importez comptes.csv)")
        tiers = None
        if l["CT_Num"]:
            tiers = Tiers.objects.filter(code=l["CT_Num"]).first()
            if tiers is None:
                raise ValueError(f"tiers {l['CT_Num']} inconnu (importez tiers.csv)")
        debit, credit = nombre(l["Debit"]), nombre(l["Credit"])
        self.soldes = getattr(self, "soldes", [])
        self.soldes_source = getattr(self, "soldes_source", [Decimal(0), Decimal(0)])
        self.soldes_source[0] += debit
        self.soldes_source[1] += credit
        solde = debit - credit
        if solde:
            self.soldes.append({"compte": compte, "tiers": tiers, "debit": max(solde, 0), "credit": max(-solde, 0),
                                "libelle": "Reprise Sage 100"})
        else:
            bilan.ignorees += 1

    def _fin_soldes(self, bilan):
        from apps.comptabilite.models import Ecriture, Journal
        from apps.comptabilite.services import creer_ecriture

        debit, credit = getattr(self, "soldes_source", [Decimal(0), Decimal(0)])
        self.rapport.controles.append(("Équilibre des soldes Sage (débit = crédit)", _fmt(debit), _fmt(credit), debit == credit))
        if debit != credit:
            return
        if Ecriture.objects.filter(reference=REFERENCE_REPRISE).exists():
            bilan.anomalies.append("soldes d'ouverture déjà repris : non rejoués")
            return
        if getattr(self, "soldes", None):
            journal = Journal.objects.get(type_journal=Journal.TYPE_AN, code="AN")
            ecriture = creer_ecriture(journal, self.date, "Reprise des soldes Sage 100", self.soldes,
                                      reference=REFERENCE_REPRISE, origine="Sage 100")
            bilan.creees += ecriture.lignes.count()
            total = ecriture.total_debit
            nets = sum((s["debit"] for s in self.soldes), Decimal(0))
            self.rapport.controles.append(("Soldes repris dans le journal AN", _fmt(nets), _fmt(total), nets == total))


def _fmt(valeur):
    return f"{valeur:,.2f}".replace(",", " ").replace(".", ",").replace(",00", "")
