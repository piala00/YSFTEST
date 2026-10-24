"""Sources de la reprise Sage 100 : lecture directe de la base SQL Server (lecture seule) ou fichiers CSV exportés.

Lecture directe : l'ERP se connecte au serveur SQL où se trouve le dossier Sage et n'exécute que des SELECT,
construits ici à partir de FICHIERS. Avant chaque table, il lit les colonnes réellement présentes
(INFORMATION_SCHEMA) : une colonne facultative absente est simplement omise, une colonne obligatoire absente
est signalée. Rien n'est jamais écrit dans la base Sage.
"""
import datetime
import re
from decimal import Decimal
from pathlib import Path

from . import FICHIERS, ORDRE, lire_csv

# Pièces commerciales reprises : ventes, achats, stocks ; archives, dépréciations et fabrication écartées
TYPES_ECARTES = (8, 18, 22, 24, 25, 26, 27)
TYPES_EN_COURS = (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15)     # devis, commandes, BL, retours… non facturés


def _date_sql(valeur):
    return f"'{valeur:%Y%m%d}'"                    # format sans ambiguïté pour SQL Server


class Requetes:
    """SELECT de lecture des tables Sage, adaptés aux colonnes présentes (toutes si `presentes` est None)."""

    def __init__(self, debut_exercice, date_bascule, historique_depuis=None, presentes=None):
        self.debut, self.bascule = debut_exercice, date_bascule
        self.historique = historique_depuis or debut_exercice
        self.presentes = presentes            # {table: set(colonnes)} ou None (script complet)

    def a(self, table, colonne):
        return self.presentes is None or colonne in self.presentes.get(table, set())

    def colonnes(self, nom, alias=""):
        table, spec = FICHIERS[nom]
        return [f"{alias}{c}" for c in spec if c != "EC_DateCompta" and self.a(table, c)]

    def _date_compta(self):
        return "DATEADD(day, e.EC_Jour - 1, e.JM_Date)"

    def _filtre_ecritures(self):
        conditions = [f"{self._date_compta()} BETWEEN {_date_sql(self.debut)} AND {_date_sql(self.bascule)}"]
        if self.a("F_ECRITUREC", "EC_Norme"):
            conditions.append("e.EC_Norme IN (0, 1)")          # norme nationale : jamais l'IFRS seule
        if self.a("F_JOURNAUX", "JO_Type"):
            conditions.append("(j.JO_Type IS NULL OR j.JO_Type <> 4)")   # journaux de situation exclus
        return " AND ".join(conditions)

    def _pieces(self, d):
        """Pièces reprises : l'historique depuis la date choisie, et toujours les pièces en cours (non facturées)
        et les factures non soldées, quelle que soit leur date."""
        ouvertes = [f"{d}.DO_Date >= {_date_sql(self.historique)}", f"{d}.DO_Type IN {TYPES_EN_COURS}"]
        if self.a("F_DOCREGL", "DR_Regle"):
            ouvertes.append(f"EXISTS (SELECT 1 FROM dbo.F_DOCREGL r WHERE r.DO_Domaine = {d}.DO_Domaine AND "
                            f"r.DO_Type = {d}.DO_Type AND r.DO_Piece = {d}.DO_Piece AND r.DR_Regle = 0)")
        return (f"{d}.DO_Domaine IN (0, 1, 2) AND {d}.DO_Type NOT IN {TYPES_ECARTES} "
                f"AND ({' OR '.join(ouvertes)})")

    def _de_pieces(self, alias):
        return (f"EXISTS (SELECT 1 FROM dbo.F_DOCENTETE d WHERE d.DO_Domaine = {alias}.DO_Domaine AND "
                f"d.DO_Type = {alias}.DO_Type AND d.DO_Piece = {alias}.DO_Piece AND {self._pieces('d')})")

    def sql(self, nom):
        table, spec = FICHIERS[nom]
        cols = ", ".join(self.colonnes(nom))
        if nom == "soldes":
            return self._soldes()
        if nom == "familles":
            return f"SELECT {cols} FROM dbo.F_FAMILLE ORDER BY FA_CodeFamille"
        if nom == "ecritures":
            cols = ", ".join(self.colonnes(nom, "e."))
            cols = cols.replace("e.JO_Num", f"e.JO_Num, CONVERT(char(10), {self._date_compta()}, 23) AS EC_DateCompta")
            return (f"SELECT {cols} FROM dbo.F_ECRITUREC AS e LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num "
                    f"WHERE {self._filtre_ecritures()} ORDER BY e.JO_Num, e.JM_Date, e.EC_Piece, e.EC_No")
        if nom == "analytique":
            return (f"SELECT {', '.join(self.colonnes(nom, 'a.'))} FROM dbo.F_ECRITUREA AS a "
                    f"JOIN dbo.F_ECRITUREC AS e ON e.EC_No = a.EC_No LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num "
                    f"WHERE {self._filtre_ecritures()} ORDER BY a.EC_No")
        if nom == "documents":
            return f"SELECT {cols} FROM dbo.F_DOCENTETE AS x WHERE {self._pieces('x')} ORDER BY DO_Domaine, DO_Type, DO_Piece"
        if nom == "lignes":
            ordre = "l.DL_Ligne" if self.a("F_DOCLIGNE", "DL_Ligne") else "l.DL_No" if self.a("F_DOCLIGNE", "DL_No") else "l.DO_Piece"
            return (f"SELECT {', '.join(self.colonnes(nom, 'l.'))} FROM dbo.F_DOCLIGNE AS l WHERE {self._de_pieces('l')} "
                    f"ORDER BY l.DO_Domaine, l.DO_Type, l.DO_Piece, {ordre}")
        if nom == "echeances":
            return (f"SELECT {', '.join(self.colonnes(nom, 'x.'))} FROM dbo.F_DOCREGL AS x WHERE {self._de_pieces('x')} "
                    f"ORDER BY x.DR_No")
        if nom == "reglements":
            cols = ", ".join(self.colonnes(nom, "g."))
            if self.a("F_REGLECH", "RC_Montant"):
                reste = "g.RG_Montant > (SELECT ISNULL(SUM(c.RC_Montant), 0) FROM dbo.F_REGLECH AS c WHERE c.RG_No = g.RG_No)"
            elif self.a("F_CREGLEMENT", "RG_Impute"):
                reste = "ISNULL(g.RG_Impute, 0) = 0"
            else:
                reste = "1 = 1"
            return f"SELECT {cols} FROM dbo.F_CREGLEMENT AS g WHERE {reste} ORDER BY g.RG_No"
        if nom == "imputations":
            return (f"SELECT {', '.join(self.colonnes(nom, 'c.'))} FROM dbo.F_REGLECH AS c "
                    f"WHERE EXISTS (SELECT 1 FROM dbo.F_DOCREGL AS x WHERE x.DR_No = c.DR_No AND {self._de_pieces('x')}) "
                    f"ORDER BY c.RG_No, c.DR_No")
        premiere = next(iter(spec))
        return f"SELECT {cols} FROM dbo.{table} ORDER BY {premiere}"

    def _soldes(self):
        return ("SELECT e.CG_Num, ISNULL(e.CT_Num, '') AS CT_Num, "
                "SUM(CASE WHEN e.EC_Sens = 0 THEN e.EC_Montant ELSE 0 END) AS Debit, "
                "SUM(CASE WHEN e.EC_Sens = 1 THEN e.EC_Montant ELSE 0 END) AS Credit "
                "FROM dbo.F_ECRITUREC AS e LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num "
                f"WHERE {self._filtre_ecritures()} GROUP BY e.CG_Num, ISNULL(e.CT_Num, '') ORDER BY e.CG_Num, CT_Num")


