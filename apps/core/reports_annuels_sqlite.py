"""Reports à nouveau à partir des écritures validées de l'exercice N.

Adaptateur SQLite pour une base N+1 déjà migrée et dotée des référentiels
(comptes, tiers, journal AN, exercice). Ne copie aucune écriture de N.
Le résultat doit être équilibré après clôture du résultat comptable en N.
"""
from collections import defaultdict
from decimal import Decimal
import sqlite3


CENTIME = Decimal("0.01")


def _colonnes(connexion, table):
    return {ligne[1] for ligne in connexion.execute(f'PRAGMA table_info("{table}")')}


def _table(connexion, table):
    if connexion.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is None:
        raise ValueError(f"table absente : {table}")


def reporter_balance_validee(source: sqlite3.Connection, cible: sqlite3.Connection,
                             exercice_source_id: int, exercice_cible_id: int,
                             date_ouverture: str, journal_code: str = "AN"):
    """Écrit une pièce AN équilibrée, sans mouvements ni écritures brouillard.

    Les comptes de gestion (classes 6 et 7) doivent être soldés en N. Une
    balance non équilibrée est refusée plutôt que de fabriquer un résultat.
    Les lignes sont agrégées par compte ET tiers, préservant le suivi tiers.
    """
    for connexion in (source, cible):
        for table in ("comptabilite_compte", "comptabilite_journal",
                      "comptabilite_ecriture", "comptabilite_ligneecriture",
                      "core_exercice"):
            _table(connexion, table)
    for connexion in (source, cible):
        colonnes = _colonnes(connexion, "comptabilite_ligneecriture")
        if not {"tiers_id", "debit", "credit", "compte_id", "ecriture_id"} <= colonnes:
            raise ValueError("schéma comptable incompatible")
    if not cible.execute("SELECT 1 FROM core_exercice WHERE id=? AND cloture=0",
                         (exercice_cible_id,)).fetchone():
        raise ValueError("exercice N+1 absent ou clôturé")
    if not source.execute("SELECT 1 FROM core_exercice WHERE id=?",
                          (exercice_source_id,)).fetchone():
        raise ValueError("exercice N absent")
    journal = cible.execute("SELECT id FROM comptabilite_journal WHERE code=? AND type_journal='AN'",
                            (journal_code,)).fetchone()
    if journal is None:
        raise ValueError("journal des à-nouveaux absent")
    numero = f"AN-{date_ouverture[:4]}-OUVERTURE"
    if cible.execute("SELECT 1 FROM comptabilite_ecriture WHERE numero=?",
                     (numero,)).fetchone():
        raise ValueError("reports à nouveau déjà présents")
    if cible.execute("SELECT 1 FROM comptabilite_ecriture WHERE exercice_id=?",
                     (exercice_cible_id,)).fetchone():
        raise ValueError("exercice N+1 non vierge")
    if source.execute(
        "SELECT 1 FROM comptabilite_ecriture WHERE exercice_id=? AND statut!='VALIDEE' LIMIT 1",
        (exercice_source_id,),
    ).fetchone():
        raise ValueError("écritures non validées en N")
    lignes = source.execute("""
        SELECT c.numero, l.tiers_id, SUM(l.debit), SUM(l.credit)
        FROM comptabilite_ligneecriture l
        JOIN comptabilite_ecriture e ON e.id=l.ecriture_id
        JOIN comptabilite_compte c ON c.id=l.compte_id
        WHERE e.exercice_id=? AND e.statut='VALIDEE'
        GROUP BY c.numero, l.tiers_id
        ORDER BY c.numero, l.tiers_id
    """, (exercice_source_id,)).fetchall()
    # SQLite SUM(REAL) peut introduire des erreurs flottantes : vérifier
    # les sommes avec Decimal et arrondir au centime explicitement.
    soldes = defaultdict(lambda: Decimal("0.00"))
    for numero_compte, tiers_id, debit, credit in lignes:
        if not numero_compte or numero_compte[0] not in "12345":
            # Les comptes de gestion ne sont pas reportés.
            continue
        solde = (Decimal(str(debit or 0)) - Decimal(str(credit or 0))).quantize(CENTIME)
        soldes[(numero_compte, tiers_id)] += solde
    total = sum(soldes.values(), Decimal("0.00"))
    if total != 0:
        raise ValueError(f"balance d'ouverture déséquilibrée : {total} ; clôturer le résultat N")
    comptes = dict(cible.execute("SELECT numero, id FROM comptabilite_compte"))
    if "tiers_id" in _colonnes(cible, "comptabilite_ligneecriture"):
        _table(cible, "commercial_tiers")
    insertions = []
    for (numero_compte, tiers_id), solde in soldes.items():
        if not solde:
            continue
        if numero_compte not in comptes:
            raise ValueError(f"compte manquant dans N+1 : {numero_compte}")
        if tiers_id is not None and not cible.execute(
            "SELECT 1 FROM commercial_tiers WHERE id=?", (tiers_id,)
        ).fetchone():
            raise ValueError(f"tiers manquant dans N+1 : {tiers_id}")
        insertions.append((comptes[numero_compte], tiers_id, str(max(solde, 0)),
                           str(max(-solde, 0))))
    if not insertions:
        return 0
    # Le service appelant doit gérer la transaction ; SAVEPOINT permet
    # également une invocation indépendante sans écriture partielle.
    cible.execute("SAVEPOINT reports_ouverture")
    try:
        # Champs requis par les modèles Django Ecriture / LigneEcriture.
        import uuid
        cible.execute("""
            INSERT INTO comptabilite_ecriture
            (journal_id, exercice_id, numero, date, libelle, reference,
             statut, origine, source_cle, source_empreinte, uid, site_origine, cree_le)
            VALUES (?, ?, ?, ?, ?, '', 'VALIDEE', 'CLOTURE_ANNUELLE',
                    '', '', ?, '', CURRENT_TIMESTAMP)
        """, (journal[0], exercice_cible_id, numero, date_ouverture,
              "Reports à nouveau", str(uuid.uuid4())))
        piece_id = cible.execute("SELECT last_insert_rowid()").fetchone()[0]
        cible.executemany("""
            INSERT INTO comptabilite_ligneecriture
            (ecriture_id, compte_id, tiers_id, libelle, debit, credit,
             lettrage, source_cle)
            VALUES (?, ?, ?, 'Solde ouverture', ?, ?, '', '')
        """, [(piece_id, *ligne) for ligne in insertions])
    except Exception:
        cible.execute("ROLLBACK TO SAVEPOINT reports_ouverture")
        cible.execute("RELEASE SAVEPOINT reports_ouverture")
        raise
    cible.execute("RELEASE SAVEPOINT reports_ouverture")
    return len(insertions)
