# Audit et architecture — comptabilité analytique

Vérifié sur la branche `ccr-5592a371-fusjt2` (pas sur l'archive « 7 chiffres » que décrit le skill : plusieurs constats
de son audit sont dépassés, voir colonne « Aujourd'hui »).

## Constats du skill et état actuel

| Constat du skill (archive précédente) | Aujourd'hui |
|---|---|
| Pas d'accès aux 10 plans ; seulement véhicules, propriétaires, balance des sections | 9 axes + plans de sections libres, chacun avec balance et 7 états par élément (`apps/comptabilite/plan_analytique.py`, `views_analytique.py`) |
| Périodes incohérentes, exercice entier par défaut | Barre de période commune : mois en cours par défaut, boutons rapides, exercice, mois + année, ←/→, Du > Au refusé |
| `LigneEcriture.section` unique : pas de 10 dimensions | Les dimensions sont **déduites** des faits (véhicule de la ligne, pièce → départ → ligne, gare, gamme ; contrat à la date ; section) ; pas de copie de montant |
| Reporting indépendant | `apps/transport/reporting.py` lit ses montants dans le même moteur (`plan_analytique.faits`) ; égalité testée au franc près |
| URLs limitées | `analytique:plan`, `analytique:axe`, `analytique:element` |

## Architecture retenue

- **Une source** : lignes de classes 6 et 7 des écritures **validées** (`faits(debut, fin)`), lues une fois avec leurs
  référentiels (`_Contexte`). Aucune table de montants analytiques, donc rien à resynchroniser ni à doubler.
- **Attribution** (une ligne → au plus un élément par axe) :
  véhicule (ligne d'écriture) ; voyage (pièce du départ, colis, plein, dépense, avance, imprévu) ; ligne, gamme, gare
  (du voyage ; section de gare ; agence à gare unique) ; propriétaire et contrat (contrat **en vigueur à la date**) ;
  activité (compte du produit ; charge rattachée ou non à un véhicule) ; service (section SV- posée par la paie hors
  véhicule ; sinon service producteur : billetterie, colis, conduite, garage) ; plans de sections (section de la ligne).
- **Invariant** testé pour chaque axe : éléments + non affecté = comptabilité générale. Une ligne compte une fois par
  axe ; on n'additionne jamais deux axes.
- **États** : `balance_axe`, `etat_element` (exploitation, comptes, grand-livre, évolution, croisé, comparaison,
  journal), `synthese_axes`. Le reporting et l'accueil utilisent les mêmes fonctions.
- **Provisoire** : les écritures au brouillard sont comptées et signalées, jamais incluses.
- **Migration** : aucune pour le moteur. La paie pose désormais une section « Services » sur ses charges hors
  véhicule (nouvelles paies seulement ; les anciennes restent non affectées sur cet axe).

## Hors périmètre de cette mise à jour

Voir `ECARTS_A_CORRIGER.md` : ventilation fractionnée et clés de répartition, canaux de vente, agence ≠ gare, droits
par gare/propriétaire, fraîcheur par agence sur les états, PDF/XLSX natifs, écrans bureau natifs.
