# 04 — États attendus, TOUS centrés sur véhicules et propriétaires

## Comptabilité analytique > Véhicules

**En-tête** : compagnie, période, dernière synchro, gamme Classique/VIP, propriétaire à la période, code/immatriculation, agence d'exploitation.

**État de résultat véhicule (tableau simple)** :

| Rubrique | Montant (FCFA) |
|---|---:|
| Billetterie, voyageurs transportés | ... |
| Bagages payants | ... |
| Colis/messagerie attribués à ce véhicule | ... |
| Autres produits attribuables | ... |
| **TOTAL PRODUITS** | **...** |
| Carburant | ... |
| Péages et frais de route | ... |
| Pièces consommées / garage | ... |
| Personnel affecté | ... |
| Assurance / charges de véhicule | ... |
| Charges communes réparties (si règles approuvées) | ... |
| **TOTAL CHARGES IMPUTÉES** | **...** |
| **RÉSULTAT ANALYTIQUE** | **...** |

Sous-états accessibles : voyages et tronçons réalisés ; recettes par origine (billet/bagage/colis) et pièce ; achats/consommations garage ; carburants, paie, frais ; comparaison périodes ; montants non encore ventilés signalés. Formule `résultat = produits affectés - charges imputées`, en montrant séparément les frais communs facultatifs et le détail de leur clé.

## Comptabilité analytique > Propriétaires

Vue 1 : liste des propriétaires et nombre de véhicules à la période (une même immatriculation peut changer de propriétaire au cours d'une période ; éviter le comptage double). Vue 2 : compte par propriétaire, avec lignes par véhicule et sous-totaux, plus un détail par contrat/date d'effet.

**État portefeuille partenaire (tableau simple)** :

| Véhicule | Gamme | Produits | Charges analytiques | Résultat analytique |
|---|---|---:|---:|---:|
| BUS-001 | Classique | ... | ... | ... |
| BUS-004 | VIP | ... | ... | ... |
| **TOTAL PARTENAIRE** | | **...** | **...** | **...** |

**État financier du propriétaire, séparé** : `montant contractuellement acquis +/- régularisations - avances applicables - règlements = solde payable/à régulariser`, avec sens débiteur/créditeur clair. Ne pas utiliser la marge analytique comme si c'était une dette certaine de la compagnie.

## Comptabilité générale > états légaux

Plan comptable, journaux, grand livre, balance, bilan, compte de résultat, auxiliaires, état de caisse/banque, rapprochements, écritures en attente, périodes comptables. Ces états couvrent **aussi les charges non attribuées aux véhicules**.

## Détail des filtres

Toutes les analyses véhicule/propriétaire acceptent date de début/fin, agence exploitation, agence ventes (option séparée), classe VIP/Classique, contrat, ligne et voyages comme filtres ; cela ne transforme pas ces dimensions en rubriques principales. Préserver mode d'export et largeur d'impression adaptée, montants lisibles et sources consultables.

## Contrôle des montants

- `total véhicules inclus = total des produits/charges analytiques attribués à ces véhicules`, sans addition de rapports déjà agrégés.
- `total véhicules par propriétaire = total partenaire pour le périmètre` ; prendre contrats datés.
- `somme analytique affectée = total GL éligible à l'affectation`, et fournir des rubriques "non affecté"/"écarts" explicables.
- `total GL société` peut être différent de `total véhicule`, car certaines charges/produits sont hors véhicules, certains produits ne sont pas reconnus dans la même période et certaines attributions sont provisoires.
- Ne pas mélanger TTC encaissements, HT produits et marges sans spécifier la base.
- Afficher `provisoire: agences non synchronisées` et la date du dernier lot reçu.

## Présentation

Tableaux blancs, bordures légères, en-tête net, chiffres à droite, sous-totaux gras, pas de dashboards graphiques obligatoires. Pour chaque montant cliquer jusqu'au document source et aux règles de calcul si l'interface supporte le drill-down.