def script_export(debut_exercice, date_bascule, historique_depuis=None):
    """Script complet pour un export manuel en CSV (SQL Server Management Studio), une requête par fichier."""
    r = Requetes(debut_exercice, date_bascule, historique_depuis)
    blocs = ["/* EXPORT SAGE 100 SQL SERVER → ERP OHADA — LECTURE SEULE (uniquement des SELECT)",
             "   Exécutez chaque requête et enregistrez la grille dans le fichier CSV indiqué (avec l'en-tête).",
             "   Si une colonne « À CONFIRMER » n'existe pas dans votre version, retirez-la de la requête.",
             "   Choisissez soit soldes.csv (soldes d'ouverture), soit ecritures.csv + analytique.csv (détail). */"]
    for nom in ORDRE:
        blocs.append(f"\n-- {nom}.csv  ({FICHIERS[nom][0]})\n{r.sql(nom)};")
    return "\n".join(blocs) + "\n"


# ---------------------------------------------------------------------------
# Connexion en lecture seule
# ---------------------------------------------------------------------------
def connecter(serveur, base, utilisateur="", mot_de_passe=""):
    """Connexion au serveur SQL de Sage : pilote ODBC 18/17 s'il est installé, sinon pilote Microsoft fourni."""
    authentification = (f"UID={utilisateur};PWD={{{mot_de_passe.replace('}', '}}')}}}" if utilisateur
                        else "Trusted_Connection=yes")
    commun = f"SERVER={serveur};DATABASE={base};{authentification};TrustServerCertificate=yes;ApplicationIntent=ReadOnly"
    erreurs = []
    try:
        import pyodbc

        for pilote in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
            if pilote in pyodbc.drivers():
                return pyodbc.connect(f"DRIVER={{{pilote}}};{commun}", timeout=15, readonly=True)
    except Exception as exc:                     # pilote absent ou connexion refusée : essayer le pilote fourni
        erreurs.append(str(exc))
    try:
        import mssql_python

        return mssql_python.connect(commun)
    except ImportError:
        raise ConnectionError("Aucun pilote SQL Server disponible (ni ODBC 17/18, ni mssql-python). " + " ".join(erreurs))


