# 08 — Orchestration métier : chaque service produit un fait, tous les états se mettent à jour

## Principe événementiel

Les modules ne doivent pas écrire directement dans les tables privées de leurs voisins. Chaque module est **source autoritative** de ses propres documents, commandes et états ; il publie des événements métier après transaction (`outbox`). Les consommateurs construisent leurs projections/services dérivés et peuvent appliquer les politiques de droits, de validation, de taxation et d'analytique.

Conserver : `event_id` UUID, `tenant_id`, `legal_entity_id`, `agency_id`, `aggregate_type`, `aggregate_id`, `event_type`, `aggregate_version`, `occurred_at_utc`, `effective_at`, `actor_id`, `device_id`, `causation_id`, `correlation_id`, `schema_version`, `payload` et `sync_status`. Toute réception enregistre une clé idempotente côté consommateur.

## Table des chaînes automatiques

| Action effectuée par le service | Événement publié | Répercussions AUTOMATIQUES mais contrôlées |
|---|---|---|
| Guichet : vente de billet | `TicketIssued` et `PaymentCaptured` selon réalité | capacité vendue ; session caisse ; sous-livre ventes ; moteur comptable ; recettes voyage/véhicule ; KPI agence |
| Guichet : annulation/remboursement | `TicketCancelled`, `RefundAuthorized`, `RefundPaid` | billet invalide, disponibilité selon règles, avoir, mouvement caisse si payé, correction analytique |
| Contrôleur : embarquement | `TicketBoarded` | manifeste, nombre de passagers, sécurité anti-double usage ; **pas deuxième revenu** |
| Colis : expédition | `ShipmentAccepted`, `ShipmentInvoiced` | suivi, créance/encaissement si réel, vente messagerie, agence commerciale |
| Quai : chargement | `ParcelLoadedOnTrip` | manifeste véhicule, étapes de transport, analytique allouable au voyage |
| Destination : livraison | `ParcelDelivered` | fin chaîne custody, preuve, éventuels frais de livraison, statistiques |
| Exploitation : départ/arrivée | `TripDeparted`, `TripArrived` | activité véhicule, kilomètres, états voyages, calcul analytique |
| Carburant : bon délivré | `FuelDispensed` | consommation, coût, véhicule/voyage, stock/dette suivant origine |
| Garage : pièce consommée | `PartConsumedOnWorkOrder` | diminution stock, coût garage/vehicle, immobilisation éventuelle selon validation |
| Garage : prestation externe approuvée | `RepairSupplierInvoiceApproved` | dette fournisseur, coût/immobilisation, véhicule, analytique |
| Comptable : dépense payée | `DisbursementPaid` | caisse/banque, apurement dette, pas redoublement du coût |
| RH : paie approuvée | `PayrollApproved` | dette personnel/organismes, charges, centres de coûts |
| Finance : paie réglée | `PayrollPaymentSettled` | trésorerie et soldes salariés/organismes |
| Partenaires : décompte approuvé | `PartnerSettlementApproved` | solde auxiliaire, détail contractuel, écritures paramétrées |
| Caisse : transfert/remise | `CashTransferDispatched/Received` | fonds en transit, confirmation, rapprochement siège |

**Chaque ligne exige au minimum** : préconditions, autorité, statut source, événement stable, consommateur, règle idempotence, compensation, imputation comptable, imputation analytique, trace d'audit et droit.

## Exemple complet d'une journée

Contexte fictif : agence Bertoua, véhicule `V-101`, voyage `T-2026-10-25-001`, chauffeur `E-17`, société `S-01`, contrat partenaire `P-09`.

1. Exploitation programme `T`, affecte `V` et `E` ; les guichets et colis voient le voyage. Aucune recette n'est encore reconnue.
2. Billetterie vend 25 billets pour `T`. Paiements réels ventilés dans les caisses d'origine ; la billetterie ne saisit jamais la dépense de carburant.
3. Colis enregistre 12 expéditions, dont 8 sont effectivement chargées sur `T`; seules les unités/segments réellement transportés entrent dans la mesure physique d'exploitation du véhicule.
4. Carburant valide 70 litres pour `V`, avec bon et mode de règlement. Le coût analytique voyage s'applique selon règle ; achat à crédit crée dette, pas sortie de caisse.
5. Garage clôture un OR pour `V` avec 2 pièces sorties du stock ; consommation imputable au véhicule, réparation à imputer au voyage seulement si politique le prévoit.
6. Contrôleur valide 24 passagers, signale 1 absent ; cela ne change pas le nombre de billets vendus ni ne crée un encaissement.
7. Chauffeur produit 3 justificatifs de péages et rend le solde de son avance ; trésorerie rapproche les flux.
8. Chef d'agence clôture les caisses et le voyage après explication des écarts ; comptabilité génère/valide ses écritures selon ses politiques.
9. Comptes partenaires : les recettes éligibles et coûts déductibles de V donnent le décompte dû à P, sans s'y substituer.
10. Siège reçoit les événements lorsque le lien revient, reconstruit chaque vue et affiche `dernier_sync` ; les chiffres incomplets sont signalés.

## Conditions de correction

- Erreur de billet : nouvel avoir/annulation, jamais écrasement.
- Erreur d'attribution de véhicule : transfert analytique versionné et, si nécessaire, réconciliation des décomptes.
- Facture atelier annulée : contrepassation et éventuel retour en stock réel ; ne pas rendre une pièce physiquement « non consommée » par simple suppression SQL.
- Erreur sur salaire : régularisation de paie signée, avec période et références.
- Document reçu en double : idempotence par `event_id` et clé métier ; journaliser le doublon technique.

## Qualité des vues dérivées

Projeter les données dans des modèles en lecture optimisés (rapport caisse, `vehicle_profitability`, `agency_daily_snapshot`, `partner_statement`). Les projections sont **reconstructibles** à partir des sources et événements durables, avec état `last_applied_event/last_sync`, version d'algorithme et politiques de réconciliation. N'utiliser qu'une seule source comptable officielle pour chaque écriture GL ; éviter une architecture où chaque module ajoute ses propres lignes au grand livre en parallèle.
