"""Reports à nouveau à partir des écritures validées de l'exercice N.

Adaptateur SQLite pour une base N+1 déjà migrée et dotée des référentiels
(comptes, tiers, journal AN, exercice). Ne copie aucune écriture de N.
Le résultat doit être équilibré après clôture du résultat comptable en N.
"""
from collections import defaultdict
from decimal import Decimal
from datetime import date
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
    Les lignes sont agrégées par compte, tiers, section et véhicule,
    préservant les dimensions analytiques des soldes de bilan.
    """
    # Une pièce d'ouverture ne doit jamais être antidatée, ni rattachée
    # à un exercice différent de l'année de son numéro AN.
    try:
        ouverture = date.fromisoformat(date_ouverture)
    except (TypeError, ValueError) as exc:
        raise ValueError("date d'ouverture invalide") from exc
    if ouverture.month != 1 or ouverture.day != 1 or ouverture.isoformat() != date_ouverture:
        raise ValueError("date d'ouverture : premier janvier obligatoire")
    if "code" in _colonnes(cible, "core_exercice"):
        exercice = cible.execute("SELECT code FROM core_exercice WHERE id=?", (exercice_cible_id,)).fetchone()
        if exercice and str(exercice[0]) != str(ouverture.year):
            raise ValueError("année de la pièce AN différente de l'exercice N+1")
    for connexion in (source, cible):
        for table in ("comptabilite_compte", "comptabilite_journal",
                      "comptabilite_ecriture", "comptabilite_ligneecriture",
                      "core_exercice"):
            _table(connexion, table)
    for connexion in (source, cible):
        colonnes = _colonnes(connexion, "comptabilite_ligneecriture")
        if not {"tiers_id", "section_id", "vehicule_id", "debit", "credit", "compte_id", "ecriture_id"} <= colonnes:
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
    # Une balance globalement équilibrée ne garantit pas l'intégrité des pièces.
    # Refuser les écritures validées individuellement déséquilibrées, y compris
    # lorsque deux erreurs opposées se compensent dans le grand livre.
    # Une seule lecture ordonnée du grand livre valide chaque pièce et
    # agrège les soldes. Sur SQL Server distant, éviter deux parcours complets
    # réduit les allers-retours sans supprimer aucune vérification métier.
    # ORDER BY e.id permet de vérifier chaque pièce en flux, sans conserver
    # tous les totaux en mémoire sur les grands livres volumineux.
    piece_courante = None
    debit_piece = Decimal("0")
    credit_piece = Decimal("0")

    def verifier_piece(piece_id, debit, credit):
        if piece_id is not None and (debit != credit or debit <= 0):
            raise ValueError(f"pièce validée déséquilibrée en N : {piece_id}")

    soldes = defaultdict(lambda: Decimal("0.00"))
    gestion = defaultdict(lambda: Decimal("0.00"))
    lignes = source.execute("""
        SELECT e.id, c.numero, l.tiers_id, l.section_id, l.vehicule_id,
               l.debit, l.credit
        FROM comptabilite_ecriture e
        LEFT JOIN comptabilite_ligneecriture l ON l.ecriture_id=e.id
        LEFT JOIN comptabilite_compte c ON c.id=l.compte_id
        WHERE e.exercice_id=? AND e.statut='VALIDEE'
        ORDER BY e.id, l.id
    """, (exercice_source_id,))
    for piece_id, numero_compte, tiers_id, section_id, vehicule_id, debit, credit in lignes:
        if piece_id != piece_courante:
            verifier_piece(piece_courante, debit_piece, credit_piece)
            piece_courante = piece_id
            debit_piece = Decimal("0")
            credit_piece = Decimal("0")
        if debit is None or credit is None:
            raise ValueError(f"pièce validée sans ligne comptable : {piece_id}")
        d, cr = Decimal(str(debit)), Decimal(str(credit))
        if not d.is_finite() or not cr.is_finite() or d < 0 or cr < 0 or (d and cr) or (not d and not cr):
            raise ValueError(f"ligne comptable invalide dans la pièce {piece_id}")
        if not numero_compte:
            raise ValueError("écriture sans numéro de compte")
        debit_piece += d
        credit_piece += cr
        montant = d - cr
        if numero_compte[0] in "12345":
            soldes[(numero_compte, tiers_id, section_id, vehicule_id)] += montant
        elif numero_compte[0] in "678":
            gestion[numero_compte] += montant
    verifier_piece(piece_courante, debit_piece, credit_piece)

    # La clôture des comptes de gestion doit avoir été réellement passée
    # en N ; leur solde global nul ne suffit pas si charges et produits
    # s'annulent seulement entre eux.
    non_soldes = [numero for numero, solde in gestion.items()
                  if solde.quantize(CENTIME) != 0]
    if non_soldes:
        raise ValueError("comptes de gestion non soldés en N : " + ", ".join(sorted(non_soldes)[:10]))
    soldes = {cle: solde.quantize(CENTIME) for cle, solde in soldes.items()}
    total = sum(soldes.values(), Decimal("0.00"))
    if total != 0:
        raise ValueError(f"balance d'ouverture déséquilibrée : {total} ; clôturer le résultat N")
    comptes = dict(cible.execute("SELECT numero, id FROM comptabilite_compte"))
    # Valider les références en une lecture par table plutôt qu'une requête
    # par ligne AN. Les grands livres ventilés par tiers/axe/véhicule peuvent
    # contenir des milliers de soldes distincts.
    references = (
        ("tiers", "commercial_tiers", 1),
        ("section analytique", "comptabilite_sectionanalytique", 2),
        ("véhicule", "transport_vehicule", 3),
    )
    identifiants = {}
    for libelle, table, position in references:
        demandes = {cle[position] for cle, solde in soldes.items()
                    if solde and cle[position] is not None}
        if demandes:
            _table(cible, table)
            existants = {ligne[0] for ligne in cible.execute(f'SELECT id FROM "{table}"')}
            manquants = demandes - existants
            if manquants:
                raise ValueError(f"{libelle} manquant dans N+1 : {min(manquants)}")
        identifiants[libelle] = demandes
    insertions = []
    for (numero_compte, tiers_id, section_id, vehicule_id), solde in soldes.items():
        if not solde:
            continue
        if numero_compte not in comptes:
            raise ValueError(f"compte manquant dans N+1 : {numero_compte}")
        insertions.append((comptes[numero_compte], tiers_id, section_id, vehicule_id, str(max(solde, 0)),
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
            (ecriture_id, compte_id, tiers_id, section_id, vehicule_id, libelle, debit, credit,
             lettrage, source_cle)
            VALUES (?, ?, ?, ?, ?, 'Solde ouverture', ?, ?, '', '')
        """, [(piece_id, *ligne) for ligne in insertions])
    except Exception:
        cible.execute("ROLLBACK TO SAVEPOINT reports_ouverture")
        cible.execute("RELEASE SAVEPOINT reports_ouverture")
        raise
    cible.execute("RELEASE SAVEPOINT reports_ouverture")
    return len(insertions)
