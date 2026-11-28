# Dictionnaire des notions Comptabilité et relations ERP

| Concept | Table Sage 100 indicative | Questions à vérifier |
|---|---|---|
| Compte général | `F_COMPTEG` | Numéro, nature, collectif, clôture, devise, reporting |
| Compte tiers | `F_COMPTET` | Catégorie client/fournisseur, contrepartie, conditions de paiement |
| Compte analytique | `F_COMPTEA` | Plan, section, répartition, imputation |
| Écriture comptable | `F_ECRITUREC` | Journal, pièce, date, exercice, débit/crédit, lettrage, clôture |
| Budget compte général | `F_COMPTEGBUDGET` | Exercice, montant et ventilation |
| Liaison tiers-généraux | `F_COMPTETG` | Cardinalité, catégorie comptable, plan |

Le nom des champs et leurs domaines se consultent directement dans Sage, **Structure des bases V12.20**, chapitre Comptabilité, 14–150 puis joints 401–408. Un schéma SQL vivant V5–V12 se collecte sans données métier via l'outil d'extraction. Ne pas inventer les PK/relations par nom ressemblant.

## Invariants conceptuels
1. Total débit = total crédit pour les écritures soumises à cette règle dans le même périmètre.
2. Échéances et règlements ne sont pas identiques à la simple somme des débits/crédits ; intégrer lettrage/affectations, devises et paiements partiels.
3. Données multi-exercices : dates de transaction, dates de pièce, dates d'échéance, ouverture et clôture à distinguer.
4. Gestion analytique : rapprochement entre comptabilité générale et analytique selon règles de ventilation.
5. Audit d'ERP : comparer les états standard Sage sur la même période, société, devise et filtre.

## Fiche de tests : grand livre et balance
Cas fictif : achat à crédit, facture de vente puis paiement partiel, annulation/reprise uniquement en test. Relever écritures par compte, total journal, balance à date, tiers ouvert, TVA/charge/produit. La démonstration fait autorité, pas une requête non réconciliée.