class SourceSQL:
    """Lit directement les tables d'un dossier Sage 100 (SELECT uniquement)."""

    def __init__(self, connexion, debut_exercice, date_bascule, historique_depuis=None):
        self.connexion = connexion
        self.debut, self.bascule, self.historique = debut_exercice, date_bascule, historique_depuis
        self.presentes = self._colonnes_presentes()
        self.requetes = Requetes(debut_exercice, date_bascule, historique_depuis, self.presentes)

    def _executer(self, sql, parametres=()):
        texte = sql.strip()
        if not re.match(r"(?is)^select\b", texte) or ";" in texte.rstrip(";"):
            raise PermissionError("Seules les requêtes SELECT sont autorisées sur la base Sage.")
        curseur = self.connexion.cursor()
        try:
            curseur.execute(texte, parametres) if parametres else curseur.execute(texte)
            noms = [c[0] for c in curseur.description]
            return [dict(zip(noms, ligne)) for ligne in curseur.fetchall()]
        finally:
            curseur.close()

    def _colonnes_presentes(self):
        tables = sorted({t for t, _ in FICHIERS.values()})
        liste = ", ".join(f"'{t}'" for t in tables)
        presentes = {}
        for l in self._executer("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                f"WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ({liste})"):
            presentes.setdefault(l["TABLE_NAME"], set()).add(l["COLUMN_NAME"])
        return presentes

    def lire(self, nom):
        """(lignes en texte, colonnes obligatoires absentes) ; (None, []) si la table n'existe pas."""
        table, spec = FICHIERS[nom]
        if nom == "soldes" or table not in self.presentes:
            return None, []                    # en lecture directe, les écritures détaillées remplacent les soldes
        manquantes = [c for c, (obligatoire, *_) in spec.items()
                      if obligatoire and c != "EC_DateCompta" and c not in self.presentes[table]]
        if nom == "ecritures":
            manquantes += [c for c in ("EC_Jour", "JM_Date") if c not in self.presentes[table]]
        if manquantes:
            return [], manquantes
        return [{k: texte(v) for k, v in l.items()} for l in self._executer(self.requetes.sql(nom))], []


class SourceCSV:
    """Fichiers CSV exportés à la main (un fichier par donnée, nommé comme dans FICHIERS)."""

    def __init__(self, dossier):
        self.dossier = Path(dossier)

    def lire(self, nom):
        chemin = self.dossier / f"{nom}.csv"
        if not chemin.exists():
            return None, []
        lignes = lire_csv(chemin)
        requis = [c for c, (obligatoire, *_) in FICHIERS[nom][1].items() if obligatoire]
        return lignes, ([c for c in requis if c not in lignes[0]] if lignes else [])


def texte(valeur):
    """Valeur SQL → texte, comme dans un CSV (dates ISO, nombres sans séparateur de milliers)."""
    if valeur is None:
        return ""
    if isinstance(valeur, datetime.datetime):
        return valeur.date().isoformat()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    if isinstance(valeur, bool):
        return "1" if valeur else "0"
    if isinstance(valeur, Decimal):
        return format(valeur, "f")
    return str(valeur).strip()


def bases_sage(connexion):
    """Bases du serveur qui contiennent un dossier Sage 100 (table F_COMPTET), lues dans sys.databases."""
    curseur = connexion.cursor()
    curseur.execute("SELECT name FROM sys.databases WHERE database_id > 4 AND state = 0 ORDER BY name")
    noms = [r[0] for r in curseur.fetchall()]
    trouvees = []
    for nom in noms:
        try:
            curseur.execute(f"SELECT 1 FROM [{nom.replace(']', ']]')}].INFORMATION_SCHEMA.TABLES "
                            "WHERE TABLE_NAME = 'F_COMPTET'")
            if curseur.fetchone():
                trouvees.append(nom)
        except Exception:
            continue                           # base inaccessible avec ce compte
    curseur.close()
    return trouvees
