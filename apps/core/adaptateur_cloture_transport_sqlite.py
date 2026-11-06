"""Adaptateur métier de clôture annuelle des dossiers Django SQLite déjà migrés.

N reste en lecture seule. N+1 doit être migrée avec la même version de Django.
Aucun document commercial, mouvement de stock ou voyage n'est recopié.
"""
from datetime import date

from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite
from apps.core.reprise_configuration_sqlite import recopier_referentiels
from apps.core.reports_annuels_sqlite import reporter_balance_validee

# Ordre libre : recopier_referentiels trie les dépendances FK.
REFERENTIELS_OBLIGATOIRES = (
    "core_societe", "comptabilite_compte", "comptabilite_journal",
    "commercial_tiers", "core_agence", "auth_user", "auth_group",
    "django_content_type", "auth_permission", "comptabilite_sectionanalytique",
    "auth_user_groups", "auth_user_user_permissions", "auth_group_permissions",
    "core_droitacces", "core_acceslogiciel",
)
REFERENTIELS_TRANSPORT = (
    "transport_gare", "transport_ligne", "transport_vehicule",
)


def initialiser_dossier_annuel(source, cible, annee, *, transport=True):
    """Reprend les paramètres stables ; refuse les schémas incomplets.

    Le schéma N+1 est créé au préalable par les migrations, jamais en
    recopiant le fichier N (qui contient des mouvements historiques).
    """
    tables = list(REFERENTIELS_OBLIGATOIRES)
    if transport:
        tables.extend(REFERENTIELS_TRANSPORT)
    recopier_referentiels(source, cible, tables)
    # Les verrouillages des journaux appartiennent à N : N+1 doit être
    # saisissable dès son ouverture, y compris dans le journal AN.
    cible.execute("UPDATE comptabilite_journal SET cloture_au=NULL")
    # Un exercice neuf est propre à N+1, et non une copie de N.
    if cible.execute("SELECT 1 FROM core_exercice LIMIT 1").fetchone():
        raise ValueError("N+1 contient déjà un exercice")
    cible.execute(
        "INSERT INTO core_exercice (code, date_debut, date_fin, cloture) VALUES (?, ?, ?, 0)",
        (str(annee), f"{annee}-01-01", f"{annee}-12-31"),
    )
    return cible.execute("SELECT last_insert_rowid()").fetchone()[0]


def preparer_dossier_transport_sqlite(catalogue, identifiant, destination,
                                     nouvel_identifiant, annee, migrer_cible):
    """Crée N+1 et sa pièce AN dans une transaction, puis publie le catalogue.

    migrer_cible est un callback qui crée uniquement le schéma cible à partir
    des migrations applicatives ; il ne doit jamais modifier la source.
    """
    if not isinstance(annee, int) or not 1900 <= annee <= 9998:
        raise ValueError("année N+1 invalide")
    if not callable(migrer_cible):
        raise TypeError("migrations N+1 obligatoires")
    etat = {}

    def initialiser(source, cible):
        migrer_cible(cible)
        exercices = source.execute(
            "SELECT id, date_debut, date_fin, cloture FROM core_exercice ORDER BY date_fin DESC"
        ).fetchall()
        if len(exercices) != 1:
            raise ValueError("la base N doit contenir exactement un exercice")
        ancien_id, debut, fin, cloture = exercices[0]
        if date.fromisoformat(fin).year != annee - 1:
            raise ValueError("année N+1 non consécutive à N")
        if date.fromisoformat(debut) > date.fromisoformat(fin):
            raise ValueError("dates de N invalides")
        # La clôture métier de N doit avoir été calculée et validée.
        # Le catalogue n'est clôturé qu'après succès de toute l'opération.
        etat["ancien_id"] = ancien_id
        etat["nouveau_id"] = initialiser_dossier_annuel(source, cible, annee)

    def reporter(source, cible):
        reporter_balance_validee(source, cible, etat["ancien_id"],
                                 etat["nouveau_id"], f"{annee}-01-01")

    return preparer_exercice_sqlite(catalogue, identifiant, destination,
                                   nouvel_identifiant, initialiser, reporter)
