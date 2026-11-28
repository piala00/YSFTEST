# 04 — Deux rubriques d'états et exemple de résultat

## Navigation
**Comptabilité analytique → Véhicules** : fiche, compte d'exploitation, grand livre imputé, balance analytique, voyages, carburant, entretiens, rémunérations dues liées, charges communes, filtres période/agence/ligne/gamme (Classique/VIP).

**Comptabilité analytique → Propriétaires de véhicules** : liste des propriétaires et véhicules historiques, conventions, détail fixe/variable, relevé des droits, compte auxiliaire GA du propriétaire, avances, paiements, retraits, restes dus et comparaison de périodes.

Autres tiers (fournisseurs, débiteurs et créditeurs divers) : dans les sous-comptes auxiliaires de **Comptabilité générale** ou leur service métier, PAS dans les propriétaires analytiques.

## Exemple récapitulatif — cas A
| Indicateur | FCFA |
|---|---:|
| Recettes de transport | 1 000 000 |
| Carburant et autres charges directes | 400 000 |
| Marge avant propriétaire | 600 000 |
| Rémunération mensuelle fixe garantie du propriétaire | 150 000 |
| Complément variable (40 % de 450 000) | 180 000 |
| **Résultat analytique du véhicule après droits propriétaire** | **270 000** |
| Droits reconnus au compte propriétaire | 330 000 |
| Versement fixe réalisé | 150 000 |
| Retrait variable complémentaire effectivement payé | 100 000 |
| **Solde créditeur restant dû au propriétaire** | **80 000** |

Éviter l'étiquette « bénéfice disponible au retrait » : les résultats analytiques, les dettes exigibles et la trésorerie disponible sont trois mesures différentes.

## États simples, imprimables
- Situation propriétaire (tableau) : Date, véhicule, numéro contrat, nature (FIXE / VARIABLE / AVANCE / RETRAIT / RÈGLEMENT / CORRECTION), numéro de pièce GL, dû, réglé, solde cumulé.
- État mensuel par véhicule : recettes, charges hors propriétaire, droit fixe, droit variable, résultat, détail par voyage.
- État global du propriétaire : véhicule 1 + véhicule 2 + historique des changements, solde global seulement après rapprochement des sous-comptes.
- Reporting : évolution N/N−1 ou Mois/Mois précédent, Classique/VIP, comparaison des propriétaires, indicateurs de paiement en retard ; distinguer période de comptabilisation, période d'exploitation et date de paiement.

## Jeu d'essai autonome
Voir `examples/cas_proprietaire_fixe_variable.csv`, `examples/ecritures_gl.csv`, `examples/ventilations_gl.csv`, `examples/releve_proprietaire.csv`. Ce scénario est **isolé des CSV de la simulation principale**, laquelle ne dispose pas encore de composante fixe : on ne l'ajoute pas artificiellement à une balance existante en prétendant qu'elle était déjà comptabilisée.
