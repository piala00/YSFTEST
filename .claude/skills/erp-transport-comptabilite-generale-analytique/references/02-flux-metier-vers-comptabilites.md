# 02 — Chaînes automatiques opérationnelles → générale → analytique

## Schéma commun

`Pièce source validée -> événement métier stable + outbox -> sous-livre (si utile) -> règle d'écriture générale -> lignes comptables équilibrées -> allocations analytiques (si éligibles) -> rapport véhicule -> agrégation propriétaire -> rapprochements`.

L'enregistrement en caisse est un événement monétaire **distinct** (paiement effectif), qui ne recrée pas l'événement de vente.

## Tableau des producteurs

| Service | Événement | GL / auxiliaires | Véhicule analytique | Propriétaire analytique |
|---|---|---|---|---|
| Billetterie | Vente, remboursement, voyage effectué | Vente/avoir ou produit différé + règlement distinct, selon politique | Voyage réellement exécuté et véhicule Classique/VIP | Propriétaire du véhicule à date de prestation |
| Bagages | Taxe bagages voyageurs, remboursement | Recette bagages et paiement | Véhicule et trajet réellement assurés | Agrégation de la part attribuable |
| Courrier/colis | Facturation, chargement/livraison, correction | Produit/encaissement selon politique et obligations | Partage de la recette entre véhicules qui ont transporté | Agrégation par titulaire de contrat |
| Exploitation | Bon carburant, péages, indemnités de route justifiées | Fournisseur/charge/avance selon fait | Affectation directe véhicule, voyage si disponible | Charge déductible au propriétaire selon contrat |
| Garage | Bon de travail, pièces consommées, main-d'œuvre | Stocks/charges/fournisseurs et éventuelles immobilisations selon nature | Véhicule bénéficiaire du travail | Répartition selon contrat, pas toutes charges automatiquement |
| RH/Paie | Paie validée, répartition d'activité, paiement salaire | Charge + dette salariale puis règlement | Affecter conducteur ou équipes selon présence/km/temps | Coût contractuellement supporté ou non |
| Administration | Loyers, assurance, frais communs | Enregistre l'intégralité des charges | Direct si justificatif ; sinon répartition approuvée ou non affectée | Selon période d'affectation et convention |
| Trésorerie | Entrée/sortie caisse, banque, Mobile Money, transferts | Mouvement de trésorerie et sous-livre | Pas de nouveau produit/coût véhicule si simple règlement/transfert | Impact sur solde règlement seulement s'il concerne le partenaire |

## Imputation analytique

Priorité: 1) affectation directe à `vehicle_id` issue du fait réel ; 2) affectation via voyage → véhicule ; 3) répartition contrôlée avec clé datée, pour les frais partagés ; 4) compte d'attente analytique lorsque donnée manquante. **Jamais forcer une répartition arbitraire**.

Séparer : produits bruts de l'activité, coûts directs voyage, coûts directs véhicule hors voyage, coûts indirects imputés, marge/contribution avant répartition, résultat après répartition. Conserver montant d'origine, pourcentages ou bases de ventilation, règle et version, date d'effet et arrondis.

## Risques spécifiques

- Billet réservé non vendu ≠ recette.
- Billet vendu hier pour voyage aujourd'hui ≠ encaissement aujourd'hui ; distinguer activité et caisse.
- Achat d'une pièce en stock ≠ coût de réparation jusqu'à sa consommation ou affectation comptable.
- Avance au chauffeur ≠ dépense tant qu'elle n'est pas justifiée.
- Transfert caisse A → caisse B ≠ vente + achat.
- Colis transitant sur deux bus : allocation de produit documentée, somme des parts = produit éligible **une seule fois**.
- Frais garage supportés par la compagnie ≠ retenue automatiquement due par le partenaire.
- Vente d'un billet VIP sur départ Classique = rejet de cohérence de gamme.
- Flux de correction : événement de contrepassation/avoir + nouvelle imputation, jamais modification silencieuse d'une écriture validée.
