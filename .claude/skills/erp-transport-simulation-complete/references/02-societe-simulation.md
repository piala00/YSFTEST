# Société fictive et exploitation du mois SEPTEMBRE 2026

**Nom : TRANS-CAM INTÉGRAL DÉMONSTRATION SARL — FICTIVE, aucune personne réelle.** Année/période : 2026-09-01 au 2026-09-30 inclus, 30 jours. Seed reproductible : `20260926` ; Python standard library, pas d'accès réseau nécessaire.

| Agence | Code | Effectif | Véhicules voyageurs affectés |
|---|---|---:|---:|
| Douala (siège) | AG01 | 65 | 12 |
| Yaoundé | AG02 | 64 | 12 |
| Bafoussam | AG03 | 34 | 8 |
| Bertoua | AG04 | 32 | 8 |
| Garoua-Boulaï | AG05 | 26 | 5 |
| Ngaoundéré | AG06 | 30 | 6 |
| Bamenda | AG07 | 27 | 5 |
| Buea | AG08 | 22 | 4 |
| **Total** | | **300** | **60** |

Pour l'entraînement, on suppose toutes les liaisons routières possibles entre les villes listées. **Ne pas utiliser ces trajets, durées ou possibilités d'acheminement comme des informations routières réelles ou des lignes commerciales vérifiées.** Le générateur ne simule qu'un départ maximum par véhicule/jour, sans logique kilométrique/réglementation de repos réelle. Pour la production : validations d'itinéraires, tronçons, habilitations, sécurité et vitesse.

## Parc de 65 véhicules
- **60 véhicules voyageurs** = 24 VIP (12 minibus de 15 places, 8 minibus de 20 places, 4 coasters de 30 places) et 36 Classique (6 coasters de 30, 10 bus de 40, 12 bus de 55, 8 grands autocars de **75**).
- Dénomination `SAVIEM` uniquement **type local de grand autocar représenté pour démonstration** ; ne déduit pas la marque réelle des véhicules. Capacité et homologation sont champs indépendants.
- **15 véhicules voyageurs** appartiennent à **10 propriétaires fictifs** (`PAR-001` à `PAR-010`), parfois un propriétaire a plusieurs véhicules. **45** appartiennent à la compagnie.
- **5 véhicules dédiés au courrier**, identifiés `FRET-001` à `FRET-005`, en plus des 60 voyageurs, soit **65 au total**.
- Un bus est VIP **ou** Classique à une date donnée ; jamais les deux simultanément. Type de carrosserie, nombre de places et gamme sont des propriétés indépendantes ; changements datés.
- La distinction « agence d'affectation / agence de vente / agence exploitante / agence bénéficiaire » est obligatoire.

## Résultats générés (exemple contrôlé, FCFA, avant fiscalité et amortissements non simulés)
- **1,275 voyages effectués** ; **35,883 billets** ; **2,523 expéditions**.
- Billetterie : **293,519,000 FCFA** ; courrier : **16,888,500 FCFA**.
- Carburant et péages : **88,437,000 FCFA**.
- **32 demandes d'achats**, **32 BC**, **32 factures fournisseurs**; inventaire et consommation suivis.
- **300 paies** ; brut **42,250,000**, net payé **40,137,500**, charges employeur FICTIVES **4,225,000** FCFA.
- Redevances contractuelles partenaires reconnues : **43,828,750**, solde restant **17,531,500** FCFA.
- Journal général : **25,993 lignes** et **12,607 ventilations traçables. Débit = crédit = **803,114,750 FCFA**.
- Résultat simplifié **128,083,550 FCFA**, **NON** bilan SYSCOHADA réel : sans amortissements, provisions, fiscalité réelle, étalement de prestations, dette TVA, dettes sociales calculées au barème, charges de siège externes, etc.

## Reproductibilité
`python .claude/skills/erp-transport-simulation-complete/scripts/generate_demo.py`
`python .claude/skills/erp-transport-simulation-complete/scripts/validate_demo.py`

Les 30 jours sont dans `rj_agences_synthese.csv` (8 agences × 30 = 240 lignes). Les CSV détaillés ont date, agence, véhicule et identifiants ; utiliser les tableaux enregistrés comme fixtures, non comme des données réelles de production. Tous les prix, les contrats et noms sont fictifs. Le `METRIQUES_ET_CONTROLES.json` reste l'oracle testable de la simulation.

## Résultat fonctionnel attendu
Des états du 01/09 au 30/09 et période comparative sélectionnable ; journaux ventes, banque, caisses, achats, paie ; balances, grands livres généraux et analytiques (avec preuve GL), situation propriétaire, grand livre tiers, stocks par agence, soldes et factures fournisseurs, bordereaux, ventes Classique/VIP, et situation agence globale. La clôture de paie doit apparaître le 30/09. La comparaison avec OCTOBRE exige un deuxième mois de données ; **ne jamais fabriquer octobre sur la base de septembre**.
